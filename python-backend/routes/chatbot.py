from fastapi import APIRouter
from database.salesforce_client import get_sf, get_soql, build_account
from config.settings import GROQ_API_KEY
from groq import Groq
import json, re, time

router = APIRouter()

# ---------------------------------------------------------------------------
# Groq LLM setup (Llama 3.3 70B - free 14,400 req/day, 30 req/min)
# Get FREE key at https://console.groq.com
# ---------------------------------------------------------------------------
_groq_client = None
_GROQ_OK     = False
_GROQ_MODEL  = "llama-3.3-70b-versatile"
try:
    if GROQ_API_KEY and GROQ_API_KEY != "PASTE_YOUR_GROQ_KEY_HERE":
        _groq_client = Groq(api_key=GROQ_API_KEY)
        _GROQ_OK     = True
        print(f"Chatbot LLM: {_GROQ_MODEL} via Groq")
    else:
        print("Groq key not set - visit https://console.groq.com for a FREE key")
except Exception as e:
    print(f"Groq setup failed: {e}")

# ---------------------------------------------------------------------------
# Account cache
# ---------------------------------------------------------------------------
_accounts_cache = []

def _load_accounts():
    global _accounts_cache
    if _accounts_cache:
        return _accounts_cache
    try:
        sf      = get_sf()
        result  = sf.query(get_soql())
        records = result.get("records", [])
        accs    = [build_account(i, r) for i, r in enumerate(records, 1)]
        accs.sort(key=lambda a: a.get("score", 0), reverse=True)
        _accounts_cache = accs
        print(f"Chatbot loaded {len(accs)} accounts")
    except Exception as e:
        print(f"Account load error: {e}")
    return _accounts_cache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fa(a):
    return (f"- **{a.get('name')}** | Score: {a.get('score',0)}/100 | "
            f"Priority: {a.get('priority','?')} | "
            f"Industry: {a.get('industry','N/A')} | "
            f"Revenue: {a.get('revenue_fmt','N/A')}")

def _fr(v):
    try:
        n = float(v or 0)
        if n >= 1e9: return f"${n/1e9:.1f}B"
        if n >= 1e6: return f"${n/1e6:.0f}M"
        if n >= 1e3: return f"${n/1e3:.0f}K"
        return f"${n:,.0f}" if n > 0 else "N/A"
    except: return "N/A"

# Industry keyword map
_IND = {
    "tech":           ["technology","software","high-tech"],
    "technology":     ["technology","software","high-tech"],
    "software":       ["software","technology"],
    "health":         ["healthcare","health","medical"],
    "healthcare":     ["healthcare","health","medical","pharmaceutical"],
    "medical":        ["healthcare","health","medical"],
    "pharma":         ["pharmaceutical","healthcare"],
    "pharmaceutical": ["pharmaceutical","healthcare"],
    "finance":        ["financial services","banking","finance","insurance"],
    "financial":      ["financial services","banking","finance","insurance"],
    "banking":        ["banking","financial services"],
    "insurance":      ["insurance","financial services"],
    "retail":         ["retail","retail & consumer goods","e-commerce"],
    "manufacturing":  ["manufacturing","industrial"],
    "consulting":     ["consulting","professional services"],
    "transportation": ["transportation","logistics","transportation & logistics"],
    "logistics":      ["transportation & logistics","logistics","transportation"],
    "education":      ["education","k-12","higher education"],
    "government":     ["government","public sector","gov-state","gov-federal"],
    "telecom":        ["telecommunications","telecom"],
    "energy":         ["energy","utilities"],
    "utilities":      ["energy","utilities"],
    "media":          ["media","entertainment"],
    "aerospace":      ["aerospace","defense"],
    "defense":        ["aerospace","defense"],
    "nonprofit":      ["non-profit","nonprofit"],
}

# US state name -> code
_STATES = {
    "california":"CA","texas":"TX","new york":"NY","florida":"FL",
    "illinois":"IL","ohio":"OH","georgia":"GA","washington":"WA",
    "arizona":"AZ","colorado":"CO","massachusetts":"MA","michigan":"MI",
    "north carolina":"NC","virginia":"VA","pennsylvania":"PA",
    "tennessee":"TN","minnesota":"MN","nevada":"NV","utah":"UT",
    "oregon":"OR","indiana":"IN","missouri":"MO",
}

# Region -> state codes
_REGIONS = {
    "southeast":   ["GA","FL","NC","SC","VA","TN","AL","MS","AR","LA","KY","WV"],
    "northeast":   ["NY","MA","CT","NJ","PA","NH","VT","ME","RI","MD","DE"],
    "midwest":     ["IL","OH","MI","WI","MN","IN","MO","IA","KS","NE","ND","SD"],
    "southwest":   ["TX","AZ","NM","OK","NV"],
    "west coast":  ["CA","WA","OR"],
    "west":        ["CA","WA","OR","CO","UT","ID","MT","WY","AK","HI"],
    "east coast":  ["NY","MA","CT","NJ","PA","NH","VT","ME","RI","MD","DE","VA","NC","SC","GA","FL"],
    "south":       ["GA","FL","NC","SC","VA","TN","AL","MS","AR","LA","TX","OK"],
    "mid-atlantic":["NY","NJ","PA","MD","DE","VA","DC"],
    "mid atlantic":["NY","NJ","PA","MD","DE","VA","DC"],
}

# Complexity patterns -> must go to Groq LLM
_COMPLEX_RE = [
    r"(high|medium|low).{1,50}(finance|tech|health|manufact|consult|retail|transpor|energy|pharma|bank|insur).{1,50}(california|texas|new york|florida|georgia|employ|revenue|employee|5[,0-9]+|10[,0-9]+)",
    r"why.{0,25}(score|priority|low|under.?score|rated)",
    r"(compare|vs\.?|versus|difference between).{1,50}(account|prospect|company|industry)",
    r"if i (focus|target|call|close|convert).{1,60}(what|how|which|total|pipeline)",
    r"(closest|likely to|about to|potential to).{1,40}(high|medium|convert|close|buy)",
    r"(pitch|proposal|strategy|approach).{1,40}(company|client|account|manufactur|health|finance)",
    r"(not.{1,20}contact|havent.{1,20}call|inactive).{1,40}(high|score|priority|why|which should)",
    r"which (rep|seller|owner|salesperson).{1,40}(best|highest|most|territory)",
    r"(cross.?sell|upsell).{1,40}(health|tech|finance|manufact|industry)",
    # Sales strategy / advisory questions -> always Groq
    r"how (do i|should i|can i|to).{1,40}(convince|persuade|sell|pitch|approach|close|win|engage|re.?engage|handle)",
    r"(convince|persuade|pitch to|sell to|approach).{1,40}(cio|cfo|cto|vp|director|executive|decision maker|manager)",
    r"(write|draft|give me).{1,40}(email|pitch|proposal|script|cold call|talking point|objection)",
    r"(objection|obstacle|challenge|pushback|concern|barrier).{1,40}(handl|overcome|face|sell|pitch|raise|expect|get|hear|anticipate|replace|switch)",
    r"(what|which|how).{1,15}(objection|obstacle|challenge|concern|pushback|barrier)",
    r"(best way|tips|advice|strategy|how to).{1,40}(sell|pitch|close|convert|re.?engage|follow.?up|cold.?call|negotiate)",
    r"how.{1,30}(switch|migrate|move|transition).{1,30}(from|to|between)",
]

# ---------------------------------------------------------------------------
# Groq LLM helpers
# ---------------------------------------------------------------------------
_SYSTEM = """You are an AI assistant for Lumen Technologies sales reps.

Lumen sells: IP VPN, SD-WAN, Cloud Connect, Dark Fiber, Managed Security, DDoS Mitigation,
Colocation, Unified Communications, MPLS, Wavelength, CDN, Ethernet.

Account data columns: Name|Industry|Priority|Score|Revenue|Employees|City,State|Owner|LastActivity
Score 0-100 (higher = better prospect). Priority: VERY HIGH > HIGH > MEDIUM > LOW.

YOU CAN ANSWER TWO TYPES OF QUESTIONS:

TYPE 1 - ACCOUNT/SALES QUESTIONS (use the provided CRM data):
- Which accounts to target, filter by priority/industry/revenue/location
- Sales strategy, pitch ideas, cross-sell opportunities
- Why an account has a low score
- Sort by Score for top/best questions
- NEVER invent company names or numbers not in the data

TYPE 2 - GENERAL KNOWLEDGE QUESTIONS (use your own knowledge):
- Tech definitions: "What is SD-WAN?", "Explain MPLS", "How does DDoS work?"
- General facts: "What is a cat?", "What is machine learning?"
- Sales skills: cold call tips, objection handling, negotiation tactics
- Any question not about the CRM data

RESPONSE FORMAT:
- Markdown bold and bullet points. Max 300 words.
- For account questions: end with a 1-sentence sales action tip.
- For general questions: just answer helpfully and concisely.

RETURN VALID JSON ONLY (no markdown fences):
{"answer": "...", "accounts": ["Name1"], "tip": "...", "intent": "label"}
For general knowledge: accounts=[] and tip can be empty or a sales connection."""


def _build_context(accounts, limit=25, filter_fn=None):
    src = sorted(accounts, key=lambda x: x.get("score", 0), reverse=True)
    if filter_fn:
        filtered = [a for a in src if filter_fn(a)]
        if filtered: src = filtered
    lines = []
    for a in src[:limit]:
        lines.append(
            f"{a.get('name')} | {a.get('industry','N/A')} | {a.get('priority','?')} | "
            f"Score:{a.get('score',0)} | Rev:{a.get('revenue_fmt','N/A')} | "
            f"Emp:{a.get('employees_fmt','N/A')} | "
            f"{a.get('billing_city','')},{a.get('billing_state','')} | "
            f"Owner:{a.get('owner_name','N/A')} | "
            f"LastAct:{a.get('last_activity','N/A')}"
        )
    return "\n".join(lines)


def _ask_llm(user_msg, accounts, filter_fn=None):
    if not _GROQ_OK or not _groq_client:
        return None
    ctx = _build_context(accounts, filter_fn=filter_fn)
    prompt = (f"Total accounts in CRM: {len(accounts)}\n"
              f"Top 25 relevant accounts (by score):\n{ctx}\n\n"
              f"USER QUESTION: {user_msg}")
    for attempt in range(2):
        try:
            comp = _groq_client.chat.completions.create(
                model=_GROQ_MODEL,
                messages=[
                    {"role":"system","content":_SYSTEM},
                    {"role":"user","content":prompt},
                ],
                temperature=0.3, max_tokens=700,
            )
            text = comp.choices[0].message.content.strip()
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()
            return json.loads(text)
        except json.JSONDecodeError:
            m2 = re.search(r"\{[\s\S]*\}", text if "text" in dir() else "")
            if m2:
                try: return json.loads(m2.group())
                except: pass
            return {"answer": text or "Could not parse AI response.", "accounts":[], "tip":"", "intent":"llm_raw"}
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                if attempt == 0: time.sleep(3); continue
                return {"answer":"**AI rate limit reached.** Wait 10 sec and ask again!","accounts":[],"tip":"Try 'summary' or 'high priority accounts'","intent":"quota"}
            print(f"Groq error: {e}")
            return None
    return None


def _resolve(names, accounts):
    nm = {a["name"].lower(): a for a in accounts}
    result = []
    for n in (names or []):
        acc = nm.get(n.lower())
        if acc: result.append(acc)
        else:
            for a in accounts:
                if n.lower() in a["name"].lower() or a["name"].lower() in n.lower():
                    result.append(a); break
    return result

# ---------------------------------------------------------------------------
# Local fast-path answers (zero Groq tokens)
# ---------------------------------------------------------------------------
def _local_answer(msg, accounts):
    m = msg.lower().strip()

    # -- Greeting --
    if re.search(r"^(hi|hello|hey|howdy|greetings|good morning|good afternoon)\b", m):
        return {
            "answer": (
                "**Hello! I'm your Lumen Sales AI Assistant (powered by Llama 3.3 70B).**\n\n"
                "I can help you with:\n"
                "- Find accounts by industry, priority, revenue, location\n"
                "- Top prospects & priority ranking\n"
                "- Cloud, IoT, Security targeting\n"
                "- Company information lookups\n"
                "- Weekly targets & upsell opportunities\n\n"
                "**Try asking:**\n"
                "- 'Show HIGH priority finance accounts'\n"
                "- 'Companies with over 10,000 employees'\n"
                "- 'Top 10 prospects'\n"
                "- 'Accounts in Texas'\n"
                "- 'Tell me about Wells Fargo'\n"
                "- 'Give me a summary'"
            ),
            "accounts":[], "tip":"Ask in plain English!", "intent":"greeting",
        }

    # -- Help --
    if re.search(r"\b(help|what can you|capabilities|what do you|what questions)\b", m):
        return {
            "answer": (
                "**Here's what I can do:**\n\n"
                "**Priority & Ranking:** Show HIGH/MEDIUM/LOW priority accounts, Top 10 prospects\n\n"
                "**Industry Search:** Finance, Tech, Healthcare, Manufacturing companies\n\n"
                "**Multi-Condition Filters (AI-powered):**\n"
                "- 'HIGH priority finance companies in California with 5,000+ employees'\n"
                "- 'LOW priority tech accounts with revenue over $500M - why?'\n"
                "- 'Best cross-sell opportunity in healthcare'\n\n"
                "**Regions:** Southeast, Northeast, Midwest, West Coast, Southwest\n\n"
                "**Company Info:** Tell me about Wells Fargo, CEO of AT&T\n\n"
                "**Analytics:** Which industries have highest average scores?"
            ),
            "accounts":[], "tip":"Ask me anything!", "intent":"help",
        }

    # -- Count / how many --
    if re.search(r"how many|total.{0,15}accounts|number of accounts|count of accounts", m):
        total = len(accounts)
        hi  = len([a for a in accounts if a.get("priority") in ("HIGH","VERY HIGH")])
        med = len([a for a in accounts if a.get("priority") == "MEDIUM"])
        low = len([a for a in accounts if a.get("priority") == "LOW"])
        if re.search(r"\bhigh\b", m):
            return {"answer":f"You have **{hi} HIGH priority** accounts.","accounts":[],"tip":"Engage these first!","intent":"count"}
        if re.search(r"\bmedium\b", m):
            return {"answer":f"You have **{med} MEDIUM priority** accounts.","accounts":[],"tip":"Nurture with regular touchpoints.","intent":"count"}
        if re.search(r"\blow\b", m):
            return {"answer":f"You have **{low} LOW priority** accounts.","accounts":[],"tip":"Add to drip campaign.","intent":"count"}
        return {"answer":f"You have **{total} accounts** total.\n- HIGH: **{hi}** | MEDIUM: **{med}** | LOW: **{low}**","accounts":[],"tip":"Focus on HIGH priority first!","intent":"count"}

    # -- Summary --
    if re.search(r"\b(summary|overview)\b", m) and not re.search(r"account |company ", m):
        total = len(accounts)
        hi  = len([a for a in accounts if a.get("priority") in ("HIGH","VERY HIGH")])
        med = len([a for a in accounts if a.get("priority") == "MEDIUM"])
        low = len([a for a in accounts if a.get("priority") == "LOW"])
        inds  = len(set(a.get("industry","") for a in accounts if a.get("industry")))
        avg   = int(sum(a.get("score",0) for a in accounts) / max(total,1))
        custs = len([a for a in accounts if "customer" in (a.get("type","") or "").lower()])
        tot_r = sum(float(a.get("revenue",0) or 0) for a in accounts)
        return {"answer":(f"**Account Summary**\n- Total: **{total}** | HIGH: **{hi}** | MEDIUM: **{med}** | LOW: **{low}**\n"
                          f"- Customers: **{custs}** | Industries: **{inds}** | Avg Score: **{avg}/100**\n"
                          f"- Total Revenue: **{_fr(tot_r)}**"),"accounts":[],"tip":"Ask about specific industries or priorities!","intent":"summary"}

    # -- Industry averages (local - uses ALL accounts) --
    if re.search(r"(industry|industries).{0,30}(average|avg|highest|best|score)|(average|avg).{0,20}score.{0,20}(industry|industri)", m):
        from collections import defaultdict
        totals = defaultdict(list)
        for a in accounts:
            ind = (a.get("industry") or "Unknown").strip()
            totals[ind].append(a.get("score",0))
        avgs = sorted([(ind, round(sum(s)/len(s)), len(s)) for ind,s in totals.items() if len(s)>=3],
                      key=lambda x: x[1], reverse=True)
        lines = ["**Industries by Average Prospect Score:**\n"]
        for ind,avg,cnt in avgs[:12]:
            lines.append(f"- **{ind}**: {avg}/100 avg ({cnt} accounts)")
        top_ind = avgs[0][0] if avgs else "N/A"
        top_accs = sorted([a for a in accounts if (a.get("industry") or "") == top_ind],
                          key=lambda x: x.get("score",0), reverse=True)[:5]
        return {"answer":"\n".join(lines),"accounts":top_accs,"tip":f"Focus on **{top_ind}** - highest avg score!","intent":"industry_averages"}

    # -- Complex multi-condition -> Groq LLM --
    for pat in _COMPLEX_RE:
        if re.search(pat, m):
            return None

    # -- Priority filters (must come before top-N to avoid over-matching) --
    if re.search(r"\bhigh\b.{0,20}priority|priority.{0,20}\bhigh\b|^high priority", m):
        f = sorted([a for a in accounts if a.get("priority") in ("HIGH","VERY HIGH")], key=lambda x: x.get("score",0), reverse=True)
        top = f[0] if f else None
        return {"answer":f"Found **{len(f)} HIGH priority** accounts!\n\n"+(f"Top: **{top.get('name')}** (Score: {top.get('score',0)}/100)" if top else ""),"accounts":f[:10],"tip":"Engage these immediately!","intent":"high_priority"}
    if re.search(r"\bmedium\b.{0,20}priority|priority.{0,20}\bmedium\b|^medium priority", m):
        f = sorted([a for a in accounts if a.get("priority") == "MEDIUM"], key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} MEDIUM priority** accounts.","accounts":f[:10],"tip":"Nurture with regular touchpoints.","intent":"medium_priority"}
    if re.search(r"\blow\b.{0,20}priority|priority.{0,20}\blow\b|^low priority", m):
        f = sorted([a for a in accounts if a.get("priority") == "LOW"], key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} LOW priority** accounts.","accounts":f[:10],"tip":"Add to drip campaign.","intent":"low_priority"}

    # -- Regional filter (Southeast, Northeast, Midwest, etc.) --
    for region_name, codes in _REGIONS.items():
        if region_name in m:
            f = sorted([a for a in accounts if (a.get("billing_state","") or "").upper() in codes],
                       key=lambda x: x.get("score",0), reverse=True)
            label = region_name.title()
            if not f:
                return {"answer":f"No accounts found in the **{label}**.","accounts":[],"tip":"Try a specific state.","intent":"region"}
            top = f[0]
            return {
                "answer":(f"Found **{len(f)} accounts** in the **{label}**!\n\n"
                          f"Top: **{top.get('name')}** (Score: {top.get('score',0)}/100, "
                          f"Priority: {top.get('priority','N/A')}, {top.get('billing_city','')}, {top.get('billing_state','')})\n\n"
                          + "\n".join(f"- **{a.get('name')}** | {a.get('billing_state','')} | Score:{a.get('score',0)} | {a.get('priority','?')} | {a.get('industry','N/A')}" for a in f[1:6])),
                "accounts":f[:10],"tip":f"Top {min(len(f),10)} {label} accounts by prospect score.","intent":"region",
            }

    # -- Top N accounts (only when no region term in query) --
    has_region = any(r in m for r in _REGIONS)
    if not has_region and re.search(r"\b(top|best|highest)\b.{0,15}\d+|\b(top|best)\b.{0,15}(accounts?|prospects?)", m):
        num_m = re.search(r"(\d+)", m)
        num   = int(num_m.group(1)) if num_m else 10
        top   = sorted(accounts, key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"**Top {num} accounts by prospect score:**\n\n"+"\n".join(_fa(a) for a in top[:min(num,5)]),"accounts":top[:num],"tip":"Sorted by AI prospect score - highest first!","intent":"top_accounts"}

    # -- Employee filter --
    if re.search(r"employ|staff|workers?", m) and re.search(r"\d+|thousand", m):
        num_m = re.search(r"([\d,]+)", m)
        threshold = int(re.sub(r"[^\d]","", num_m.group(1))) if num_m else 1000
        if "thousand" in m and threshold < 1000: threshold *= 1000
        f = sorted([a for a in accounts if int(a.get("employees",0) or 0) >= threshold],
                   key=lambda x: int(x.get("employees",0) or 0), reverse=True)
        return {"answer":f"Found **{len(f)} accounts** with **{threshold:,}+ employees**!","accounts":f[:10],"tip":"Larger teams = bigger deals!","intent":"employee_filter"}

    # -- Revenue filter --
    if re.search(r"revenue|annual\s+revenue", m) and re.search(r"over|more|above|greater|billion|million|\$", m):
        threshold = 100_000_000
        b  = re.search(r"([\d.]+)\s*b(?:illion)?", m)
        mv = re.search(r"([\d.]+)\s*m(?:illion)?", m)
        if b:    threshold = float(b.group(1)) * 1e9
        elif mv: threshold = float(mv.group(1)) * 1e6
        f = sorted([a for a in accounts if float(a.get("revenue",0) or 0) >= threshold],
                   key=lambda x: float(x.get("revenue",0) or 0), reverse=True)
        return {"answer":f"Found **{len(f)} accounts** with revenue >= **{_fr(threshold)}**!","accounts":f[:10],"tip":"Enterprise-level opportunities!","intent":"revenue_filter"}

    # -- Upsell / cross-sell (BEFORE industry filter) --
    if re.search(r"\b(upsell|expand|upgrade|grow account)\b|cross.?sell", m):
        f = sorted([a for a in accounts if (a.get("type","") or "").lower() in ("customer","partner")
                    and a.get("priority") in ("HIGH","VERY HIGH","MEDIUM")],
                   key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} upsell/cross-sell opportunities**!","accounts":f[:10],"tip":"Expand existing relationships first!","intent":"upsell"}

    # -- Industry filter --
    for ind_key in sorted(_IND.keys(), key=len, reverse=True):
        if re.search(r"\b" + re.escape(ind_key) + r"\b", m):
            ind_vals = _IND[ind_key]
            f = sorted([a for a in accounts if any(v in (a.get("industry","") or "").lower() for v in ind_vals)],
                       key=lambda x: x.get("score",0), reverse=True)
            label = ind_key.title()
            if not f:
                return {"answer":f"No **{label}** accounts found.","accounts":[],"tip":"Try a different industry.","intent":f"industry_{ind_key}"}
            top = f[0]
            return {
                "answer":(f"Found **{len(f)} {label}** companies!\n\n"
                          f"**Top: {top.get('name')}** (Score: {top.get('score',0)}/100, Priority: {top.get('priority','N/A')})\n\n"
                          + "\n".join(_fa(a) for a in f[1:4])),
                "accounts":f[:10],"tip":f"Ask 'top priority {label} account' to find the best one!","intent":f"industry_{ind_key}",
            }

    # -- Location filter --
    for state, code in _STATES.items():
        if state in m:
            f = sorted([a for a in accounts if (a.get("billing_state","") or "").upper() == code],
                       key=lambda x: x.get("score",0), reverse=True)
            return {"answer":f"Found **{len(f)} accounts** in **{state.title()}**!","accounts":f[:10],"tip":f"Target the {state.title()} market!","intent":"location_filter"}

    # -- Enterprise --
    if re.search(r"\b(enterprise|large compan|fortune\s*500|big compan)\b", m):
        f = sorted([a for a in accounts if int(a.get("employees",0) or 0) >= 1000 or float(a.get("revenue",0) or 0) >= 1e8],
                   key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} enterprise accounts**!","accounts":f[:10],"tip":"Enterprise = higher contract value!","intent":"enterprise"}

    # -- Cloud targets --
    if re.search(r"\b(cloud|aws|azure|saas|infrastructure)\b", m):
        _ci = ["technology","software","telecommunications","telecom","high tech"]
        f = sorted([a for a in accounts if any(re.search(r"\b"+v+r"\b",(a.get("industry","") or "").lower()) for v in _ci)
                    and int(a.get("employees",0) or 0) >= 50],
                   key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} companies** suitable for **Cloud Services**!","accounts":f[:10],"tip":"Technology & Software are the best cloud buyers!","intent":"cloud_targets"}

    # -- IoT targets --
    if re.search(r"\b(iot|internet of things)\b", m):
        _ii = ["manufacturing","transportation","logistics","energy","utilities","healthcare"]
        f = sorted([a for a in accounts if any(v in (a.get("industry","") or "").lower() for v in _ii)],
                   key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} companies** suitable for **IoT Solutions**!","accounts":f[:10],"tip":"Manufacturing & Logistics lead IoT adoption!","intent":"iot_targets"}

    # -- Not contacted / inactive --
    if re.search(r"not contacted|inactive|no.{0,10}follow|stale|6 months|six months|havent.{0,10}call", m):
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        f = sorted([a for a in accounts if not a.get("last_activity") or str(a.get("last_activity","")) < cutoff],
                   key=lambda x: x.get("score",0), reverse=True)
        return {"answer":f"Found **{len(f)} accounts** not contacted in 6+ months!","accounts":f[:10],"tip":"High-score inactive accounts = quick wins!","intent":"not_contacted"}

    # -- Largest by revenue --
    if re.search(r"\b(largest|biggest|most revenue|highest revenue|most valuable|richest)\b", m):
        f = sorted([a for a in accounts if float(a.get("revenue",0) or 0) > 0],
                   key=lambda x: float(x.get("revenue",0) or 0), reverse=True)
        if f:
            top = f[0]
            return {"answer":(f"**Largest account by revenue:**\n\n**{top.get('name')}**\n"
                              f"- Revenue: **{top.get('revenue_fmt','N/A')}**\n"
                              f"- Industry: {top.get('industry','N/A')}\n"
                              f"- Priority: {top.get('priority','N/A')}\n"
                              f"- Score: {top.get('score',0)}/100"),"accounts":f[:10],"tip":"Top 10 by revenue shown.","intent":"largest_account"}

    # -- Score filter --
    if re.search(r"\bscore\b.{0,20}(above|below|over|under|greater|more|less|\d+)", m):
        threshold = 70
        sm = re.search(r"(\d+)", m)
        if sm: threshold = int(sm.group(1))
        direction = "above" if re.search(r"above|over|greater|more", m) else "below"
        if direction == "above":
            f = sorted([a for a in accounts if a.get("score",0) >= threshold], key=lambda x: x.get("score",0), reverse=True)
        else:
            f = sorted([a for a in accounts if a.get("score",0) <= threshold], key=lambda x: x.get("score",0))
        return {"answer":f"Found **{len(f)} accounts** with score {direction} **{threshold}/100**!","accounts":f[:10],"tip":"Higher score = better prospect!","intent":"score_filter"}

    # -- Tech/product "what is X" questions -> Groq LLM, not company lookup --
    _TECH_TERMS = [
        "sd-wan","sdwan","mpls","vpn","ip vpn","dwdm","wavelength","cdn","ddos",
        "colocation","colo","ethernet","fiber","dark fiber","unified communications",
        "cloud connect","iot","internet of things","saas","paas","iaas","latency",
        "bandwidth","throughput","firewall","bgp","qos","sla","wan","lan",
        "ai ","machine learning","llm","neural network","sales pitch",
        "objection","cold call","discovery call","buying cycle","churn",
        "pipeline","forecast","quota","commission","crm","salesforce",
    ]
    if re.search(r"\b(what is|what are|how does|how do|explain|define)\b", m):
        stripped = re.sub(r"\b(what is|what are|how does|how do|explain|define)\b", "", m).strip()
        if any(t in stripped for t in _TECH_TERMS) or re.search(r"\b(work|function|benefit|differ|compare|vs)\b", stripped):
            return None  # route to Groq LLM

    # -- Company lookup --
    if re.search(r"tell me about|info on|info about|details about|who is|what is|ceo of|revenue of|score of|who manages|who owns|look up", m):
        strip = ["tell me about","info on","info about","details about","details on","look up","search for",
                 "what is the","what is","who is the","who is","what does","ceo of","revenue of","score of",
                 "owner of","who manages","who owns","tell me","about"]
        search = m
        for ph in sorted(strip, key=len, reverse=True):
            search = search.replace(ph, " ")
        search = " ".join(search.split()).strip()
        if len(search) >= 2:
            try:
                from enrichment.wikipedia_client import enrich
            except ImportError:
                enrich = lambda x: {}
            matched = [a for a in accounts if search in (a.get("name","") or "").lower()]
            if not matched:
                for w in [ww for ww in search.split() if len(ww) > 2]:
                    matched = [a for a in accounts if w in (a.get("name","") or "").lower()]
                    if matched: break
            if matched:
                acc  = matched[0]
                wiki = enrich(acc.get("name",""))
                return {
                    "answer":(
                        f"**{acc.get('name')}**\n\n"
                        f"- Revenue: {acc.get('revenue_fmt','N/A')}\n"
                        f"- Employees: {acc.get('employees_fmt','N/A')}\n"
                        f"- Industry: {acc.get('industry','N/A')}\n"
                        f"- Location: {', '.join(filter(None,[acc.get('billing_city'),acc.get('billing_state')])) or 'N/A'}\n"
                        f"- Priority: {acc.get('priority','N/A')}\n"
                        f"- Score: {acc.get('score',0)}/100\n"
                        f"- Owner: {acc.get('owner_name','N/A')}\n\n"
                        f"**Wikipedia:**\n"
                        f"- Industry: {wiki.get('wiki_industry','N/A')}\n"
                        f"- Founded: {wiki.get('wiki_founded','N/A')}\n"
                        f"- HQ: {wiki.get('wiki_hq','N/A')}\n"
                        f"- CEO: {wiki.get('wiki_ceo','N/A')}"
                    ),
                    "accounts":matched[:1],"tip":"Go to AI Insights tab for full analysis!","intent":"company_lookup",
                }

    # -- Weekly targets --
    if re.search(r"weekly target|this week|week target|per seller", m):
        try:
            from routes.weekly_targets import weekly_targets as _wt
            data    = _wt()
            sellers = data.get("sellers", [])
            lines   = [f"**Weekly Top 3 Targets - {data.get('week','This Week')}**\n"]
            for s in sellers[:5]:
                lines.append(f"**{s['owner']}** ({s['total_accounts']} accounts, {s['high_priority_count']} HIGH)")
                for t in s["top_targets"]:
                    medal = ["1st","2nd","3rd"][t["rank"]-1]
                    lines.append(f"  {medal} **{t['name']}** | Score: {t['score']}/100 | {t['priority']}")
                lines.append("")
            return {"answer":"\n".join(lines),"accounts":[t for s in sellers[:5] for t in s["top_targets"]],
                    "tip":f"{data['total_sellers']} sellers, {data['high_priority_total']} HIGH priority targets.","intent":"weekly_targets"}
        except Exception as e:
            return {"answer":f"Could not load weekly targets: {e}","accounts":[],"tip":"","intent":"weekly_targets"}

    return None  # -> Groq LLM


# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------
@router.post("/chat")
def chat(body: dict):
    user_message = (body.get("message") or "").strip()
    if not user_message:
        return {"answer":"Please type a question!","accounts":[],"tip":"","intent":"empty","ai_powered":False}

    accounts = _load_accounts()
    if not accounts:
        return {"answer":"No Salesforce data loaded yet. Connect from the Accounts tab first.",
                "accounts":[],"tip":"","intent":"no_data","ai_powered":False}

    # 1. Local fast-path
    local = _local_answer(user_message, accounts)
    if local:
        local["ai_powered"] = False
        return local

    # 2. Groq LLM for complex/open-ended questions
    llm_r = _ask_llm(user_message, accounts)
    if not llm_r:
        return {"answer":"AI is temporarily unavailable. Please try again.","accounts":[],"tip":"","intent":"error","ai_powered":False}

    return {
        "answer":     llm_r.get("answer",""),
        "accounts":   _resolve(llm_r.get("accounts",[]), accounts),
        "tip":        llm_r.get("tip",""),
        "intent":     llm_r.get("intent","llm"),
        "ai_powered": True,
    }

