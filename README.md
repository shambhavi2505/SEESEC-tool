# SEESEC Competitor Intelligence Platform

AI-powered competitive intelligence platform that monitors competitor content, identifies content gaps, and generates actionable recommendations for SEESEC's content strategy.

## Overview

SEESEC scrapes competitor blogs/resource sections, stores the content, classifies it by topic, and uses an LLM (via Groq) to generate a competitor intelligence summary — content strategy, top topics, content-type breakdown, publishing frequency, trending keywords, and a content gap analysis against SEESEC.

**System flow:**

```
Competitor Websites
        |
        v
   Scrapers (Playwright)
        |
        v
      SQLite / Postgres DB
        |
        +----------------+
        |                |
        v                v
  clustering.py       keywords.py
        |
        v
     comp_ai.py (Groq)
        |
        v
  ai_insights.json
        |
        v
   FastAPI Backend
        |
        v
   React Dashboard
        |
        v
   HTML / PDF Report
```

Key capabilities:

- On-demand competitor scraping (any company website, not just the tracked list)
- Topic categorization and keyword/trend extraction
- Content gap detection with a weighted gap score
- AI-generated competitor summaries and content recommendations
- Interactive analytics dashboard (overview, content feed, side-by-side comparison)
- Automated HTML/PDF report generation

## Competitors Tracked

Dedicated scrapers exist for:

- AuthBridge
- IDfy
- Signzy
- HyperVerge
- Bureau
- DigiTap

A generic scraper (`scraper/generic.py`) is also available and can analyze **any** competitor by URL through the dashboard's "Search a Competitor" feature, independent of the six above.

## Project Structure

```
├── analysis/
│   ├── ai.py            # Legacy Anthropic-based analysis (not used by main.py)
│   ├── clustering.py     # Rule-based topic tagging
│   ├── comp_ai.py        # Groq-based competitor summary/insights (used by main.py)
│   ├── keywords.py        # Keyword/bigram/trigram extraction
│   ├── opportunities.py   # Content gap scoring
│   └── techstack.py       # Tech stack detection from scraped HTML
│
├── database/
│   └── models.py          # SQLAlchemy models
│
├── reports/
│   ├── generator.py       # HTML/PDF report generation
│   └── scheduler.py       # Scheduled report runs
│
├── scraper/
│   ├── generic.py         # Generic scraper (used for "Search a Competitor")
│   ├── authbridge.py
│   ├── bureau.py
│   ├── digitap.py
│   ├── hyperverge.py
│   ├── idfy.py
│   ├── signzy.py
│   ├── run_analysis.py
│   ├── save_company.py
│   └── search.py
│
├── dashboard/              # React + Vite frontend
│   └── src/
│       ├── App.jsx
│       ├── SearchAnalyzeTab.jsx
│       ├── CompareCompaniesTab.jsx
│       ├── Login.jsx
│       └── config.js
│
├── output/
│   ├── ai_insights.json
│   └── reports/
│
├── main.py                 # FastAPI app and all API routes
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Quick Start

```bash
# Install backend dependencies
python -m pip install -r requirements.txt
python -m playwright install chromium

# Start the backend API
python main.py
# or: uvicorn main:app --reload

# In a separate terminal, start the dashboard
cd dashboard
npm install
npm run dev
```

- Backend: http://localhost:8000
- Dashboard: http://localhost:5173

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=
```

- `GROQ_API_KEY` — required for AI-generated competitor summaries (`analysis/comp_ai.py`).
- `DATABASE_URL` — optional. If unset, the app falls back to a local SQLite database. Set this to a Postgres connection string for a persistent/deployed database (requires `psycopg2-binary`, see Known Issues below).

For the dashboard, if you deploy the backend separately from the frontend, set `VITE_API_URL` (e.g. in Vercel) to point at your deployed backend URL. It defaults to `http://localhost:8000` for local development (`dashboard/src/config.js`).

## Standalone Scripts

These can be run independently of the API for local analysis/testing:

```bash
# Rule-based topic classification over already-scraped content
python analysis/clustering.py

# Generate the HTML intelligence report from current DB/insights
python reports/generator.py
```

```bash
# Test the generic scraper directly against a single site
python -m scraper.generic
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/content` | GET | Retrieve articles with filtering support |
| `/api/stats` | GET | Content statistics and distribution metrics |
| `/api/topics` | GET | Keywords, bigrams, trigrams, and topic insights |
| `/api/opportunities` | GET | Content gaps and AI-generated recommendations |
| `/api/competitors` | GET | List of tracked competitors |
| `/api/analyze` | POST | Trigger a new AI analysis run |
| `/api/analyze/status` | GET | Check analysis progress |
| `/api/search-company` | GET | Search for a company by name/domain |
| `/api/analyze-company` | POST | Run a full scrape + AI analysis on a given competitor URL |
| `/api/analyze-company/status/{company_name}` | GET | Live progress of an in-flight company analysis |
| `/api/compare-companies` | GET | Side-by-side comparison data for 2–4 analyzed companies |
| `/api/company/{company_name}` | GET | Full profile for a single analyzed company |
| `/api/companies` | GET | List of all companies analyzed so far |

## Dashboard Features

**Analyze Competitor**
- Search any competitor by URL and run a live scrape + AI analysis
- Real-time progress (scraping → saving → AI analysis → finalizing)
- Competitor profile: content strategy, top topics, tech stack, social presence, publishing frequency, trending keywords
- Content gap analysis against SEESEC with priority levels and recommendations

**Content Feed**
- Searchable, paginated content repository
- Filtering by competitor and topic

**Compare Competitors (Side-by-Side)**
- Benchmark 2–4 analyzed competitors against each other
- Radar chart visualization
- Keyword and topic comparisons

## Deployment

- **Backend**: containerized via the included `Dockerfile` (based on `mcr.microsoft.com/playwright/python`, which bundles Chromium). Designed for Render — reads the `PORT` env var at runtime, and the scraper detects the `RENDER` env var to apply container-safe Chromium launch flags automatically.
- **Frontend**: designed for Vercel; set `VITE_API_URL` to your deployed backend URL.

## Known Issues / Notes

- **`psycopg2-binary` fails to build locally on some setups** (missing `pg_config`) if you try to use a Postgres `DATABASE_URL`. For local development, leave `DATABASE_URL` unset to use SQLite instead, or install PostgreSQL locally to get `pg_config` on your PATH.
- **`analysis/ai.py` is legacy** and uses the Anthropic API — it is not called by `main.py`. The active AI pipeline is `analysis/comp_ai.py`, which uses Groq. Only `GROQ_API_KEY` is required to run the app as-is.
- **Chromium launch flags**: `scraper/generic.py` conditionally applies container-only Playwright launch flags (`--single-process`, etc.) based on the `RENDER` env var, since these flags can crash Chromium on local (especially Windows) machines. No manual changes are needed when switching between local and deployed environments.

## Gap Score Formula

```
Gap Score =
    (Number of competitors covering topic)
    × (Topic importance weight)
    ÷ (Current SEESEC coverage)
```

## Technologies Used

- Python, FastAPI, SQLAlchemy
- Playwright (scraping)
- Groq API (AI analysis/summaries)
- React + Vite (dashboard)
- HTML/PDF report generation