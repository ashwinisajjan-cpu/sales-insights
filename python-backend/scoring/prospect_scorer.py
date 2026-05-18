HIGH_VALUE_INDUSTRIES = {
    "Technology": 20, "High Technology": 20,
    "Financial Services": 20, "Banking": 20, "Insurance": 18,
    "Healthcare": 18, "Pharmaceuticals": 18,
    "Energy": 16, "Utilities": 16,
    "Government": 15,
    "Telecommunications": 14,
    "Manufacturing": 13,
    "Retail": 12, "Consumer Goods": 12,
    "Transportation": 12,
    "Education": 10, "Media": 10,
}


def calc_score(revenue, employees, industry, acc_type, last_activity) -> int:
    score = 0
    try:
        rev = float(revenue or 0)
        if rev >= 5e9:   score += 40
        elif rev >= 1e9: score += 35
        elif rev >= 5e8: score += 28
        elif rev >= 1e8: score += 20
        elif rev >= 1e7: score += 12
        elif rev > 0:    score += 5
    except Exception:
        pass

    try:
        emp = int(employees or 0)
        if emp >= 50000:   score += 20
        elif emp >= 10000: score += 17
        elif emp >= 5000:  score += 14
        elif emp >= 1000:  score += 10
        elif emp >= 500:   score += 7
        elif emp >= 100:   score += 4
        elif emp > 0:      score += 2
    except Exception:
        pass

    ind = (industry or "").strip()
    score += HIGH_VALUE_INDUSTRIES.get(ind, 6)

    atype = (acc_type or "").lower()
    if "customer" in atype:     score += 10
    elif "prospect" in atype:   score += 7
    elif "partner" in atype:    score += 5
    elif "competitor" in atype: score += 1
    else:                       score += 4

    if last_activity:
        try:
            from datetime import datetime, timezone
            la   = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
            now  = datetime.now(timezone.utc)
            days = (now - la).days
            if days <= 30:    score += 10
            elif days <= 90:  score += 7
            elif days <= 180: score += 4
            elif days <= 365: score += 2
        except Exception:
            score += 3

    return min(score, 100)


def priority_from_score(score: int) -> str:
    if score >= 80: return "HIGH"
    if score >= 55: return "MEDIUM"
    return "LOW"


def action_from_priority(priority: str, acc_type: str) -> str:
    is_customer = "customer" in (acc_type or "").lower()
    if priority == "HIGH":
        return "Engage immediately — schedule executive meeting" if not is_customer else "Upsell / expand — schedule QBR"
    if priority == "MEDIUM":
        return "Nurture — send targeted content, follow up in 2 weeks"
    return "Monitor — add to drip campaign, revisit next quarter"


def calc_sales_potential(industry, acc_type) -> str:
    ind   = (industry or "").lower()
    atype = (acc_type or "").lower()
    base  = "Standard — evaluate specific needs"
    if "tech" in ind or "high-tech" in ind:
        base = "Strong — Cloud & Security solutions"
    elif "health" in ind:
        base = "High — Secure, compliant networks"
    elif "finance" in ind or "bank" in ind or "insurance" in ind:
        base = "Very High — Compliance & low-latency infra"
    elif "government" in ind or "public sector" in ind:
        base = "High — Government-grade secure infra"
    elif "telecom" in ind:
        base = "Medium — Partnership opportunity"
    elif "manufactur" in ind:
        base = "Medium — IoT & edge connectivity"
    elif "retail" in ind or "consumer" in ind:
        base = "Medium — Cloud & e-commerce backbone"
    elif "education" in ind:
        base = "Medium — Affordable broadband"
    elif "energy" in ind or "utilities" in ind:
        base = "High — OT/IT network convergence"
    if "customer" in atype:
        base = "⭐ " + base + " [Existing Customer]"
    return base


# ─────────────────────────────────────
# Lumen Services Mapping
# ─────────────────────────────────────

from config.settings import LUMEN_SERVICES

def get_lumen_services(
        account_type: str,
        industry: str,
        revenue: float,
        employees: int,
        description: str = "") -> dict:
    """
    Returns:
    - active_services: list of services 
      already provided
    - recommended_services: list of services 
      to upsell
    """
    active = []
    recommended = []

    acc_type = (account_type or "").lower()
    ind = (industry or "").lower()
    desc = (description or "").lower()
    rev = float(revenue or 0)
    emp = int(employees or 0)

    # ── Determine ACTIVE services ──
    # Based on account type (applies to all types)
    
    # Large enterprise customers/prospects
    if rev >= 1e9 or emp >= 10000:
        active.extend([
            "IP VPN",
            "MPLS",
            "Ethernet",
            "Managed Security",
        ])

    # Medium enterprise customers/prospects
    elif rev >= 1e7 or emp >= 1000:
        active.extend([
            "IP VPN",
            "Internet (Broadband)",
        ])

    # Small enterprise
    elif rev >= 1e6 or emp >= 100:
        active.extend([
            "Internet (Broadband)",
        ])

    # Industry specific active services
    if "financial" in ind or "bank" in ind:
        if "DDoS Mitigation" not in active:
            active.append("DDoS Mitigation")
        if "Managed Security" not in active:
            active.append("Managed Security")

    if "telecom" in ind:
        if "Dark Fiber" not in active:
            active.append("Dark Fiber")
        if "Wavelength" not in active:
            active.append("Wavelength")

    if "government" in ind or \
       "public sector" in ind:
        if "MPLS" not in active:
            active.append("MPLS")

    # Check description for clues
    if "voice" in desc or "phone" in desc:
        if "Voice Complete" not in active:
            active.append("Voice Complete")
    if "cloud" in desc:
        if "Cloud Connect" not in active:
            active.append("Cloud Connect")
    if "coloc" in desc or "data center" in desc:
        if "Colocation" not in active:
            active.append("Colocation")

    # ── Determine RECOMMENDED services ──
    # (not in active list)
    if "technology" in ind or "software" in ind:
        recommended.extend([
            "SD-WAN",
            "Cloud Connect",
            "CDN",
            "Managed Security",
        ])

    if "financial" in ind or "bank" in ind or \
       "insurance" in ind:
        recommended.extend([
            "SD-WAN",
            "Cloud Connect",
            "Managed Router",
            "Unified Communications",
        ])

    if "healthcare" in ind or "medical" in ind:
        recommended.extend([
            "Cloud Connect",
            "Managed Security",
            "Unified Communications",
            "SD-WAN",
        ])

    if "retail" in ind:
        recommended.extend([
            "SD-WAN",
            "CDN",
            "Ethernet",
            "Managed Router",
        ])

    if "manufacturing" in ind:
        recommended.extend([
            "SD-WAN",
            "Ethernet",
            "MPLS",
            "Managed Router",
        ])

    if "government" in ind:
        recommended.extend([
            "DDoS Mitigation",
            "Managed Security",
            "Unified Communications",
        ])

    if "education" in ind or "k-12" in ind:
        recommended.extend([
            "Internet (Broadband)",
            "Unified Communications",
            "SD-WAN",
        ])

    # Revenue based recommendations
    if rev >= 1e9:
        recommended.extend([
            "Dark Fiber",
            "Wavelength",
            "Colocation",
        ])

    # Remove duplicates and 
    # services already active
    recommended = list(set([
        s for s in recommended
        if s not in active
    ]))

    active = list(set(active))

    return {
        "active_services": active,
        "recommended_services": 
            recommended[:5],
        "total_active": len(active),
        "total_recommended": len(recommended),
        "method": "rule-based"
    }


# ─────────────────────────────────────
# AI-Enhanced Service Recommendations
# ─────────────────────────────────────

def get_ai_enhanced_services(
        account_name: str,
        account_type: str,
        industry: str,
        revenue: float,
        employees: int,
        description: str = "") -> dict:
    """
    Combines rule-based logic with AI analysis for smarter recommendations.
    AI provides context-aware suggestions based on company profile.
    """
    try:
        from ai.service_enricher import get_ai_services
        
        # Get AI recommendations
        ai_result = get_ai_services(
            account_name=account_name,
            industry=industry,
            revenue=revenue,
            employees=employees,
            description=description,
            account_type=account_type
        )
        
        # If AI failed, fallback to rule-based
        if "error" in ai_result:
            err = str(ai_result.get("error", ""))
            if "rate-limited" not in err:
                print(f"⚠️ AI returned error, falling back to rules: {err}")
            result = get_lumen_services(account_type, industry, revenue, employees, description)
            result["method"] = "rule-based (AI failed)"
            return result
        
        # Merge rule-based + AI results
        rule_result = get_lumen_services(account_type, industry, revenue, employees, description)
        
        # AI-enhanced result (prefer AI but include missed rule-based services)
        active = list(set(ai_result.get("active_services", []) + 
                         rule_result.get("active_services", [])))
        recommended = list(set(ai_result.get("recommended_services", []) + 
                              rule_result.get("recommended_services", [])))
        
        # Remove overlap
        recommended = [s for s in recommended if s not in active]
        
        return {
            "active_services": active[:5],
            "recommended_services": recommended[:5],
            "total_active": len(active),
            "total_recommended": len(recommended),
            "ai_reasoning": ai_result.get("ai_reasoning", ""),
            "method": "ai-enhanced"
        }
    except Exception as e:
        print(f"⚠️ AI enhancement failed: {e}")
        # Fallback to rule-based
        result = get_lumen_services(account_type, industry, revenue, employees, description)
        result["method"] = "rule-based (AI failed)"
        return result