import os
from dotenv import load_dotenv

load_dotenv()

SF_USERNAME       = os.getenv("SF_USERNAME")
SF_PASSWORD       = os.getenv("SF_PASSWORD")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN")
SF_DOMAIN         = os.getenv("SF_DOMAIN", "login")

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

"""

OPTIONAL_FIELDS = ["Fax", "LeadSource", "Rating", "AccountSource"]

HEADERS = {"User-Agent": "LumenSalesInsightsAI/4.0 (sales-tool; contact@lumen.com)"}

WIKIPEDIA_API    = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKIPEDIA_SEARCH = "https://en.wikipedia.org/w/api.php"
DUCKDUCKGO_API   = "https://api.duckduckgo.com/"

# Google Gemini AI API
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

# Groq AI API (Llama 3.3 70B) — free tier: 14,400 req/day, 30 req/min
# Get your FREE key at: https://console.groq.com → API Keys → Create API Key
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

# Lumen Services Catalog
LUMEN_SERVICES = [
    "IP VPN",
    "SD-WAN",
    "DDoS Mitigation",
    "Managed Security",
    "Cloud Connect",
    "Colocation",
    "Voice Complete",
    "Dark Fiber",
    "Ethernet",
    "CDN",
    "Unified Communications",
    "MPLS",
    "Internet (Broadband)",
    "Managed Router",
    "Wavelength",
]