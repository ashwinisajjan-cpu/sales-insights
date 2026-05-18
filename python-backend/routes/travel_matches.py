from fastapi import APIRouter, HTTPException, Query
from database.salesforce_client import get_sf, get_soql, build_account

router = APIRouter()


@router.get("/api/travel-matches")
def travel_matches(
    city:  str = Query(...,  description="City to search accounts in"),
    state: str = Query("",  description="Optional state/province filter"),
):
    """Find accounts in a given city (and optionally state) for in-person meetings."""
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]

        city_lower  = city.lower().strip()
        state_lower = state.lower().strip()

        matches = []
        for acc in accounts:
            acc_city  = acc.get("billing_city",  "").lower().strip()
            acc_state = acc.get("billing_state", "").lower().strip()
            if not city_lower or city_lower not in acc_city:
                continue
            if state_lower and state_lower not in acc_state:
                continue
            matches.append(acc)

        matches.sort(key=lambda a: a.get("score", 0), reverse=True)

        high_priority = [a for a in matches if a.get("priority") in ("HIGH", "VERY HIGH")]

        return {
            "city":          city.strip(),
            "state":         state.strip() or None,
            "total_matches": len(matches),
            "high_priority": len(high_priority),
            "accounts":      matches,
            "tip":           _travel_tip(city.strip(), matches, high_priority),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/travel-coverage")
def travel_coverage():
    """Return all cities grouped with account and high-priority counts for road-trip planning."""
    try:
        sf       = get_sf()
        result   = sf.query(get_soql())
        records  = result.get("records", [])
        accounts = [build_account(i, r) for i, r in enumerate(records, 1)]

        cities: dict = {}
        for acc in accounts:
            city  = acc.get("billing_city",  "").strip()
            state = acc.get("billing_state", "").strip()
            if not city:
                continue
            key = f"{city}, {state}" if state else city
            if key not in cities:
                cities[key] = {
                    "city":          city,
                    "state":         state,
                    "location":      key,
                    "count":         0,
                    "high_priority": 0,
                    "top_score":     0,
                }
            cities[key]["count"] += 1
            if acc.get("priority") in ("HIGH", "VERY HIGH"):
                cities[key]["high_priority"] += 1
            cities[key]["top_score"] = max(
                cities[key]["top_score"], acc.get("score", 0)
            )

        locations = sorted(
            cities.values(),
            key=lambda c: (c["high_priority"], c["count"]),
            reverse=True,
        )
        return {"locations": locations, "total_cities": len(locations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _travel_tip(city: str, matches: list, high_priority: list) -> str:
    if not matches:
        return f"No accounts found in {city}. Try a nearby city or check spelling."
    if high_priority:
        names = ", ".join(a["name"] for a in high_priority[:3])
        suffix = " and more" if len(high_priority) > 3 else ""
        return (
            f"{len(high_priority)} high-priority account(s) worth visiting: "
            f"{names}{suffix}"
        )
    return (
        f"{len(matches)} account(s) in {city} — lower priority but worth a check-in "
        f"while you're there."
    )
