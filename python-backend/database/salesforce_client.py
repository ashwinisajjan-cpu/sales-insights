from config.settings import (
    SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN,
    SF_DOMAIN, SOQL_BASE, OPTIONAL_FIELDS
)
from scoring.prospect_scorer import (
    calc_score, priority_from_score,
    action_from_priority, calc_sales_potential,
    get_lumen_services, get_ai_enhanced_services
)
from simple_salesforce import Salesforce

_sf_instance = None
_soql_ready  = False
SOQL         = SOQL_BASE


def get_sf():
    global _sf_instance, SOQL, _soql_ready
    if _sf_instance is None:
        try:
            _sf_instance = Salesforce(
                username=SF_USERNAME,
                password=SF_PASSWORD,
                security_token=SF_SECURITY_TOKEN,
                domain=SF_DOMAIN,
            )
            print("✅ Salesforce connected")
        except Exception as e:
            raise RuntimeError(f"Salesforce connection failed: {e}")
    if not _soql_ready:
        extra       = _discover_fields(_sf_instance)
        SOQL        = _build_soql(extra)
        _soql_ready = True
    return _sf_instance


def get_soql():
    return SOQL


def _discover_fields(sf) -> list:
    available = []
    try:
        fields = {f["name"] for f in sf.Account.describe()["fields"]}
        for f in OPTIONAL_FIELDS:
            if f in fields:
                available.append(f)
    except Exception as e:
        print(f"Field discovery warning: {e}")
    return available


def _build_soql(extra: list) -> str:
    if not extra:
        return SOQL_BASE.strip()
    extras = ",\n    ".join(extra)
    return SOQL_BASE.replace(
        "    LastActivityDate, CreatedDate",
        f"    LastActivityDate, CreatedDate,\n    {extras}",
    ).strip()


def safe(v):
    if v is None: return ""
    s = str(v).strip()
    return "" if s in ("None", "null", "none") else s


def fmt_revenue(v):
    try:
        n = float(v)
        if n == 0:   return "N/A"
        if n >= 1e9: return f"${n/1e9:.2f}B"
        if n >= 1e6: return f"${n/1e6:.2f}M"
        if n >= 1e3: return f"${n/1e3:.0f}K"
        return f"${n:,.0f}"
    except Exception:
        return "N/A"


def fmt_employees(v):
    try:
        n = int(v)
        return f"{n:,}" if n > 0 else "N/A"
    except Exception:
        return "N/A"


def get_owner(rec):
    try:
        o = rec.get("Owner") or {}
        return {
            "name":  o.get("Name",  "") if isinstance(o, dict) else "",
            "email": o.get("Email", "") if isinstance(o, dict) else "",
        }
    except Exception:
        return {"name": "", "email": ""}


def get_parent(rec):
    try:
        p = rec.get("Parent") or {}
        return {
            "id":   safe(rec.get("ParentId")),
            "name": p.get("Name", "") if isinstance(p, dict) else "",
        }
    except Exception:
        return {"id": "", "name": ""}


def _join_addr(parts):
    return ", ".join(p for p in parts if p) or "N/A"


def build_account(i, rec):
    revenue   = safe(rec.get("AnnualRevenue"))
    employees = safe(rec.get("NumberOfEmployees"))
    industry  = safe(rec.get("Industry"))
    acc_type  = safe(rec.get("Type"))
    last_act  = safe(rec.get("LastActivityDate"))
    owner     = get_owner(rec)
    parent    = get_parent(rec)
    score     = calc_score(revenue, employees, industry, acc_type, last_act)
    priority  = priority_from_score(score)
    
    # Get Lumen services with AI enrichment
    services = get_ai_enhanced_services(
        account_name=rec.get("Name", ""),
        account_type=acc_type,
        industry=industry,
        revenue=float(revenue) if revenue and revenue != "N/A" else 0,
        employees=int(employees) if employees and employees != "N/A" else 0,
        description=rec.get("Description", "")
    )

    return {
        "no":               i,
        "id":               safe(rec.get("Id")),
        "name":             safe(rec.get("Name")),
        "website":          safe(rec.get("Website")),
        "phone":            safe(rec.get("Phone")),
        "fax":              safe(rec.get("Fax")),
        "description":      safe(rec.get("Description")),
        "industry":         industry,
        "type":             acc_type,
        "rating":           safe(rec.get("Rating")),
        "lead_source":      safe(rec.get("LeadSource")),
        "account_source":   safe(rec.get("AccountSource")),
        "revenue":          revenue,
        "revenue_fmt":      fmt_revenue(revenue),
        "employees":        employees,
        "employees_fmt":    fmt_employees(employees),
        "owner_name":       owner["name"],
        "owner_email":      owner["email"],
        "parent_id":        parent["id"],
        "parent_name":      parent["name"],
        "billing_address":  _join_addr([
                                safe(rec.get("BillingStreet")),
                                safe(rec.get("BillingCity")),
                                safe(rec.get("BillingState")),
                                safe(rec.get("BillingPostalCode")),
                                safe(rec.get("BillingCountry")),
                            ]),
        "billing_city":     safe(rec.get("BillingCity")),
        "billing_state":    safe(rec.get("BillingState")),
        "billing_country":  safe(rec.get("BillingCountry")),
        "shipping_address": _join_addr([
                                safe(rec.get("ShippingStreet")),
                                safe(rec.get("ShippingCity")),
                                safe(rec.get("ShippingState")),
                                safe(rec.get("ShippingPostalCode")),
                                safe(rec.get("ShippingCountry")),
                            ]),
        "last_activity":    last_act,
        "created_date":     safe(rec.get("CreatedDate")),
        "score":            score,
        "priority":         priority,
        "recommended_action": action_from_priority(priority, acc_type),
        "sales_potential":  calc_sales_potential(industry, acc_type),
        "active_services":  services["active_services"],
        "recommended_services": services["recommended_services"],
        "total_active":     services["total_active"],
        "total_recommended": services["total_recommended"],
        "ai_reasoning":     services.get("ai_reasoning", ""),
        "services_method":  services.get("method", ""),
    }