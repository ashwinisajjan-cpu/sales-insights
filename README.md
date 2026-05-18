# Sales Insights AI - Lumen Sales Intelligence Platform

A full-stack AI-powered sales intelligence application built with React, FastAPI, and Groq LLM. Provides real-time prospect scoring, enrichment, and AI-driven sales coaching.

## Features

- **Prospect Database**: Browse 1000+ Salesforce accounts with advanced filtering
- **AI Insights**: Company enrichment from Salesforce, Wikipedia, and Google News
- **Top Prospects**: AI-ranked prospects by priority (HIGH/MEDIUM/LOW)
- **Weekly Targets**: Personalized top-3 targets for 108+ sellers
- **Travel Planner**: Geographic-based account matching
- **Dashboard**: Deep company profiles with all enrichment data
- **Charts**: Industry distribution, revenue breakdown, employee size analysis
- **AI Chatbot**: Sales strategy coaching powered by Groq Llama 3.3 70B LLM

## Tech Stack

**Backend:**
- FastAPI 0.111.0
- Python 3.12.7
- Salesforce (simple-salesforce)
- Groq LLM (Llama 3.3 70B)
- Wikipedia REST API
- Google News RSS

**Frontend:**
- React 18.2.0
- Vite 5.1.4
- Recharts 2.10.3

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Salesforce credentials
- Groq API key (free at https://console.groq.com)

### Backend Setup

```bash
cd python-backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

Create `.env` from `.env.example`:
```bash
cp .env.example .env
# Edit .env with your Salesforce and Groq credentials
```

Run backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:5173`

## API Endpoints

- `GET /api/accounts?limit=10` - Get accounts list
- `GET /api/top-prospects?limit=10` - Get top-ranked prospects
- `GET /api/insights?company=NAME` - Get company enrichment
- `GET /api/news-signals?company=NAME` - Get news signals (M&A, funding, etc.)
- `GET /api/weekly-targets` - Get seller weekly targets
- `GET /api/travel-matches?city=NAME` - Get location-based matches
- `POST /chat` - Chat with AI sales coach

## Configuration

Set environment variables in `.env`:

```
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_security_token
SF_DOMAIN=login
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## License

Proprietary - Lumen Technologies

## Support

For issues or questions, contact the development team.
