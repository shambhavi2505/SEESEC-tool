import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func


# =============================================================================
# PROJECT SETUP
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# =============================================================================
# DATABASE
# =============================================================================

from database.models import (
    SessionLocal,
    ContentItem,
    Company,
)


# =============================================================================
# ANALYSIS
# =============================================================================

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

from analysis.comp_ai import (
    generate_competitor_summary,
)


# =============================================================================
# SCRAPER
# =============================================================================

from scraper.search import find_website
from scraper.generic import scrape_articles
from scraper.save_company import save_company_data


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="SEESEC Competitor Intelligence API",
    description=(
        "Real-time competitor content intelligence platform "
        "for discovering, scraping, analyzing and comparing competitors."
    ),
    version="3.0.0",
)


# =============================================================================
# CORS
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# GLOBAL ANALYSIS STATUS
# =============================================================================

_scrape_status = {
    "running": False,
    "last_run": None,
    "message": "Not run yet",
    "stdout": "",
    "stderr": "",
    "returncode": None,
}


# =============================================================================
# INDIVIDUAL COMPANY STATUS
# =============================================================================

_company_status = {}


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "SEESEC Intelligence API",
        "version": "3.0.0",
    }


# =============================================================================
# CONTENT
# =============================================================================

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
            q.order_by(
                ContentItem.scraped_time.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [
                {
                    "id": item.id,
                    "competitor_name": item.competitor_name,
                    "content_type": (
                        item.content_type
                        or "Blog Post"
                    ),
                    "title": item.title,
                    "url": item.url,
                    "published_date": item.published_date,
                    "topics": item.topics,
                    "keywords": item.keywords,
                    "summary": item.summary,
                    "scraped_time": (
                        str(item.scraped_time)
                        if item.scraped_time
                        else None
                    ),
                }
                for item in items
            ],
        }

    finally:
        db.close()


# =============================================================================
# STATISTICS
# =============================================================================

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()

    try:
        competitor_counts = (
            db.query(
                ContentItem.competitor_name,
                func.count(ContentItem.id),
            )
            .group_by(
                ContentItem.competitor_name
            )
            .order_by(
                func.count(ContentItem.id).desc()
            )
            .all()
        )

        total_articles = (
            db.query(
                func.count(ContentItem.id)
            )
            .scalar()
        )

        content_type_counts = (
            db.query(
                ContentItem.content_type,
                func.count(ContentItem.id),
            )
            .group_by(
                ContentItem.content_type
            )
            .all()
        )

        return {
            "total_articles": total_articles,

            "competitor_counts": [
                {
                    "competitor": competitor,
                    "count": count,
                }
                for competitor, count
                in competitor_counts
            ],

            "content_type_counts": [
                {
                    "type": content_type or "Blog Post",
                    "count": count,
                }
                for content_type, count
                in content_type_counts
            ],

            "publishing_frequency": (
                get_publishing_frequency()
            ),

            "content_type_breakdown": (
                get_content_type_breakdown()
            ),
        }

    finally:
        db.close()


# =============================================================================
# TOPICS
# =============================================================================

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
            for word, count
            in list(keyword_freq.items())[:30]
        ],

        "top_bigrams": [
            {
                "bigram": bigram,
                "count": count,
            }
            for bigram, count
            in list(bigram_freq.items())[:20]
        ],

        "top_trigrams": [
            {
                "trigram": trigram,
                "count": count,
            }
            for trigram, count
            in list(trigram_freq.items())[:15]
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


# =============================================================================
# OPPORTUNITIES
# =============================================================================

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

            analysis["gap_score"] = (
                gap_score_map.get(
                    analysis.get("topic"),
                    "—",
                )
            )

    return {

        "executive_summary": (
            get_executive_summary()
        ),

        "gaps": gaps,

        "gap_analyses": gap_analyses,

        "recommendations": (
            get_recommendations()
        ),

        "db_opportunities": (
            get_opportunities_from_db()
        ),
    }


# =============================================================================
# EXISTING COMPETITORS
# =============================================================================

@app.get("/api/competitors")
def get_competitors():

    db = SessionLocal()

    try:

        competitors = (
            db.query(
                ContentItem.competitor_name
            )
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


# =============================================================================
# GLOBAL AI ANALYSIS
# =============================================================================

def run_analysis_job():

    _scrape_status["running"] = True
    _scrape_status["message"] = (
        "Running AI analysis..."
    )
    _scrape_status["stdout"] = ""
    _scrape_status["stderr"] = ""
    _scrape_status["returncode"] = None

    try:

        result = subprocess.run(
            [
                sys.executable,
                str(
                    BASE_DIR
                    / "analysis"
                    / "ai.py"
                ),
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            cwd=str(BASE_DIR),
        )

        _scrape_status["stdout"] = (
            result.stdout or ""
        )

        _scrape_status["stderr"] = (
            result.stderr or ""
        )

        _scrape_status["returncode"] = (
            result.returncode
        )

        if result.returncode == 0:

            _scrape_status["message"] = (
                "Analysis complete!"
            )

        else:

            _scrape_status["message"] = (
                f"Analysis failed with code "
                f"{result.returncode}"
            )

    except Exception as e:

        _scrape_status["stderr"] = str(e)

        _scrape_status["message"] = (
            f"Error: {str(e)}"
        )

    finally:

        _scrape_status["running"] = False

        _scrape_status["last_run"] = (
            str(datetime.now(timezone.utc))
        )


@app.post("/api/analyze")
def trigger_analysis(
    background_tasks: BackgroundTasks,
):

    if _scrape_status["running"]:

        return {
            "status": "already_running",
            "message": (
                "Analysis already running"
            ),
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


# =============================================================================
# COMPANY SEARCH
# =============================================================================

@app.get("/api/search-company")
def search_company(q: str):

    """
    Search for a company by name or URL.
    """

    q = q.strip()

    if not q:

        return {
            "type": "error",
            "message": (
                "Please enter a company name "
                "or website."
            ),
            "candidates": [],
        }

    # --------------------------------------------------
    # User entered a URL/domain
    # --------------------------------------------------

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

    # --------------------------------------------------
    # User entered company name
    # --------------------------------------------------

    candidates = find_website(q)

    return {
        "type": "name",
        "query": q,
        "candidates": candidates or [],
    }


# =============================================================================
# START COMPANY ANALYSIS
# =============================================================================

@app.post("/api/analyze-company")
def analyze_company(
    background_tasks: BackgroundTasks,
    company_name: str,
    website: str,
):

    """
    Start real-time company intelligence pipeline.

    Pipeline:

    Company
        ↓
    Website
        ↓
    Scraping
        ↓
    Content extraction
        ↓
    Database
        ↓
    AI analysis
        ↓
    Intelligence result
    """

    company_name = company_name.strip()
    website = website.strip()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    if not company_name:

        return {
            "status": "error",
            "message": (
                "Company name is required."
            ),
        }

    if not website:

        return {
            "status": "error",
            "message": (
                "Website is required."
            ),
        }

    # --------------------------------------------------
    # Prevent duplicate running analysis
    # --------------------------------------------------

    current_status = (
        _company_status.get(
            company_name,
            {},
        )
    )

    if current_status.get("running"):

        return {
            "status": "already_running",
            "message": (
                f"{company_name} analysis "
                "is already running."
            ),
        }

    # --------------------------------------------------
    # Check database
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Existing company
    #
    # IMPORTANT:
    # We currently return cached data.
    # Later we will add a "refresh" option.
    # --------------------------------------------------

    if existing:

        return {
            "status": "cached",
            "message": (
                f"{company_name} has already "
                "been analysed."
            ),
            "company": company_name,
        }

    # --------------------------------------------------
    # Initialize status
    # --------------------------------------------------

    _company_status[company_name] = {

        "running": True,

        "stage": "starting",

        "message": (
            "Starting company analysis..."
        ),

        "progress": 0,

        "article_count": 0,

        "pages_discovered": 0,

        "pages_scanned": 0,

        "articles_found": 0,

        "error": None,

        "started_at": (
            str(datetime.now(timezone.utc))
        ),

        "completed_at": None,
    }

    # --------------------------------------------------
    # Start background pipeline
    # --------------------------------------------------

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


# =============================================================================
# COMPANY ANALYSIS STATUS
# =============================================================================

@app.get(
    "/api/analyze-company/status/{company_name}"
)
def company_analysis_status(
    company_name: str,
):

    """
    Return live status of a company analysis.
    """

    status = _company_status.get(
        company_name
    )

    if status:

        return status

    return {

        "running": False,

        "stage": "not_started",

        "message": "Not started",

        "progress": 0,

        "article_count": 0,

        "pages_discovered": 0,

        "pages_scanned": 0,

        "articles_found": 0,

        "error": None,
    }


# =============================================================================
# GET SINGLE COMPANY
# =============================================================================

@app.get("/api/company/{company_name}")
def get_company(
    company_name: str,
):

    """
    Get complete analysis results for a company.
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

            "description": (
                getattr(
                    company,
                    "description",
                    None,
                )
            ),

            "industry": (
                getattr(
                    company,
                    "industry",
                    None,
                )
            ),

            "ai_summary": (
                company.ai_summary
            ),

            "scrape_status": (
                getattr(
                    company,
                    "scrape_status",
                    None,
                )
            ),

            "pages_discovered": (
                getattr(
                    company,
                    "pages_discovered",
                    0,
                )
            ),

            "pages_scanned": (
                getattr(
                    company,
                    "pages_scanned",
                    0,
                )
            ),

            "articles_found": (
                getattr(
                    company,
                    "articles_found",
                    len(articles),
                )
            ),

            "last_scraped": (
                str(company.last_scraped)
                if company.last_scraped
                else None
            ),

            "article_count": len(articles),

            "articles": [

                {
                    "id": article.id,

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

                    "keywords": article.keywords,

                    "summary": article.summary,
                }

                for article in articles[:100]
            ],
        }

    finally:

        db.close()


# =============================================================================
# ALL ANALYSED COMPANIES
# =============================================================================

@app.get("/api/companies")
def get_all_companies():

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

                    "description": (
                        getattr(
                            company,
                            "description",
                            None,
                        )
                    ),

                    "industry": (
                        getattr(
                            company,
                            "industry",
                            None,
                        )
                    ),

                    "scrape_status": (
                        getattr(
                            company,
                            "scrape_status",
                            None,
                        )
                    ),

                    "articles_found": (
                        getattr(
                            company,
                            "articles_found",
                            0,
                        )
                    ),

                    "last_scraped": (
                        str(
                            company.last_scraped
                        )
                        if company.last_scraped
                        else None
                    ),
                }

                for company in companies
            ]
        }

    finally:

        db.close()


# =============================================================================
# BACKGROUND COMPANY PIPELINE
# =============================================================================

def run_company_pipeline(
    company_name: str,
    website: str,
):

    try:

        # ==============================================================
        # STEP 1 — SCRAPE WEBSITE
        # ==============================================================

        _company_status[company_name].update({

            "stage": "scraping",

            "message": (
                "Discovering website pages..."
            ),

            "progress": 10,
        })

        scrape_result = scrape_articles(
            website
        )

        # --------------------------------------------------------------
        # Normalize scraper output
        #
        # Expected:
        #
        # {
        #     "articles": [...],
        #     "pages_discovered": 98,
        #     "pages_scanned": 20,
        #     ...
        # }
        #
        # --------------------------------------------------------------

        if scrape_result is None:

            scrape_result = {}

        # --------------------------------------------------------------
        # Backwards compatibility:
        #
        # If scraper still returns a plain list,
        # accept it.
        # --------------------------------------------------------------

        if isinstance(
            scrape_result,
            list,
        ):

            articles = scrape_result

            scrape_result = {
                "articles": articles
            }

        else:

            articles = (
                scrape_result.get(
                    "articles",
                    [],
                )
            )

        if articles is None:

            articles = []

        # --------------------------------------------------------------
        # Extract scraper statistics
        # --------------------------------------------------------------

        pages_discovered = (
            scrape_result.get(
                "pages_discovered",
                0,
            )
        )

        pages_scanned = (
            scrape_result.get(
                "pages_scanned",
                0,
            )
        )

        articles_found = len(articles)

        # --------------------------------------------------------------
        # Update live status
        # --------------------------------------------------------------

        _company_status[company_name].update({

            "stage": "scraping_complete",

            "message": (
                f"Scraping complete. "
                f"Found {articles_found} resources."
            ),

            "progress": 45,

            "pages_discovered": (
                pages_discovered
            ),

            "pages_scanned": (
                pages_scanned
            ),

            "articles_found": (
                articles_found
            ),

            "article_count": (
                articles_found
            ),
        })

        # ==============================================================
        # STEP 2 — CHECK RESULTS
        # ==============================================================

        if not articles:

            _company_status[company_name].update({

                "running": False,

                "stage": "completed",

                "message": (
                    "No articles/resources "
                    "were found on this website."
                ),

                "progress": 100,

                "completed_at": (
                    str(
                        datetime.now(
                            timezone.utc
                        )
                    )
                ),
            })

            return

        # ==============================================================
        # STEP 3 — SAVE DATA
        # ==============================================================

        _company_status[company_name].update({

            "stage": "saving",

            "message": (
                f"Saving {len(articles)} "
                "resources to database..."
            ),

            "progress": 55,
        })

        save_company_data(
            company_name,
            website,
            articles,
        )

        # ==============================================================
        # STEP 4 — AI ANALYSIS
        # ==============================================================

        _company_status[company_name].update({

            "stage": "ai_analysis",

            "message": (
                "Generating competitor intelligence..."
            ),

            "progress": 70,
        })

        summary = generate_competitor_summary(
            company_name,
            articles,
        )

        # ==============================================================
        # STEP 5 — SAVE AI RESULTS
        # ==============================================================

        _company_status[company_name].update({

            "stage": "finalizing",

            "message": (
                "Saving intelligence results..."
            ),

            "progress": 90,
        })

        db = SessionLocal()

        try:

            company = (
                db.query(Company)
                .filter(
                    Company.name
                    == company_name
                )
                .first()
            )

            if company:

                company.ai_summary = summary

                # ------------------------------------------------------
                # Save scraper statistics if the columns exist
                # ------------------------------------------------------

                if hasattr(
                    company,
                    "pages_discovered",
                ):

                    company.pages_discovered = (
                        pages_discovered
                    )

                if hasattr(
                    company,
                    "pages_scanned",
                ):

                    company.pages_scanned = (
                        pages_scanned
                    )

                if hasattr(
                    company,
                    "articles_found",
                ):

                    company.articles_found = (
                        articles_found
                    )

                if hasattr(
                    company,
                    "scrape_status",
                ):

                    company.scrape_status = (
                        "completed"
                    )

                if hasattr(
                    company,
                    "updated_at",
                ):

                    company.updated_at = (
                        datetime.utcnow()
                    )

                db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

        # ==============================================================
        # STEP 6 — COMPLETE
        # ==============================================================

        _company_status[company_name].update({

            "running": False,

            "stage": "completed",

            "message": (
                "Company intelligence analysis complete!"
            ),

            "progress": 100,

            "article_count": (
                len(articles)
            ),

            "pages_discovered": (
                pages_discovered
            ),

            "pages_scanned": (
                pages_scanned
            ),

            "articles_found": (
                articles_found
            ),

            "completed_at": (
                str(
                    datetime.now(
                        timezone.utc
                    )
                )
            ),
        })

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    except Exception as e:

        error_message = str(e)

        print(
            f"\nCompany analysis error "
            f"for {company_name}: "
            f"{error_message}\n"
        )

        _company_status[company_name].update({

            "running": False,

            "stage": "failed",

            "message": (
                "Company analysis failed."
            ),

            "progress": 0,

            "error": error_message,

            "completed_at": (
                str(
                    datetime.now(
                        timezone.utc
                    )
                )
            ),
        })


# =============================================================================
# SERVER
# =============================================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )