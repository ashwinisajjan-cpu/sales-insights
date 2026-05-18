from fastapi import APIRouter, HTTPException
from database.salesforce_client import get_sf, get_soql, build_account
from enrichment.wikipedia_client import enrich
from ai.news_signals import get_news_signals
import json
import time
import requests

# Optional Gemini for locations lookup
try:
    import google.generativeai as genai
    from config.settings import GEMINI_API_KEY
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    _GENAI_OK = True
except Exception:
    genai = None
    _GENAI_OK = False

_LOCATIONS_CACHE: dict = {}
_LOC_COOLDOWN_UNTIL = 0.0

router = APIRouter()


@router.get("/api/accounts")
def get_accounts():
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]
        accounts.sort(key=lambda a: a["score"], reverse=True)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/top-prospects")
def top_prospects(limit: int = 10):
    try:
        accounts = get_accounts()
        return {
            "top_prospects":  accounts[:limit],
            "total_accounts": len(accounts),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/news-signals")
def news_signals(company: str):
    """Fetch news signals for a company — M&A, leadership changes, funding, etc."""
    try:
        return get_news_signals(company)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/hot-leads")
def hot_leads():
    """Return accounts that have recent high-value news signals."""
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]
        # Only check top 30 by score (to keep response time reasonable)
        top      = sorted(accounts, key=lambda a: a.get("score", 0), reverse=True)[:30]
        hot      = []
        for acc in top:
            news = get_news_signals(acc.get("name", ""))
            if news["hot_lead"] or news["score_boost"] > 0:
                acc["news_boost"]   = news["score_boost"]
                acc["news_signals"] = news["signals"]
                acc["news_score"]   = min(acc.get("score", 0) + news["score_boost"], 100)
                acc["hot_lead"]     = news["hot_lead"]
                hot.append(acc)
        hot.sort(key=lambda a: a["news_score"], reverse=True)
        return {"hot_leads": hot, "total": len(hot)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account-profile/{account_id}")
def get_account_profile(account_id: str):
    try:
        sf   = get_sf()
        soql = get_soql().replace(
            "FROM Account",
            f"FROM Account WHERE Id = '{account_id}' LIMIT 1"
        )
        records = sf.query(soql).get("records", [])
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"Account '{account_id}' not found."
            )
        sf_acc    = build_account(1, records[0])
        wiki_data = enrich(sf_acc["name"])
        return {
            "salesforce": sf_acc,
            "wikipedia":  wiki_data,
            "score":      sf_acc.get("score", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/weekly-targets")
def weekly_targets():
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]

        # Group by sales director
        seller_map = {}
        for acc in accounts:
            owner = acc.get("owner_name") or "Unassigned"
            if owner not in seller_map:
                seller_map[owner] = []
            seller_map[owner].append(acc)

        # Top 3 per seller
        weekly = []
        for seller, accs in seller_map.items():
            top3 = sorted(
                accs, key=lambda a: a.get("score", 0), reverse=True
            )[:3]
            weekly.append({
                "seller":         seller,
                "seller_email":   top3[0].get("owner_email", "") if top3 else "",
                "total_accounts": len(accs),
                "top_targets": [
                    {
                        "rank":               i + 1,
                        "name":               a.get("name"),
                        "score":              a.get("score", 0),
                        "priority":           a.get("priority"),
                        "industry":           a.get("industry"),
                        "revenue_fmt":        a.get("revenue_fmt"),
                        "employees_fmt":      a.get("employees_fmt"),
                        "location":           a.get("billing_address"),
                        "recommended_action": a.get("recommended_action"),
                        "sales_potential":    a.get("sales_potential"),
                        "last_activity":      a.get("last_activity"),
                        "website":            a.get("website"),
                        "phone":              a.get("phone"),
                    }
                    for i, a in enumerate(top3)
                ],
            })

        # Sort sellers by their best account score
        weekly.sort(
            key=lambda s: s["top_targets"][0]["score"] if s["top_targets"] else 0,
            reverse=True,
        )

        return {
            "week":          __import__("datetime").datetime.utcnow().strftime("%Y-W%U"),
            "total_sellers": len(weekly),
            "sellers":       weekly,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/travel-match")
def travel_match(city: str, state: str = ""):
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]

        city_lower  = city.strip().lower()
        state_lower = state.strip().lower()

        matched = [
            a for a in accounts
            if city_lower in (a.get("billing_city")    or "").lower()
            or city_lower in (a.get("billing_address") or "").lower()
        ]

        if state_lower:
            matched = [
                a for a in matched
                if state_lower in (a.get("billing_state")   or "").lower()
                or state_lower in (a.get("billing_address") or "").lower()
            ]

        matched.sort(key=lambda a: a.get("score", 0), reverse=True)

        high   = [a for a in matched if a.get("priority") == "HIGH"]
        medium = [a for a in matched if a.get("priority") == "MEDIUM"]
        low    = [a for a in matched if a.get("priority") == "LOW"]

        def _fmt(a):
            return {
                "name":               a.get("name"),
                "score":              a.get("score", 0),
                "priority":           a.get("priority"),
                "industry":           a.get("industry"),
                "revenue_fmt":        a.get("revenue_fmt"),
                "billing_address":    a.get("billing_address"),
                "owner_name":         a.get("owner_name"),
                "recommended_action": a.get("recommended_action"),
                "phone":              a.get("phone"),
                "website":            a.get("website"),
            }

        return {
            "travel_city":    city,
            "travel_state":   state,
            "total_matches":  len(matched),
            "high_priority":  [_fmt(a) for a in high[:5]],
            "medium_priority":[_fmt(a) for a in medium[:5]],
            "low_priority":   [_fmt(a) for a in low[:3]],
            "recommendation": (
                f"You are traveling to {city}. "
                f"There are {len(high)} HIGH priority accounts nearby. "
                + (
                    f"Top target: {high[0]['name']} "
                    f"(Score: {high[0]['score']}/100)"
                    if high else
                    "No HIGH priority accounts found in this location."
                )
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/company-locations/{name}")
def company_locations(name: str):
    """Return a structured list of a company's office/branch locations
    worldwide. Uses Gemini AI when available; falls back to Wikipedia HQ
    info if AI is unavailable or rate-limited."""
    global _LOC_COOLDOWN_UNTIL
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name required")

    key = name.lower()
    if key in _LOCATIONS_CACHE:
        return _LOCATIONS_CACHE[key]

    if _GENAI_OK and genai and time.time() >= _LOC_COOLDOWN_UNTIL:
        try:
            prompt = (
                f"List the office, branch, and corporate locations of "
                f"the company '{name}'. Return STRICT JSON only, no prose, "
                f"with this schema:\n"
                "{\n"
                '  "company": "...",\n'
                '  "headquarters": "City, State/Country",\n'
                '  "summary": "1-2 sentence overview of footprint",\n'
                '  "us_locations": [{"city":"","state":"","note":""}],\n'
                '  "international_locations": [{"city":"","country":"","note":""}],\n'
                '  "total_branches": "approx number or N/A",\n'
                '  "total_atms": "approx number or N/A"\n'
                "}\n"
                "Include all major hubs you know of. Return ONLY JSON."
            )
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(prompt)
            text = (resp.text or "").strip()
            import re as _re
            m = _re.search(r"\{.*\}", text, _re.DOTALL)
            if m:
                data = json.loads(m.group())
                data["source"] = "AI"
                _LOCATIONS_CACHE[key] = data
                return data
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "rate" in msg:
                _LOC_COOLDOWN_UNTIL = time.time() + 3600
            print(f"⚠️ Locations AI error for {name}: {e}")

    wiki = enrich(name)
    return {
        "company": name,
        "headquarters": wiki.get("wiki_hq", "N/A"),
        "summary": wiki.get("wiki_summary", "N/A"),
        "us_locations": [],
        "international_locations": [],
        "total_branches": "N/A",
        "total_atms": "N/A",
        "source": "Wikipedia (fallback)",
    }


@router.get("/api/wells-fargo-branches")
def wells_fargo_branches(city: str = "", state: str = ""):
    """
    Fetches Wells Fargo branches for a given city/state using their public locator API.
    """
    url = "https://www.wellsfargo.com/locator/service/search"
    params = {
        "serviceType": "BRANCH",
        "city": city,
        "state": state,
        "radius": 100,  # miles
        "limit": 1000   # max results
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        branches = [
            {
                "name": b.get("name"),
                "address": b.get("address", {}).get("line1"),
                "city": b.get("address", {}).get("city"),
                "state": b.get("address", {}).get("state"),
                "zip": b.get("address", {}).get("postalCode"),
                "phone": b.get("phone"),
            }
            for b in data.get("locations", [])
        ]
        return {"branches": branches, "total": len(branches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))