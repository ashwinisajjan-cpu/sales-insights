"""
News Signal Scoring
--------------------
Fetches free Google News RSS for each company and detects high-value
sales signals: M&A activity, C-suite changes, expansions, funding rounds.
These boost the company's prospect score and flag them as hot leads.
"""

import re
import time
import requests
from urllib.parse import quote

# ── Signal definitions ────────────────────────────────────────────────────────
# Each signal has: keywords to match in headline, score boost, label, emoji
SIGNALS = [
    # M&A / Acquisitions — biggest buying signal
    {
        "keywords": ["acqui", "merger", "acquisition", "acquired", "merges with",
                     "buys ", "purchase", "takeover", "acquired by"],
        "boost":    25,
        "label":    "M&A Activity",
        "emoji":    "🤝",
        "tip":      "Company involved in M&A — major infrastructure expansion likely",
    },
    # Funding / IPO
    {
        "keywords": ["funding", "raises $", "series a", "series b", "series c",
                     "ipo", "goes public", "valuation", "investment round"],
        "boost":    20,
        "label":    "Funding / IPO",
        "emoji":    "💰",
        "tip":      "Fresh capital — ready to invest in new technology",
    },
    # C-suite / Leadership change
    {
        "keywords": ["new ceo", "new cto", "new cfo", "new ciso", "appoints",
                     "names new", "hires", "joins as", "chief executive",
                     "leadership change", "executive change"],
        "boost":    18,
        "label":    "Leadership Change",
        "emoji":    "👔",
        "tip":      "New leadership = new priorities and budget reviews",
    },
    # Expansion / Growth
    {
        "keywords": ["expand", "expansion", "new office", "new headquarters",
                     "opens", "growth", "scaling", "headcount", "hiring"],
        "boost":    15,
        "label":    "Expansion",
        "emoji":    "📈",
        "tip":      "Company is growing — increased networking and tech needs",
    },
    # Digital transformation / Cloud
    {
        "keywords": ["digital transformation", "cloud migration", "moderniz",
                     "ai strategy", "technology overhaul", "infrastructure upgrade"],
        "boost":    20,
        "label":    "Digital Transformation",
        "emoji":    "☁️",
        "tip":      "Active digital transformation — ideal Lumen cloud/network opportunity",
    },
    # Partnership / Contract wins
    {
        "keywords": ["partnership", "partner with", "contract win", "deal with",
                     "agreement with", "signed with", "selected by"],
        "boost":    12,
        "label":    "Partnership",
        "emoji":    "🤲",
        "tip":      "New partnerships = new integration and connectivity needs",
    },
    # Layoffs / Restructuring — also a signal (cost-cutting → managed services)
    {
        "keywords": ["layoff", "layoffs", "restructur", "downsiz", "cuts jobs",
                     "workforce reduction"],
        "boost":    8,
        "label":    "Restructuring",
        "emoji":    "⚠️",
        "tip":      "Restructuring — opportunity for managed services to reduce costs",
    },
]

# Cache: company_name → {timestamp, result}
_NEWS_CACHE: dict = {}
_CACHE_TTL = 3600  # 1 hour


def _fetch_news_headlines(company: str) -> list[str]:
    """Fetch up to 10 recent headlines from Google News RSS (free, no API key)."""
    cached = _NEWS_CACHE.get(company.lower())
    if cached and time.time() - cached["ts"] < _CACHE_TTL:
        return cached["headlines"]

    try:
        query = quote(f'"{company}"')
        url   = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        r     = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SalesInsightsBot/1.0)"
        })
        if r.status_code != 200:
            return []

        # Parse <title> tags from RSS (simple regex, no xml lib needed)
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
        if not titles:
            titles = re.findall(r"<title>(.*?)</title>", r.text)

        # Skip the first title (it's the feed title, not an article)
        headlines = [t.strip() for t in titles[1:11]]
        _NEWS_CACHE[company.lower()] = {"ts": time.time(), "headlines": headlines}
        return headlines
    except Exception:
        return []


def get_news_signals(company: str) -> dict:
    """
    Returns news signals for a company:
    {
        "score_boost": int,        # total score boost from news signals
        "signals": [               # list of detected signals
            {"label": str, "emoji": str, "headline": str, "tip": str, "boost": int}
        ],
        "headlines": [str],        # raw headlines fetched
        "hot_lead": bool,          # True if boost >= 20
    }
    """
    headlines = _fetch_news_headlines(company)
    detected  = []
    total_boost = 0
    seen_labels = set()

    for headline in headlines:
        hl_lower = headline.lower()
        for sig in SIGNALS:
            if sig["label"] in seen_labels:
                continue
            if any(kw in hl_lower for kw in sig["keywords"]):
                detected.append({
                    "label":    sig["label"],
                    "emoji":    sig["emoji"],
                    "headline": headline[:120],
                    "tip":      sig["tip"],
                    "boost":    sig["boost"],
                })
                total_boost += sig["boost"]
                seen_labels.add(sig["label"])
                break  # one match per signal type per headline

    return {
        "score_boost": min(total_boost, 40),   # cap at +40 so scores stay ≤100
        "signals":     detected,
        "headlines":   headlines[:5],
        "hot_lead":    total_boost >= 20,
    }
