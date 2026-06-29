# SEESEC Competitor Intelligence Platform

AI-powered competitive intelligence platform that monitors competitor content, identifies content gaps, and generates actionable recommendations to support SEESEC's content strategy.

---

## Overview

This platform analyzes content published by six industry competitors, detects underserved topics, and provides AI-generated insights to help prioritize future content opportunities.

Key capabilities include:

* Competitor content monitoring and analysis
* Topic categorization and trend identification
* Content gap detection
* AI-powered content recommendations
* Interactive analytics dashboard
* Automated report generation

---

## Quick Start

```bash
# Run AI analysis
python analysis/ai.py

# Start the backend API
python main.py

# Start the dashboard
cd dashboard && npm run dev
```

Backend: http://localhost:8000

Dashboard: http://localhost:5173

---

## Setup & Execution

### 1. Topic Classification

```bash
python analysis/clustering.py
```

Classifies articles into predefined topics using rule-based tagging.

### 2. AI Analysis

```bash
python analysis/ai.py
```

Performs content gap analysis and generates recommendations.

Results are saved to:

```bash
output/ai_insights.json
```

### 3. Generate Report

```bash
python reports/generator.py
```

Creates an HTML report that can be exported as a PDF.

Output:

```bash
output/seesec_intelligence_report.html
```

### 4. Start API Server

```bash
python main.py
```

### 5. Launch Dashboard

```bash
cd dashboard
npm install
npm run dev
```

---

## Project Structure

```text
├── analysis/
│   ├── keywords.py
│   ├── clustering.py
│   ├── ai.py
│   └── opportunities.py
│
├── reports/
│   └── generator.py
│
├── dashboard/
│   └── src/App.jsx
│
├── database/
│   └── models.py
│
├── output/
│   ├── ai_insights.json
│   └── seesec_intelligence_report.html
│
├── main.py
└── .env
```

---

## API Endpoints

| Endpoint                  | Description                                     |
| ------------------------- | ----------------------------------------------- |
| GET `/api/content`        | Retrieve articles with filtering support        |
| GET `/api/stats`          | Content statistics and distribution metrics     |
| GET `/api/topics`         | Keywords, bigrams, trigrams, and topic insights |
| GET `/api/opportunities`  | Content gaps and AI-generated recommendations   |
| GET `/api/competitors`    | List of tracked competitors                     |
| POST `/api/analyze`       | Trigger a new AI analysis run                   |
| GET `/api/analyze/status` | Check analysis progress                         |

---

## Dashboard Features

### Overview

* Content statistics
* Competitor comparison charts
* Keyword trends
* Topic distribution insights

### Content Feed

* Searchable content repository
* Filtering by competitor and topic
* Pagination support

### Opportunities

* Content gap analysis
* AI-generated recommendations
* Priority content opportunities

### Competitor Comparison

* Competitor benchmarking
* Radar chart visualization
* Keyword and topic comparisons

---

## Competitors Tracked

* AuthBridge
* IDfy
* Signzy
* HyperVerge
* Bureau
* DigiTap

---

## Cost

| Component            | Cost                        |
| -------------------- | --------------------------- |
| Topic Classification | Free                        |
| Keyword Analysis     | Free                        |
| AI Analysis          | Approximately $0.05 per run |
| Report Generation    | Free                        |

AI analysis results are cached in `output/ai_insights.json`, minimizing repeated API costs.

---

## Technologies Used

* Python
* FastAPI
* React
* SQLAlchemy
* Anthropic Claude API
* HTML Report Generation

---

## Environment Variables

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key
```
