from fastapi import APIRouter
from database.salesforce_client import get_sf, get_soql, build_account
from datetime import datetime, timedelta

router = APIRouter()

_accounts_cache = []

def _get_accounts():
    global _accounts_cache
    if not _accounts_cache:
        try:
            sf      = get_sf()
            result  = sf.query(get_soql())
            records = result.get("records", [])
            _accounts_cache = [build_account(i, r) for i, r in enumerate(records, 1)]
        except Exception as e:
            print(f"Weekly targets account load error: {e}")
    return _accounts_cache


def _week_label():
    today  = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"


@router.get("/api/weekly-targets")
def weekly_targets():
    """
    Returns top 3 accounts per sales owner/director for the current week,
    ranked by prospect score.
    """
    accounts = _get_accounts()

    # Group accounts by owner
    by_owner: dict = {}
    for acc in accounts:
        owner = acc.get("owner_name") or "Unassigned"
        by_owner.setdefault(owner, []).append(acc)

    # For each owner pick top 3 by score
    week = _week_label()
    sellers = []
    for owner, accs in sorted(by_owner.items()):
        top3 = sorted(accs, key=lambda a: a.get("score", 0), reverse=True)[:3]
        high_count = len([a for a in accs if a.get("priority") in ("HIGH", "VERY HIGH")])
        sellers.append({
            "owner":        owner,
            "total_accounts": len(accs),
            "high_priority_count": high_count,
            "top_targets":  [
                {
                    "rank":         idx + 1,
                    "name":         a.get("name"),
                    "score":        a.get("score", 0),
                    "priority":     a.get("priority"),
                    "industry":     a.get("industry"),
                    "revenue_fmt":  a.get("revenue_fmt"),
                    "employees_fmt":a.get("employees_fmt"),
                    "billing_city": a.get("billing_city"),
                    "billing_state":a.get("billing_state"),
                    "action":       a.get("action"),
                    "website":      a.get("website"),
                    "phone":        a.get("phone"),
                }
                for idx, a in enumerate(top3)
            ],
        })

    # Sort sellers: most high-priority accounts first
    sellers.sort(key=lambda s: s["high_priority_count"], reverse=True)

    total_targets = sum(len(s["top_targets"]) for s in sellers)
    high_total    = sum(s["high_priority_count"] for s in sellers)

    return {
        "week":           week,
        "total_sellers":  len(sellers),
        "total_targets":  total_targets,
        "high_priority_total": high_total,
        "sellers":        sellers,
    }


@router.get("/api/weekly-targets/{owner_name}")
def weekly_targets_for_seller(owner_name: str):
    """
    Returns top 3 accounts for a specific sales owner.
    """
    accounts = _get_accounts()
    name_lower = owner_name.lower().replace("-", " ")

    owner_accs = [
        a for a in accounts
        if name_lower in (a.get("owner_name") or "").lower()
    ]

    if not owner_accs:
        return {"error": f"No accounts found for seller '{owner_name}'", "sellers": []}

    owner_label = owner_accs[0].get("owner_name", owner_name)
    top3 = sorted(owner_accs, key=lambda a: a.get("score", 0), reverse=True)[:3]

    return {
        "week":   _week_label(),
        "owner":  owner_label,
        "total_accounts": len(owner_accs),
        "top_targets": [
            {
                "rank":          idx + 1,
                "name":          a.get("name"),
                "score":         a.get("score", 0),
                "priority":      a.get("priority"),
                "industry":      a.get("industry"),
                "revenue_fmt":   a.get("revenue_fmt"),
                "employees_fmt": a.get("employees_fmt"),
                "billing_city":  a.get("billing_city"),
                "billing_state": a.get("billing_state"),
                "action":        a.get("action"),
                "website":       a.get("website"),
                "phone":         a.get("phone"),
            }
            for idx, a in enumerate(top3)
        ],
    }
