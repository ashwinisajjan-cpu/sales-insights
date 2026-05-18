import os

# ── Salesforce ──
SF_USERNAME        = os.getenv("SF_USERNAME",       "l3svc@lumen.com.prod")
SF_PASSWORD        = os.getenv("SF_PASSWORD",       "QdTest@2026")
SF_SECURITY_TOKEN  = os.getenv("SF_SECURITY_TOKEN", "")
SF_DOMAIN          = os.getenv("SF_DOMAIN",         "login")

# ── Free Enrichment APIs ──
WIKIPEDIA_API      = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKIPEDIA_SEARCH   = "https://en.wikipedia.org/w/api.php"
DUCKDUCKGO_API     = "https://api.duckduckgo.com/"

HEADERS = {
    "User-Agent": "LumenSalesInsightsAI/3.0 (sales-tool; contact@lumen.com)"
}

# ── SOQL ──
SOQL_BASE = """
SELECT
    Id, Name, Website, Phone,
    Industry, Type, Description,
    AnnualRevenue, NumberOfEmployees,
    Owner.Name, Owner.Email,
    ParentId, Parent.Name,
    BillingStreet, BillingCity, BillingState,
    BillingPostalCode, BillingCountry,
    ShippingStreet, ShippingCity, ShippingState,
    ShippingPostalCode, ShippingCountry,
    LastActivityDate, CreatedDate
FROM Account
LIMIT 200
"""

OPTIONAL_FIELDS = ["Fax", "LeadSource", "Rating", "AccountSource"]