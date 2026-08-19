import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func

# ─── Project Setup ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from database.models import SessionLocal, ContentItem, Company
from analysis.keywords import (
    get_keyword_freq,
    get_bigram_freq,
    get_trigram_freq,
    get_publishing_frequency,
    get_competitor_keyword_freq,
    get_content_type_breakdown,
    load_titles,
)
from analysis.opportunities import (
    get_gaps,
    get_recommendations,
    get_gap_analyses,
    get_executive_summary,
    get_opportunities_from_db,
)
from scraper.search import find_website
from scraper.generic import scrape_articles
from scraper.save_company import save_company_data
from analysis.comp_ai import generate_competitor_summary


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="SEESEC Competitor Intelligence API",
    version="2.0.0",
)


# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Analysis Status ──────────────────────────────────────────────────────────

_scrape_status = {
    "running": False,
    "last_run": None,
    "message": "Not run yet",
    "stdout": "",
    "stderr": "",
    "returncode": None,
}


# Stores the status of individual company analyses
_company_status = {}


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "SEESEC Intelligence API v2",
    }


# ─── Content ──────────────────────────────────────────────────────────────────

@app.get("/api/content")
def get_content(
    competitor: str = None,
    content_type: str = None,
    topic: str = None,
    limit: int = 100,
    offset: int = 0,
):
    db = SessionLocal()

    try:
        q = db.query(ContentItem)

        if competitor:
            q = q.filter(
                ContentItem.competitor_name == competitor
            )

        if content_type:
            q = q.filter(
                ContentItem.content_type == content_type
            )

        if topic:
            q = q.filter(
                ContentItem.topics.contains(topic)
            )

        total = q.count()

        items = (
            q.order_by(ContentItem.scraped_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "items": [
                {
                    "id": i.id,
                    "competitor_name": i.competitor_name,
                    "content_type": i.content_type or "Blog Post",
                    "title": i.title,
                    "url": i.url,
                    "published_date": i.published_date,
                    "topics": i.topics,
                    "scraped_time": str(i.scraped_time),
                }
                for i in items
            ],
        }

    finally:
        db.close()


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()

    try:
        comp_counts = (
            db.query(
                ContentItem.competitor_name,
                func.count(ContentItem.id),
            )
            .group_by(ContentItem.competitor_name)
            .order_by(func.count(ContentItem.id).desc())
            .all()
        )

        total = (
            db.query(func.count(ContentItem.id))
            .scalar()
        )

        ctype_counts = (
            db.query(
                ContentItem.content_type,
                func.count(ContentItem.id),
            )
            .group_by(ContentItem.content_type)
            .all()
        )

        return {
            "total_articles": total,
            "competitor_counts": [
                {
                    "competitor": c,
                    "count": n,
                }
                for c, n in comp_counts
            ],
            "content_type_counts": [
                {
                    "type": t or "Blog Post",
                    "count": n,
                }
                for t, n in ctype_counts
            ],
            "publishing_frequency": get_publishing_frequency(),
            "content_type_breakdown": get_content_type_breakdown(),
        }

    finally:
        db.close()


# ─── Topics ───────────────────────────────────────────────────────────────────

@app.get("/api/topics")
def get_topics():
    rows = load_titles()

    keyword_freq = get_keyword_freq(rows)
    bigram_freq = get_bigram_freq(rows)
    trigram_freq = get_trigram_freq(rows)

    return {
        "top_keywords": [
            {
                "word": word,
                "count": count,
            }
            for word, count in list(keyword_freq.items())[:30]
        ],

        "top_bigrams": [
            {
                "bigram": bigram,
                "count": count,
            }
            for bigram, count in list(bigram_freq.items())[:20]
        ],

        "top_trigrams": [
            {
                "trigram": trigram,
                "count": count,
            }
            for trigram, count in list(trigram_freq.items())[:15]
        ],

        "competitor_keywords": {
            competitor: [
                {
                    "word": word,
                    "count": count,
                }
                for word, count in keywords
            ]
            for competitor, keywords
            in get_competitor_keyword_freq().items()
        },
    }


# ─── Opportunities ────────────────────────────────────────────────────────────

@app.get("/api/opportunities")
def get_opportunities_endpoint():

    gaps = get_gaps()
    gap_analyses = get_gap_analyses()

    gap_score_map = {
        gap["topic"]: gap["gap_score"]
        for gap in gaps
    }

    for analysis in gap_analyses:

        if not analysis.get("gap_score"):
            analysis["gap_score"] = gap_score_map.get(
                analysis.get("topic"),
                "—",
            )

    return {
        "executive_summary": get_executive_summary(),
        "gaps": gaps,
        "gap_analyses": gap_analyses,
        "recommendations": get_recommendations(),
        "db_opportunities": get_opportunities_from_db(),
    }


# ─── Existing Competitors ─────────────────────────────────────────────────────

@app.get("/api/competitors")
def get_competitors():

    db = SessionLocal()

    try:

        competitors = (
            db.query(ContentItem.competitor_name)
            .distinct()
            .all()
        )

        return {
            "competitors": [
                competitor[0]
                for competitor in competitors
                if competitor[0]
            ]
        }

    finally:
        db.close()


# ─── Phase 1: AI Analysis ─────────────────────────────────────────────────────

def run_analysis_job():

    _scrape_status["running"] = True
    _scrape_status["message"] = "Running AI analysis..."
    _scrape_status["stdout"] = ""
    _scrape_status["stderr"] = ""
    _scrape_status["returncode"] = None

    try:

        result = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "analysis" / "ai.py"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(BASE_DIR),
        )

        _scrape_status["stdout"] = result.stdout or ""
        _scrape_status["stderr"] = result.stderr or ""
        _scrape_status["returncode"] = result.returncode

        if result.returncode == 0:

            _scrape_status["message"] = (
                "Analysis complete!"
            )

        else:

            _scrape_status["message"] = (
                f"Analysis failed with code "
                f"{result.returncode}"
            )

            if result.stderr:
                print(
                    "AI analysis stderr:",
                    result.stderr,
                )

    except Exception as e:

        _scrape_status["stderr"] = str(e)

        _scrape_status["message"] = (
            f"Error: {str(e)}"
        )

    finally:

        _scrape_status["running"] = False

        _scrape_status["last_run"] = str(
            datetime.now(timezone.utc)
        )


@app.post("/api/analyze")
def trigger_analysis(
    background_tasks: BackgroundTasks,
):

    if _scrape_status["running"]:

        return {
            "status": "already_running",
            "message": "Analysis already running",
        }

    background_tasks.add_task(
        run_analysis_job
    )

    return {
        "status": "started",
        "message": (
            "AI analysis running in background"
        ),
    }


@app.get("/api/analyze/status")
def analysis_status():

    return _scrape_status


# ─── Phase 2: Company Search ──────────────────────────────────────────────────

@app.get("/api/search-company")
def search_company(q: str):

    """
    Search for a company by name or URL
    and return candidate websites.
    """

    q = q.strip()

    if not q:

        return {
            "type": "error",
            "message": "Please enter a company name or website.",
            "candidates": [],
        }

    # User entered a URL or domain
    if q.startswith("http") or (
        "." in q and " " not in q
    ):

        website = (
            q
            if q.startswith("http")
            else f"https://{q}"
        )

        return {
            "type": "url",
            "query": q,
            "candidates": [website],
        }

    # User entered a company name
    candidates = find_website(q)

    return {
        "type": "name",
        "query": q,
        "candidates": candidates or [],
    }


# ─── Start Company Analysis ───────────────────────────────────────────────────

@app.post("/api/analyze-company")
def analyze_company(
    background_tasks: BackgroundTasks,
    company_name: str,
    website: str,
):

    """
    Confirm the company website and start
    the scraping + AI analysis pipeline.
    """

    company_name = company_name.strip()
    website = website.strip()

    if not company_name:

        return {
            "status": "error",
            "message": "Company name is required.",
        }

    if not website:

        return {
            "status": "error",
            "message": "Website is required.",
        }

    # Prevent duplicate analysis
    if _company_status.get(
        company_name,
        {},
    ).get("running"):

        return {
            "status": "already_running",
            "message": (
                f"{company_name} analysis "
                f"is already running."
            ),
        }

    # Check database cache
    db = SessionLocal()

    try:

        existing = (
            db.query(Company)
            .filter(
                Company.name == company_name
            )
            .first()
        )

    finally:
        db.close()

    # Company already analysed
    if existing:

        return {
            "status": "cached",
            "message": (
                f"{company_name} has already been "
                f"analysed."
            ),
            "company": company_name,
        }

    # Set initial status
    _company_status[company_name] = {
        "running": True,
        "message": "Starting analysis...",
        "article_count": 0,
    }

    # Start background pipeline
    background_tasks.add_task(
        run_company_pipeline,
        company_name,
        website,
    )

    return {
        "status": "started",
        "message": (
            f"Analysing {company_name}..."
        ),
        "company": company_name,
    }


# ─── Company Analysis Status ──────────────────────────────────────────────────

@app.get("/api/analyze-company/status/{company_name}")
def company_analysis_status(
    company_name: str,
):

    """
    Check the current status of a company's analysis.
    """

    return _company_status.get(
        company_name,
        {
            "running": False,
            "message": "Not started",
            "article_count": 0,
        },
    )


# ─── Get Single Company ───────────────────────────────────────────────────────

@app.get("/api/company/{company_name}")
def get_company(
    company_name: str,
):

    """
    Get the complete analysis results
    for a company.
    """

    db = SessionLocal()

    try:

        company = (
            db.query(Company)
            .filter(
                Company.name == company_name
            )
            .first()
        )

        if not company:

            return {
                "error": (
                    "Company not found. "
                    "Run analysis first."
                )
            }

        articles = (
            db.query(ContentItem)
            .filter(
                ContentItem.competitor_name
                == company_name
            )
            .order_by(
                ContentItem.scraped_time.desc()
            )
            .all()
        )

        return {

            "company": company.name,

            "website": company.website,

            "ai_summary": company.ai_summary,

            "last_scraped": (
                str(company.last_scraped)
                if company.last_scraped
                else None
            ),

            "article_count": len(articles),

            "articles": [

                {
                    "title": article.title,
                    "url": article.url,
                    "content_type": (
                        article.content_type
                        or "Blog Post"
                    ),
                    "published_date": (
                        article.published_date
                    ),
                    "topics": article.topics,
                }

                for article in articles[:50]

            ],
        }

    finally:
        db.close()


# ─── Get All Analysed Companies ───────────────────────────────────────────────

@app.get("/api/companies")
def get_all_companies():

    """
    List all companies
    that have already been analysed.
    """

    db = SessionLocal()

    try:

        companies = (
            db.query(Company)
            .order_by(
                Company.last_scraped.desc()
            )
            .all()
        )

        return {

            "companies": [

                {
                    "name": company.name,

                    "website": company.website,

                    "last_scraped": (
                        str(company.last_scraped)
                        if company.last_scraped
                        else None
                    ),
                }

                for company in companies

            ]
        }

    finally:
        db.close()


# ─── Background Company Pipeline ──────────────────────────────────────────────

def run_company_pipeline(
    company_name: str,
    website: str,
):

    try:

        # ── Step 1: Scrape ───────────────────────────────────────────────

        _company_status[company_name] = {
            "running": True,
            "message": "Scraping articles...",
            "article_count": 0,
        }

        articles = scrape_articles(website)

        # Handle scraper returning None
        if articles is None:
            articles = []

        # ── Step 2: Check if articles were found ─────────────────────────

        if not articles:

            _company_status[company_name] = {
                "running": False,
                "message": (
                    "No articles found on this website."
                ),
                "article_count": 0,
            }

            return

        # ── Step 3: Save Articles ────────────────────────────────────────

        _company_status[company_name] = {
            "running": True,
            "message": (
                f"Saving {len(articles)} articles..."
            ),
            "article_count": len(articles),
        }

        save_company_data(
            company_name,
            website,
            articles,
        )

        # ── Step 4: Generate AI Summary ─────────────────────────────────

        _company_status[company_name] = {
            "running": True,
            "message": "Generating AI summary...",
            "article_count": len(articles),
        }

        summary = generate_competitor_summary(
            company_name,
            articles,
        )

        # ── Step 5: Save AI Summary ─────────────────────────────────────

        db = SessionLocal()

        try:

            company = (
                db.query(Company)
                .filter(
                    Company.name == company_name
                )
                .first()
            )

            if company:

                company.ai_summary = summary

                db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

        # ── Step 6: Complete ─────────────────────────────────────────────

        _company_status[company_name] = {
            "running": False,
            "message": "Analysis complete!",
            "article_count": len(articles),
        }

    except Exception as e:

        print(
            f"Company analysis error for "
            f"{company_name}: {str(e)}"
        )

        _company_status[company_name] = {
            "running": False,
            "message": (
                f"Error: {str(e)}"
            ),
            "article_count": 0,
        }


# ─── Run Server ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )