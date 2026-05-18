# Sales Insights AI — Lumen  v4.0
> Salesforce + Wikipedia Enrichment + AI Prospect Scoring

---

## PROJECT STRUCTURE

```
sales-insights/
├── backend/
│   ├── main.py              ← FastAPI backend (ALL logic here)
│   └── requirements.txt
└── frontend/
    ├── package.json
    └── src/
        ├── App.jsx          ← React frontend (ALL UI here)
        └── main.jsx
```

---

## STEP 1 — Set up the backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

✅ Backend is running at: http://localhost:8000

---

## STEP 2 — Set up the frontend

```bash
# Open a NEW terminal tab
cd frontend

npm install
npm run dev
```

✅ Frontend is running at: http://localhost:5173

---

## WHAT EACH ENDPOINT DOES

| Endpoint | What it returns |
|---|---|
| `GET /health` | Salesforce + Wikipedia connection status |
| `GET /api/accounts` | All 200 accounts with score, priority, action |
| `GET /api/top-prospects?limit=10` | Top N scored accounts |
| `GET /company-insights?company=NAME` | Full SF + Wikipedia + AI insight for one company |
| `GET /account-profile/{id}` | Deep profile by Salesforce Account ID |
| `GET /wiki-search?company=NAME` | Wikipedia-only lookup |

---

## SCORING MODEL (0–100)

| Factor | Max Points | How |
|---|---|---|
| Revenue | 40 | $5B+ = 40, $1B+ = 35, $500M+ = 28 ... |
| Employees | 20 | 50k+ = 20, 10k+ = 17, 5k+ = 14 ... |
| Industry fit | 20 | Technology/Finance = 20, Energy = 16 ... |
| Engagement | 10 | Last activity ≤30 days = 10, ≤90 = 7 ... |
| Account type | 10 | Customer = 10, Prospect = 7, Other = 4 |

**Priority:** Score ≥80 = HIGH · Score ≥55 = MEDIUM · Score <55 = LOW

---

## THE 5 TABS

1. **Accounts** — Full sortable table with score badge, priority chip, and recommended action
2. **AI Insights** — Search any company → get Salesforce data + Wikipedia enrichment
3. **Top Prospects** — Ranked list of top 10 targets for the week + scoring explanation
4. **Dashboard** — Full KPI view for selected company
5. **Charts** — Revenue by industry, priority distribution, employee distribution

---

## SALESFORCE CREDENTIALS

Edit these in `backend/main.py` or set as environment variables:

```python
SF_USERNAME       = "l3svc@lumen.com.prod"
SF_PASSWORD       = "QdTest@2026"
SF_SECURITY_TOKEN = ""          # leave blank if IP is whitelisted
SF_DOMAIN         = "login"     # use "test" for sandbox
```

Or set env vars (recommended for production):
```bash
export SF_USERNAME=l3svc@lumen.com.prod
export SF_PASSWORD=QdTest@2026
```

---

## COMMON ISSUES

| Problem | Fix |
|---|---|
| `CORS error` | Make sure backend is on port 8000 |
| `Salesforce connection failed` | Check username/password/token in main.py |
| `Wikipedia returns N/A` | Normal for private/small companies |
| `Score is 0` | Account has no revenue, employees, or industry in Salesforce |