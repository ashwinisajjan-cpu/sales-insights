import warnings
warnings.filterwarnings("ignore", message=".*Metaclasses with custom tp_new.*")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception as e:
    genai = None
    GEMINI_AVAILABLE = False

from config.settings import GEMINI_API_KEY, LUMEN_SERVICES
import json
import re
import time

# Configure Gemini API (only if available)
if GEMINI_AVAILABLE and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except:
        pass

# In-memory cache of AI results keyed by account name (avoid re-enriching)
_AI_CACHE: dict = {}

# Cooldown state: when Gemini returns 429 (quota exceeded), pause AI calls
# for a while so the app stays responsive via the rule-based fallback.
_RATE_LIMIT_COOLDOWN_UNTIL: float = 0.0
_COOLDOWN_SECONDS = 60 * 60  # 1 hour after a quota error
_QUOTA_EXHAUSTED = False  # set True when daily quota is hit

def get_ai_services(
    account_name: str,
    industry: str,
    revenue: float,
    employees: int,
    description: str = "",
    account_type: str = "") -> dict:
    """
    Uses Google Gemini AI to analyze company and recommend Lumen services
    based on real-world understanding of the company.
    
    Returns:
    - active_services: Services they likely already use
    - recommended_services: Services to upsell
    - ai_reasoning: Why these services were chosen
    """
    
    try:
        # Check if Gemini is available
        if not GEMINI_AVAILABLE or not genai:
            return {
                "error": "Gemini API not available",
                "active_services": [],
                "recommended_services": [],
                "total_active": 0,
                "total_recommended": 0
            }

        # Serve from cache if we've already enriched this account
        cache_key = (account_name or "").strip().lower()
        if cache_key and cache_key in _AI_CACHE:
            return _AI_CACHE[cache_key]

        # If we previously hit a quota/rate-limit error, skip Gemini
        # quietly and let the caller fall back to rules.
        global _RATE_LIMIT_COOLDOWN_UNTIL, _QUOTA_EXHAUSTED
        if _QUOTA_EXHAUSTED or time.time() < _RATE_LIMIT_COOLDOWN_UNTIL:
            return {
                "error": "AI rate-limited (using fallback)",
                "active_services": [],
                "recommended_services": [],
                "total_active": 0,
                "total_recommended": 0
            }
        
        # Build context for AI
        context = f"""
        Company: {account_name}
        Industry: {industry}
        Annual Revenue: ${revenue:,.0f} (${revenue/1e9:.2f}B)
        Employees: {employees:,}
        Account Type: {account_type}
        Description: {description}
        
        Available Lumen Services:
        {', '.join(LUMEN_SERVICES)}
        """
        
        prompt = f"""You are a Lumen telecommunications expert. Analyze this company and recommend services.

{context}

Based on this company's profile, profile, and industry:
1. List 3-5 services they LIKELY ALREADY USE (active_services)
2. List 3-5 services to RECOMMEND for upsell (recommended_services)
3. Provide brief reasoning

Format your response as JSON:
{{
    "active_services": ["service1", "service2", ...],
    "recommended_services": ["service1", "service2", ...],
    "reasoning": "Brief explanation of why these services"
}}

Only return valid JSON, no other text."""

        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        if not response.text:
            return {"error": "No response from AI"}
        
        # Parse AI response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                ai_result = json.loads(response.text)
            
            # Validate and clean results
            active = [s for s in ai_result.get("active_services", []) 
                     if s in LUMEN_SERVICES]
            recommended = [s for s in ai_result.get("recommended_services", []) 
                          if s in LUMEN_SERVICES and s not in active]
            
            print(f"✅ AI enrichment SUCCESS for {account_name}: {len(active)} active, {len(recommended)} recommended")
            
            result = {
                "active_services": active[:5],
                "recommended_services": recommended[:5],
                "total_active": len(active),
                "total_recommended": len(recommended),
                "ai_reasoning": ai_result.get("reasoning", ""),
                "source": "AI"
            }
            if cache_key:
                _AI_CACHE[cache_key] = result
            return result
            
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}
            
    except Exception as e:
        error_msg = str(e)
        # Detect quota / rate-limit errors and trip the cooldown so we
        # stop hammering the API and silently fall back to rules.
        lower = error_msg.lower()
        if "429" in error_msg or "quota" in lower or "rate" in lower or "resourceexhausted" in lower:
            _RATE_LIMIT_COOLDOWN_UNTIL = time.time() + _COOLDOWN_SECONDS
            if "perday" in lower.replace(" ", "") or "per day" in lower or "daily" in lower:
                _QUOTA_EXHAUSTED = True
            print(f"⏸️  Gemini rate-limited; falling back to rules for next {_COOLDOWN_SECONDS}s")
            return {
                "error": "AI rate-limited (using fallback)",
                "active_services": [],
                "recommended_services": [],
                "total_active": 0,
                "total_recommended": 0
            }
        print(f"❌ AI enrichment error for {account_name}: {error_msg}")
        return {
            "error": error_msg,
            "active_services": [],
            "recommended_services": [],
            "total_active": 0,
            "total_recommended": 0
        }
