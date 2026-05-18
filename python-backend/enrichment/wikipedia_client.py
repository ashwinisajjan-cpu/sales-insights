import re
import json
import time
import requests
import mwparserfromhell
from config.settings import (
    HEADERS, WIKIPEDIA_API, WIKIPEDIA_SEARCH, DUCKDUCKGO_API, GEMINI_API_KEY
)

try:
    import google.generativeai as _genai
    _genai.configure(api_key=GEMINI_API_KEY)
    _GEMINI_OK = True
except Exception:
    _genai = None
    _GEMINI_OK = False

_GEMINI_FILL_CACHE: dict = {}
_GEMINI_COOLDOWN_UNTIL: float = 0.0


def _gemini_fill_missing(company: str, missing_fields: list) -> dict:
    """Ask Gemini for rich, detailed company information."""
    global _GEMINI_COOLDOWN_UNTIL
    if not _GEMINI_OK or time.time() < _GEMINI_COOLDOWN_UNTIL:
        return {}
    cache_key = company.lower().strip()
    if cache_key in _GEMINI_FILL_CACHE:
        return _GEMINI_FILL_CACHE[cache_key]
    try:
        prompt = (
            f'You are a business intelligence expert. Provide accurate, detailed information about "{company}" '
            f'in valid JSON with these exact keys:\n'
            f'{{\n'
            f'  "industry": "Primary industry + subcategories (e.g. Information Technology, Software, Cloud Computing)",\n'
            f'  "hq": "Full HQ location with city, state/country (e.g. Redmond, Washington, United States)",\n'
            f'  "ceo": "Current CEO full name (e.g. Satya Nadella)",\n'
            f'  "founded": "Founded year and founders if notable (e.g. 1975 by Bill Gates and Paul Allen)",\n'
            f'  "revenue": "Latest annual revenue with fiscal year (e.g. $245 billion (FY2025))",\n'
            f'  "employees": "Approximate employee count (e.g. ~228,000 employees (2024))",\n'
            f'  "description": "2-sentence company description highlighting what they do and their market position"\n'
            f'}}\n'
            f'Use the most current data available. If a field is truly unknown, use null. '
            f'Respond with ONLY the JSON object, no markdown, no explanation.'
        )
        model = _genai.GenerativeModel("gemini-2.0-flash")
        resp  = model.generate_content(prompt)
        raw   = resp.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            data   = json.loads(m.group(0))
            result = {k: str(v).strip() for k, v in data.items()
                      if v and str(v).strip() not in ("null", "None", "")}
            _GEMINI_FILL_CACHE[cache_key] = result
            return result
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "exhausted" in err.lower():
            _GEMINI_COOLDOWN_UNTIL = time.time() + 3600
            print(f"Gemini quota exhausted — cooling down 1 hour")
        else:
            print(f"Gemini error for {company}: {e}")
    return {}

_EMPTY_WIKI = {
    "wiki_found": False,
    "wiki_title": "N/A", "wiki_summary": "N/A",
    "wiki_url": "N/A",   "wiki_image": "N/A",
    "wiki_founded": "N/A", "wiki_hq": "N/A",
    "wiki_industry": "N/A", "wiki_products": [],
    "wiki_ceo": "N/A",   "wiki_revenue": "N/A",
    "wiki_employees": "N/A", "wiki_mission": "N/A",
    "wiki_core_values": "N/A", "wiki_solutions": "N/A",
}


def _wiki_fetch(slug: str):
    try:
        r = requests.get(
            f"{WIKIPEDIA_API}/{slug}", headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("type") not in (
                "disambiguation",
                "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"
            ):
                return data
    except Exception:
        pass
    return None


def _extract_infobox_field(found, *keys):
    """Try to extract a field from Wikipedia infobox data."""
    infobox = found.get('infobox', {})
    for key in keys:
        val = infobox.get(key)
        if val and isinstance(val, str):
            return val.strip()
    return None


def wikipedia_summary(company: str) -> dict:
    found = _wiki_fetch(company.replace(" ", "_"))
    if not found:
        try:
            r = requests.get(
                WIKIPEDIA_SEARCH,
                params={"action": "query", "list": "search",
                        "srsearch": company + " company",
                        "format": "json", "srlimit": 3},
                headers=HEADERS, timeout=10,
            )
            results = r.json().get("query", {}).get("search", [])
            for hit in results:
                found = _wiki_fetch(hit["title"].replace(" ", "_"))
                if found:
                    break
        except Exception:
            pass

    if not found:
        return dict(_EMPTY_WIKI)

    summary   = found.get("extract", "") or ""
    title     = found.get("title", "N/A")
    page_url  = found.get("content_urls", {}).get("desktop", {}).get("page", "N/A")
    image_url = found.get("thumbnail", {}).get("source", "N/A")
    # Try REST infobox, then wikitext infobox, then summary
    infobox = found.get('infobox', {})
    if not infobox and title and title != "N/A":
        infobox = _fetch_infobox_from_wikitext(title)
    def getbox(*keys):
        for k in keys:
            v = infobox.get(k.lower())
            if v: return v
        return None
    industry  = getbox("industry", "type") or _extract_industry(summary)
    products  = _extract_products(summary)
    # Try more keys for founded
    founded_raw = getbox("founded", "foundation", "established", "formed", "date_founded", "date_established", "date_formed")
    if founded_raw:
        # Extract just the year (4 digits) from things like "1852 03 18" or "March 18, 1852"
        yr = re.search(r"\b(1[5-9]\d{2}|20[012]\d)\b", founded_raw)
        founded = yr.group(1) if yr else founded_raw
    else:
        founded = _extract_year(summary)
    # HQ: try multiple fields and join city/country if present
    hq_city   = getbox("location_city")
    hq_country= getbox("location_country")
    hq        = getbox("headquarters", "hq_location", "location")
    if not hq and hq_city and hq_country:
        hq = f"{hq_city}, {hq_country}"
    elif not hq and hq_city:
        hq = hq_city
    elif not hq and hq_country:
        hq = hq_country
    # Fallback to text extraction for HQ
    if not hq:
        hq = _extract_hq(summary)
    ceo       = getbox("ceo", "chief_executive_officer")
    if not ceo:
        key_people = getbox("key_people")
        if key_people:
            ceo = _extract_ceo_from_key_people(key_people)
    # Fallback to text extraction for CEO
    if not ceo:
        ceo = _extract_ceo(summary)
    # Search full Wikipedia article text for CEO
    if (not ceo or ceo == "N/A") and title and title != "N/A":
        ceo = _wiki_search_ceo(title)
    # DuckDuckGo fallback for CEO
    if not ceo or ceo == "N/A":
        ceo = _ddg_search_ceo(company)
    revenue   = getbox("revenue") or _extract_revenue(summary)
    employees = getbox("num_employees", "employees") or _extract_employees(summary)

    # --- Gemini AI enrichment — always called for richer, current data ---
    ai = _gemini_fill_missing(company, [])  # fetch full profile
    # Prefer Gemini data when it's richer/more detailed
    if ai.get("industry") and len(ai["industry"]) > len(industry or ""):
        industry = ai["industry"]
    if ai.get("hq") and len(ai["hq"]) > len(hq or ""):
        hq = ai["hq"]
    if ai.get("ceo") and (not ceo or ceo == "N/A"):
        ceo = ai["ceo"]
    if ai.get("founded") and len(ai["founded"]) > len(founded or ""):
        founded = ai["founded"]
    if ai.get("revenue") and len(ai["revenue"]) > len(revenue or ""):
        revenue = ai["revenue"]
    if ai.get("employees") and len(ai["employees"]) > len(employees or ""):
        employees = ai["employees"]
    # Use Gemini description to enhance summary if available
    ai_desc = ai.get("description", "")

    # Final fallbacks
    industry  = industry  or "N/A"
    hq        = hq        or "N/A"
    ceo       = ceo       or "N/A"
    founded   = founded   or "N/A"
    revenue   = revenue   or "N/A"
    employees = employees or "N/A"

    return {
        "wiki_found":       True,
        "wiki_title":       title,
        "wiki_summary":     (ai_desc + " " + summary)[:700].strip() if ai_desc else ((summary[:600] + "...") if len(summary) > 600 else summary),
        "wiki_url":         page_url,
        "wiki_image":       image_url,
        "wiki_founded":     founded,
        "wiki_hq":          hq,
        "wiki_industry":    industry,
        "wiki_products":    products,
        "wiki_ceo":         ceo,
        "wiki_revenue":     revenue,
        "wiki_employees":   employees,
        "wiki_mission":     _build_mission(summary, title),
        "wiki_core_values": _build_core_values(industry, summary),
        "wiki_solutions":   _build_solutions(products, industry),
    }


def duckduckgo_summary(company: str) -> dict:
    empty = {"ddg_found": False, "ddg_abstract": "N/A",
             "ddg_url": "N/A", "ddg_image": "N/A"}
    try:
        r = requests.get(
            DUCKDUCKGO_API,
            params={"q": company, "format": "json",
                    "no_html": 1, "skip_disambig": 1},
            headers=HEADERS, timeout=10,
        )
        d        = r.json()
        abstract = d.get("AbstractText", "")
        if not abstract:
            return empty
        return {"ddg_found": True, "ddg_abstract": abstract,
                "ddg_url": d.get("AbstractURL", "N/A"),
                "ddg_image": d.get("Image", "N/A")}
    except Exception:
        return empty


def enrich(company: str) -> dict:
    wiki = wikipedia_summary(company)
    if not wiki["wiki_found"]:
        ddg = duckduckgo_summary(company)
        if ddg["ddg_found"]:
            wiki["wiki_mission"] = ddg["ddg_abstract"][:300]
            wiki["wiki_url"]     = ddg["ddg_url"]
            wiki["wiki_image"]   = ddg["ddg_image"]
            wiki["wiki_found"]   = True
    return wiki


def _extract_year(text: str) -> str:
    # Try "founded/established/incorporated in YEAR" first
    m = re.search(r"(?:founded|established|incorporated|formed|organized)[^.]{0,80}?\b(1[5-9]\d{2}|20[012]\d)\b", text, re.I)
    if m: return m.group(1)
    # "YEAR, it was founded/established"
    m = re.search(r"\b(1[5-9]\d{2}|20[012]\d)\b[^.]{0,40}?(?:founded|established|incorporated)", text, re.I)
    if m: return m.group(1)
    # Any 4-digit year as last resort
    m = re.search(r"\b(1[5-9]\d{2}|20[012]\d)\b", text)
    return m.group(0) if m else "N/A"


def _extract_hq(text: str) -> str:
    # Specific city/state patterns
    for pat in [
        r"headquartered in ([A-Z][a-zA-Z ,]+?)(?:\.|,\s[A-Z]|\s(?:United|U\.S))",
        r"based in ([A-Z][a-zA-Z ,]+?)(?:\.|,|\s(?:United|U\.S))",
        r"headquarters (?:located )?in ([A-Z][a-zA-Z ,]+?)(?:\.|,)",
        r"head offices? in ([A-Z][a-zA-Z ,]+?)(?:\.|,)",
        r"principal offices? in ([A-Z][a-zA-Z ,]+?)(?:\.|,)",
    ]:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()[:60]
    # Country-level fallback: "American company/brand" → United States
    country_map = [
        (r"\bamerican\b", "United States"),
        (r"\bbritish\b",  "United Kingdom"),
        (r"\bcanadian\b", "Canada"),
        (r"\bgerman\b",   "Germany"),
        (r"\bfrench\b",   "France"),
        (r"\bjapanese\b", "Japan"),
        (r"\bchinese\b",  "China"),
        (r"\baustralian\b","Australia"),
        (r"\bindian\b",   "India"),
        (r"\bkorean\b",   "South Korea"),
    ]
    tl = text.lower()
    for pat, country in country_map:
        if re.search(pat, tl):
            return country
    return "N/A"


def _extract_employees(text: str) -> str:
    for pat in [
        r"([\d,]+)\s+employees",
        r"employs\s+([\d,]+)",
        r"workforce of\s+([\d,]+)",
        r"approximately\s+([\d,]+)\s+(?:full-time\s+)?employees",
    ]:
        m = re.search(pat, text, re.I)
        if m: return m.group(1).replace(",", "")
    return "N/A"


def _extract_revenue(text: str) -> str:
    for pat in [
        r"revenue[^.]{0,40}?\$([\d.]+)\s*(billion|million|trillion)",
        r"\$([\d.]+)\s*(billion|million|trillion)[^.]{0,20}?revenue",
    ]:
        m = re.search(pat, text, re.I)
        if m: return f"${m.group(1)} {m.group(2).capitalize()}"
    return "N/A"


def _extract_ceo_from_key_people(val):
    """Extract CEO name from key_people field.
    Handles formats like:
      'Charles Scharf (President (corporate title), CEO)'
      'CEO – John Doe'
      'John Doe (Chief Executive Officer)'
    """
    # Split at top-level commas (not inside parentheses) to get individual people
    def split_top_level(s):
        parts, depth, current = [], 0, []
        for c in s:
            if c == '(':
                depth += 1; current.append(c)
            elif c == ')':
                depth -= 1; current.append(c)
            elif c == ',' and depth == 0:
                parts.append(''.join(current).strip()); current = []
            else:
                current.append(c)
        if current:
            parts.append(''.join(current).strip())
        return parts

    ceo_keywords = re.compile(r'\bCEO\b|chief executive officer', re.I)

    for segment in split_top_level(val):
        if ceo_keywords.search(segment):
            # Extract leading proper name (two or more Title-Case words)
            m = re.match(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', segment)
            if m:
                return m.group(1).strip()

    # Fallback patterns: "CEO – Name" or "CEO: Name"
    m = re.search(r'CEO\s*[–:\-]\s*([A-Z][a-zA-Z .\']+?)(?:\s*[,(]|$)', val, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'Chief Executive Officer\s*[–:\-]\s*([A-Z][a-zA-Z .\']+?)(?:\s*[,(]|$)', val, re.I)
    if m:
        return m.group(1).strip()

    # If only one entry in the list, return it
    if ',' not in val and ';' not in val and '\n' not in val:
        return val.strip()
    return None


def _is_person_name(name: str) -> bool:
    """Return True if the string looks like a human name (2-3 title-case words, no common words)."""
    _NOT_NAMES = {
        "the", "this", "its", "his", "her", "our", "their", "as", "in", "on",
        "at", "by", "for", "from", "with", "to", "of", "and", "or", "a", "an",
        "it", "he", "she", "we", "they", "is", "was", "are", "were", "be",
        "been", "has", "have", "had", "do", "did", "does", "will", "would",
        "can", "could", "should", "may", "might", "while", "when", "where",
        "which", "who", "that", "these", "those", "all", "some", "any",
        "over", "under", "after", "before", "during", "between", "among",
        "new", "old", "first", "last", "next", "each", "every", "both",
        "since", "then", "now", "also", "just", "still", "even", "well",
    }
    words = name.strip().split()
    if not 2 <= len(words) <= 4:
        return False
    for w in words:
        if not w[0].isupper():
            return False
        if w.lower() in _NOT_NAMES:
            return False
    return True


def _ddg_search_ceo(company: str) -> str:
    """Search DuckDuckGo abstract for CEO info."""
    try:
        r = requests.get(
            DUCKDUCKGO_API,
            params={"q": f"{company} CEO", "format": "json", "no_html": 1, "skip_disambig": 1},
            headers=HEADERS, timeout=8,
        )
        data = r.json()
        abstract = data.get("AbstractText", "") or ""
        for pat in [
            r"\bCEO[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
            r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)[,\s]+(?:is )?(?:the )?CEO\b",
        ]:
            m = re.search(pat, abstract)  # NO re.I
            if m and _is_person_name(m.group(1)):
                return m.group(1).strip()
        for topic in data.get("RelatedTopics", []):
            text = topic.get("Text", "")
            m = re.search(r"\bCEO[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)", text)
            if m and _is_person_name(m.group(1)):
                return m.group(1).strip()
    except Exception:
        pass
    return "N/A"


def _wiki_search_ceo(title: str) -> str:
    """Search the full Wikipedia article text for CEO mentions, sentence by sentence."""
    # NOTE: name-capture patterns must NOT use re.I — [A-Z]/[a-z] would
    # match everything case-insensitively and over-capture.
    ceo_pats = [
        # "CEO John Smith" or "CEO, John Smith"
        r"\bCEO[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
        # "John Smith, CEO" or "John Smith (CEO)"
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)[,\s]+(?:is )?(?:the )?CEO\b",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+) \(CEO\)",
        # "co-founder and CEO John Smith"
        r"(?:co-founder and CEO|founder and CEO|president and CEO)[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
        # "John Smith, founder and CEO"
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+),? (?:founder and CEO|co-founder and CEO|president and CEO)",
        # "John Smith serves as / became CEO"
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+) (?:serves as|is|became|was named|was appointed)(?: the)? CEO",
        # "chief executive officer John Smith"
        r"[Cc]hief [Ee]xecutive [Oo]fficer[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)[,\s]+[Cc]hief [Ee]xecutive [Oo]fficer",
    ]
    try:
        headers = {"User-Agent": "LumenSalesInsightsAI/4.0"}
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "prop": "extracts", "explaintext": 1,
            "exsentences": 40, "format": "json", "titles": title,
        }
        r = requests.get(url, params=params, timeout=12, headers=headers)
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            text = page.get("extract", "") or ""
            if not text:
                continue
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sent in sentences:
                if not re.search(r'\bCEO\b|[Cc]hief [Ee]xecutive|founder and CEO|co-founder and CEO', sent):
                    continue
                for pat in ceo_pats:
                    m = re.search(pat, sent)  # NO re.I – preserve case for name matching
                    if m:
                        name = m.group(1).strip()
                        if _is_person_name(name):
                            return name
    except Exception:
        pass
    return "N/A"


def _extract_ceo(text: str) -> str:
    for pat in [
        r"\bCEO[,\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)[,\s]+(?:is )?(?:the )?CEO\b",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+) (?:serves as|is|became)(?: the)? CEO",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+),? (?:founder and CEO|co-founder and CEO)",
    ]:
        m = re.search(pat, text)  # NO re.I – case-sensitive for name matching
        if m and _is_person_name(m.group(1)):
            return m.group(1).strip()
    return "N/A"


def _extract_products(text: str) -> list:
    kws = ["Cloud", "Software", "Hardware", "Banking", "Insurance",
           "Logistics", "Manufacturing", "Consulting", "Technology",
           "Healthcare", "Education", "Retail", "Telecommunications",
           "Energy", "Media", "E-commerce", "Financial services",
           "Pharmaceutical", "Automotive"]
    tl = text.lower()
    return [k for k in kws if k.lower() in tl][:5]


def _extract_industry(text: str) -> str:
    checks = [
        ("Technology",          ["software", "technology company", "tech firm", "saas", "semiconductor",
                                  "artificial intelligence", "cloud computing", "internet company",
                                  "information technology", "cybersecurity", "data analytics"]),
        ("Financial Services",  ["bank", "financial services", "investment", "insurance", "asset management",
                                  "credit card", "mortgage", "brokerage", "fintech", "wealth management"]),
        ("Healthcare",          ["healthcare", "medical", "pharmaceutical", "hospital", "biotech",
                                  "life sciences", "clinical", "health system", "drug", "therapeutics"]),
        ("Consumer Goods",      ["consumer goods", "household", "beverage", "food", "beverage container",
                                  "drinkware", "cookware", "personal care", "packaged goods", "fmcg",
                                  "apparel", "clothing", "fashion", "footwear", "reusable", "kitchenware",
                                  "insulated", "bottle", "tumbler", "containers"]),
        ("Retail",              ["retailer", "retail", "e-commerce", "supermarket", "department store",
                                  "online shopping", "brick-and-mortar"]),
        ("Automotive",          ["automotive", "automobile", "car manufacturer", "vehicle", "electric vehicle"]),
        ("Transportation",      ["logistics", "shipping", "freight", "transportation", "airline",
                                  "railroad", "delivery", "supply chain"]),
        ("Manufacturing",       ["manufactur", "industrial", "factory", "fabricat", "production plant",
                                  "assembly", "equipment manufacturer"]),
        ("Energy",              ["energy", "utilities", "oil", "gas", "renewable", "power generation",
                                  "electricity", "solar", "wind energy", "petroleum"]),
        ("Education",           ["education", "university", "school", "learning", "edtech", "college",
                                  "academic", "e-learning"]),
        ("Media & Entertainment",["media", "entertainment", "broadcasting", "streaming", "film",
                                  "television", "publishing", "music", "gaming", "video games"]),
        ("Government",          ["government", "federal agency", "public sector", "municipal",
                                  "department of", "ministry of"]),
        ("Consulting",          ["consulting", "advisory", "professional services", "management consulting",
                                  "strategy firm"]),
        ("Telecommunications",  ["telecom", "telecommunications", "wireless", "broadband", "internet provider",
                                  "mobile network", "5g", "fiber"]),
        ("Real Estate",         ["real estate", "property", "reit", "commercial property", "residential developer"]),
        ("Aerospace & Defense", ["aerospace", "defense", "military", "aircraft", "satellite", "space"]),
        ("Hospitality",         ["hotel", "hospitality", "resort", "tourism", "restaurant", "food service"]),
    ]
    tl = text.lower()
    for ind, signals in checks:
        if any(s in tl for s in signals):
            return ind
    return "N/A"


def _build_mission(summary: str, title: str) -> str:
    sentences = [s.strip() for s in summary.split(".") if len(s.strip()) > 30]
    return sentences[0] + "." if sentences else f"{title} is committed to delivering value."


def _build_core_values(industry: str, summary: str) -> str:
    ind = (industry or "").lower()
    if "tech" in ind:        return "Innovation, Scalability, Security, Customer Focus, Excellence"
    if "health" in ind:      return "Patient Safety, Integrity, Compassion, Excellence, Compliance"
    if "financ" in ind or "bank" in ind: return "Trust, Compliance, Integrity, Transparency, Client Focus"
    if "education" in ind:   return "Learning, Inclusion, Community, Excellence, Respect"
    if "government" in ind:  return "Service, Accountability, Transparency, Equity, Stewardship"
    if "retail" in ind:      return "Customer Experience, Quality, Value, Innovation, Sustainability"
    if "manufactur" in ind:  return "Quality, Safety, Efficiency, Innovation, Reliability"
    return "Integrity, Innovation, Customer Focus, Teamwork, Excellence"


def _build_solutions(products: list, industry: str) -> str:
    if products:
        return ", ".join(products[:5])
    ind = (industry or "").lower()
    if "tech" in ind:    return "Cloud computing, SaaS platforms, Cybersecurity, IT services"
    if "health" in ind:  return "Medical services, Healthcare IT, Patient care, Diagnostics"
    if "financ" in ind:  return "Banking, Investment management, Insurance, Wealth advisory"
    if "retail" in ind:  return "E-commerce, Retail operations, Supply chain, Customer service"
    return "Industry-specific products and professional services"


def _clean_wikitext(raw: str) -> str:
    """Convert wikitext to plain text, preserving content from list/formatting templates."""
    try:
        text = raw
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Expand list templates: {{ubl|a|b}} → "a, b"
        def expand_list(m):
            inner = m.group(1)
            parts = re.split(r'\|', inner)
            items = []
            for p in parts[1:]:  # skip template name
                p = p.strip()
                if '=' in p:    # skip named params like style=
                    continue
                # strip inner wikilinks
                p = re.sub(r'\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]', r'\1', p)
                p = re.sub(r'\(\([^)]*\)\)', '', p)
                p = p.strip()
                if p:
                    items.append(p)
            return ', '.join(items)
        text = re.sub(
            r'\{\{((?:ubl|hlist|flatlist|plainlist|unbulleted list|cslist)[^}]*)\}\}',
            expand_list, text, flags=re.IGNORECASE
        )
        # Extract year from date templates: {{Start date and age|1852|3|18}} → "1852"
        def extract_year_from_date(m):
            args = m.group(1).split('|')
            for a in args:
                a = a.strip()
                if re.match(r'^(1[5-9]\d{2}|20[012]\d)$', a):
                    return a
            return ''
        text = re.sub(
            r'\{\{(?:start date[^|{]*|birth date[^|{]*|death date[^|{]*)\|([^}]+)\}\}',
            extract_year_from_date, text, flags=re.IGNORECASE
        )
        # Expand simple 1-arg formatting templates: {{nowrap|text}} → "text"
        for _ in range(4):
            prev = text
            text = re.sub(r'\{\{(?:nowrap|small|big|strong|em|down|up|increase|decrease|steady)\|([^|}]+)\}\}',
                          r'\1', text, flags=re.IGNORECASE)
            if text == prev:
                break
        # Remove remaining templates (loop for nesting)
        for _ in range(6):
            prev = text
            text = re.sub(r'\{\{[^{}]*\}\}', '', text)
            if text == prev:
                break
        # Convert wikilinks [[page|display]] → display, [[page]] → page
        text = re.sub(r'\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]', r'\1', text)
        # Remove HTML tags and refs
        text = re.sub(r'<ref[^>]*/>', '', text)
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        # Collapse whitespace
        text = re.sub(r'[\n\r]+', ' ', text).strip()
        text = re.sub(r'\s{2,}', ' ', text)
        return text
    except Exception:
        return raw.strip()


def _fetch_infobox_from_wikitext(title: str):
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "titles": title,
        }
        r = requests.get(url, params=params, timeout=15,
                         headers={"User-Agent": "LumenSalesInsightsAI/4.0"})
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            wikitext = page.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", "")
            if wikitext:
                code = mwparserfromhell.parse(wikitext)
                for template in code.filter_templates():
                    if template.name.lower().strip().startswith("infobox"):
                        result = {}
                        for p in template.params:
                            key = str(p.name).strip().lower()
                            val = _clean_wikitext(str(p.value))
                            if val:
                                result[key] = val
                        return result
    except Exception:
        pass
    return {}