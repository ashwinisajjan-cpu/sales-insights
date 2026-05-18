def build_ai_insights(sf_acc: dict, wiki: dict) -> dict:
    rev_sf = sf_acc.get("revenue_fmt", "N/A")
    rev_wi = wiki.get("wiki_revenue", "N/A")

    if rev_sf not in ("N/A", ""):
        financial = f"Annual Revenue: {rev_sf}"
    elif rev_wi not in ("N/A", ""):
        financial = f"Estimated Revenue: {rev_wi}"
    else:
        financial = "Financial data not available"

    return {
        "financial_status": financial,
        "headcount": sf_acc.get("employees_fmt", "N/A"),
        "mission": wiki.get("wiki_mission", "Not available"),
        "core_values": wiki.get("wiki_core_values", "Not available"),
        "solutions": wiki.get("wiki_solutions", "Not available"),
    }