from fastapi import APIRouter
from database.salesforce_client import get_sf, get_soql, build_account
from ai.insights_logic import build_ai_insights
from enrichment.wikipedia_client import enrich   # ✅ FIXED
from enrichment.real_locations import get_real_company_locations

router = APIRouter()


def _get_all_accounts():
    sf = get_sf()
    result = sf.query(get_soql())
    records = result.get("records", [])
    accounts = [build_account(i, r) for i, r in enumerate(records, 1)]
    accounts.sort(key=lambda a: a["score"], reverse=True)
    return accounts


def _find_account(company: str, accounts: list):
    company_lower = company.strip().lower()
    return next(
        (a for a in accounts if a.get("name", "").lower() == company_lower),
        next(
            (a for a in accounts if company_lower in a.get("name", "").lower()),
            None
        )
    )


@router.get("/wiki-search")
def wiki_search(company: str):
    return enrich(company)


@router.get("/ai-insight")
def get_ai_insight(company: str):
    try:
        accounts = _get_all_accounts()
        found = _find_account(company, accounts)

        if not found:
            return {
                "found": False,
                "company": company,
                "message": f"'{company}' not found in Salesforce."
            }

        return {"found": True, **found}

    except Exception as e:
        return {"error": str(e)}


@router.get("/company-insights")
def get_company_insights(company: str):
    try:
        accounts = _get_all_accounts()
        sf_acc = _find_account(company, accounts) or {}

        wiki = enrich(company)
        ai_ins = build_ai_insights(sf_acc, wiki)

        summary = {
            "name": sf_acc.get("name", wiki.get("wiki_title", company)),
            "website": sf_acc.get("website", "N/A"),
            "phone": sf_acc.get("phone", "N/A"),
            "salesforce_id": sf_acc.get("id", "N/A"),
            "wikipedia_url": wiki.get("wiki_url", "N/A"),
            "company_image": wiki.get("wiki_image", "N/A"),
            "industry": sf_acc.get("industry", wiki.get("wiki_industry", "N/A")),
            "account_type": sf_acc.get("type", "N/A"),
            "rating": sf_acc.get("rating", "N/A"),
            "annual_revenue": sf_acc.get("revenue_fmt", wiki.get("wiki_revenue", "N/A")),
            "employees": sf_acc.get("employees_fmt", wiki.get("wiki_employees", "N/A")),
            "founded": wiki.get("wiki_founded", "N/A"),
            "ceo": wiki.get("wiki_ceo", "N/A"),
            "location": sf_acc.get("billing_address", wiki.get("wiki_hq", "N/A")),
            "sales_director": sf_acc.get("owner_name", "N/A"),
            "director_email": sf_acc.get("owner_email", "N/A"),
            "parent_account": sf_acc.get("parent_name", "N/A"),
            "score": sf_acc.get("score", 0),
            "priority": sf_acc.get("priority", "N/A"),
            "recommended_action": sf_acc.get("recommended_action", "N/A"),
            "sales_potential": sf_acc.get("sales_potential", "N/A"),
            "last_activity": sf_acc.get("last_activity", "N/A"),

            # ✅ AI OUTPUT
            "financial_status": ai_ins.get("financial_status"),
            "headcount": ai_ins.get("headcount"),
            "mission": ai_ins.get("mission"),
            "core_values": ai_ins.get("core_values"),
            "solutions": ai_ins.get("solutions"),

            "wikipedia_summary": wiki.get("wiki_summary", "N/A"),
            "products": wiki.get("wiki_products", []),
            "description": sf_acc.get("description", wiki.get("wiki_summary", "N/A")),
        }

        return {
            "company": company,
            "sf_found": bool(sf_acc),
            "salesforce": sf_acc,
            "wikipedia": wiki,
            "ai_insights": ai_ins,
            "summary": summary,
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/api/company-locations")
def get_company_locations_api(company: str):
    """Get REAL global office locations for a company from Wikipedia + Salesforce"""
    try:
        # Get Salesforce account data
        accounts = _get_all_accounts()
        sf_acc = _find_account(company, accounts)
        
        # Get REAL locations from Wikipedia + Salesforce
        locations = get_real_company_locations(company, sf_acc)
        
        return {
            "company": company,
            "headquarters": locations.get("headquarters"),
            "countries": locations.get("countries", []),
            "major_offices": locations.get("major_offices", []),
            "offices_count": locations.get("offices_count"),
            "source": locations.get("source"),
        }
    except Exception as e:
        return {"error": str(e)}