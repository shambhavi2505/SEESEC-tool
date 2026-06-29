# SEESEC Competitor Intelligence Platform

## Objective

Build a tool that monitors competitor content and identifies
content opportunities for SEESEC.

The platform tracks competitor blogs, analyzes topics,
detects content gaps, and generates AI-powered recommendations.

Competitors:
- AuthBridge
- IDfy
- Signzy
- HyperVerge
- Bureau
- DigiTap
## System Architecture:
Competitor Websites
        |
        v
    Scrapers
        |
        v
    SQLite DB
        |
        +----------------+
        |                |
        v                v
clustering.py        keywords.py
        |
        v
      ai.py
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
 HTML/PDF Report
 ## Database Schema
 ## ContentItem

| Field | Type |
|---------|---------|
| id | Integer |
| competitor_name | String |
| title | String |
| url | String |
| content_type | String |
| topic | String |
| published_date | Date |
| scraped_time | DateTime |
## AI pipeline
1. Scrape competitor content
2. Store in SQLite
3. Topic tagging using clustering.py
4. Calculate gap scores
5. Send summary to Claude
6. Generate recommendations
7. Save ai_insights.json
## GAP SCORE FORMULA
Gap Score =
(Number of competitors covering topic)
×
(Topic importance weight)
÷
(Current SEESEC coverage)