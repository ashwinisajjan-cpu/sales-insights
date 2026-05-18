import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database.salesforce_client import get_sf, build_account
from enrichment.wikipedia_client import enrich
from routes.accounts import router as accounts_router
from routes.insights import router as insights_router
from config.settings import WIKIPEDIA_API, HEADERS

# ── Create app FIRST ──────────────────────────────────────────
app = FastAPI(
    title="Sales Insights AI — Lumen",
    description="Salesforce + Wikipedia Enrichment + Prospect Scoring",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(insights_router)
from routes.chatbot import router as chat_router
app.include_router(chat_router)
from routes.weekly_targets import router as weekly_router
app.include_router(weekly_router)
from routes.travel_matches import router as travel_router
app.include_router(travel_router)


@app.get("/")
def home():
    return {
        "message": "✅ Sales Insights AI v4.0",
        "endpoints": [
            "GET /health",
            "GET /api/accounts",
            "GET /api/top-prospects",
            "GET /company-insights?company=NAME",
            "GET /account-profile/{id}",
            "GET /wiki-search?company=NAME",
            "GET /chart-data?company=NAME",
        ]
    }


@app.get("/health")
def health():
    try:
        sf    = get_sf()
        count = sf.query("SELECT COUNT() FROM Account").get("totalSize", 0)
        wiki_ok = False
        try:
            r = requests.get(
                f"{WIKIPEDIA_API}/Lumen_Technologies",
                headers=HEADERS, timeout=5
            )
            wiki_ok = r.status_code == 200
        except Exception:
            pass
        return {
            "status":         "✅ Healthy",
            "salesforce":     "OK",
            "total_accounts": count,
            "wikipedia":      "OK" if wiki_ok else "⚠️ Unreachable",
        }
    except Exception as e:
        return {"status": "❌ Failed", "error": str(e)}


@app.get("/chart-data")
def chart_data(company: str):
    try:
        from routes.accounts import get_accounts
        accounts    = get_accounts()
        company_low = company.strip().lower()
        sf_acc = next(
            (a for a in accounts if a["name"].lower() == company_low),
            next((a for a in accounts if company_low in a["name"].lower()), None),
        )
        try:
            base_rev = float((sf_acc or {}).get("revenue") or 0)
        except Exception:
            base_rev = 0
        try:
            base_emp = int((sf_acc or {}).get("employees") or 0)
        except Exception:
            base_emp = 0

        industry = (sf_acc or {}).get("industry", "") or ""
        score    = (sf_acc or {}).get("score", 50) or 50
        ind      = industry.lower()

        if base_rev > 0:
            rev_trend = {}
            r = base_rev
            for yr in [2024, 2023, 2022, 2021, 2020]:
                rev_trend[yr] = round(r / 1e6, 2)
                r = r / 1.08
        else:
            rev_trend = {y: "Not Available" for y in [2020, 2021, 2022, 2023, 2024]}

        if base_emp > 0:
            emp_trend = {}
            e = base_emp
            for yr in [2024, 2023, 2022, 2021, 2020]:
                emp_trend[yr] = int(round(e))
                e = e / 1.05
        else:
            emp_trend = {y: "Not Available" for y in [2020, 2021, 2022, 2023, 2024]}

        high   = min(score, 60)
        medium = min(100 - score, 30)
        low    = max(100 - high - medium, 10)

        if "tech" in ind or "software" in ind:
            segments = {"Cloud Services":40,"Cybersecurity":25,"Managed IT":20,"Consulting":15}
            sub      = {"SaaS":35,"Infrastructure":25,"AI & ML":20,"Data Analytics":12,"IoT":8}
        elif "financ" in ind or "bank" in ind or "insurance" in ind:
            segments = {"Retail Banking":35,"Investment":30,"Insurance":20,"Wealth Mgmt":15}
            sub      = {"Commercial Banking":30,"Capital Markets":25,"FinTech":20,"Asset Management":15,"Risk":10}
        elif "health" in ind:
            segments = {"Hospital Services":40,"Pharma":25,"Medical Devices":20,"Diagnostics":15}
            sub      = {"Acute Care":30,"Ambulatory":25,"Behavioral Health":15,"Home Health":20,"Labs":10}
        elif "telecom" in ind:
            segments = {"Enterprise":45,"Consumer":30,"Wholesale":15,"IoT":10}
            sub      = {"Fiber":30,"5G Wireless":25,"SD-WAN":20,"UCaaS":15,"Security":10}
        elif "energy" in ind or "utilities" in ind:
            segments = {"Generation":40,"Distribution":30,"Renewables":20,"Services":10}
            sub      = {"Solar":25,"Wind":20,"Natural Gas":30,"Nuclear":15,"Hydro":10}
        elif "manufactur" in ind:
            segments = {"Industrial":35,"Consumer Goods":30,"Automotive":20,"Aerospace":15}
            sub      = {"Heavy Machinery":30,"Electronics":25,"Chemicals":20,"Food Processing":15,"Textiles":10}
        else:
            segments = {"Core Business":50,"Services":25,"International":15,"Other":10}
            sub      = {"Segment A":35,"Segment B":30,"Segment C":20,"Segment D":10,"Other":5}

        return {
            "company":  (sf_acc or {}).get("name", company),
            "sf_found": sf_acc is not None,
            "revenue_trend":                [{"year":str(y),"revenue_M":v} for y,v in sorted(rev_trend.items())],
            "employee_growth":              [{"year":str(y),"employees":v} for y,v in sorted(emp_trend.items())],
            "sales_potential_distribution": [{"name":k,"value":v} for k,v in {"High":high,"Medium":medium,"Low":low}.items()],
            "industry_segment_contribution":[{"name":k,"value":v} for k,v in segments.items()],
            "industry_distribution":        [{"name":k,"value":v} for k,v in sub.items()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/ai-chat")
def ai_chat(data: dict):

    query = data.get("query")

    # ✅ For now (dummy response)
    response = f"You asked: {query}"

    return {"response": response}