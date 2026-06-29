import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from database.models import SessionLocal, ContentItem
from analysis.keywords import (
    get_keyword_freq, get_bigram_freq, get_trigram_freq,
    get_publishing_frequency, get_competitor_keyword_freq,
    get_content_type_breakdown, load_titles
)
from analysis.opportunities import (
    get_gaps, get_recommendations, get_gap_analyses,
    get_executive_summary, get_opportunities_from_db
)

app = FastAPI(title="SEESEC Competitor Intelligence API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_scrape_status = {
    "running": False,
    "last_run": None,
    "message": "Not run yet",
    "stdout": "",
    "stderr": "",
    "returncode": None,
}


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "SEESEC Intelligence API v2"}


# ─── Content ──────────────────────────────────────────────────────────────────

@app.get("/api/content")
def get_content(competitor: str = None, content_type: str = None,
                topic: str = None, limit: int = 100, offset: int = 0):
    db = SessionLocal()
    try:
        q = db.query(ContentItem)
        if competitor:
            q = q.filter(ContentItem.competitor_name == competitor)
        if content_type:
            q = q.filter(ContentItem.content_type == content_type)
        if topic:
            q = q.filter(ContentItem.topics.contains(topic))

        total = q.count()
        items = q.order_by(ContentItem.scraped_time.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "items": [{
                "id":              i.id,
                "competitor_name": i.competitor_name,
                "content_type":    i.content_type or "Blog Post",
                "title":           i.title,
                "url":             i.url,
                "published_date":  i.published_date,
                "topics":          i.topics,
                "scraped_time":    str(i.scraped_time),
            } for i in items]
        }
    finally:
        db.close()


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        comp_counts = (
            db.query(ContentItem.competitor_name, func.count(ContentItem.id))
            .group_by(ContentItem.competitor_name)
            .order_by(func.count(ContentItem.id).desc())
            .all()
        )
        total = db.query(func.count(ContentItem.id)).scalar()
        ctype_counts = (
            db.query(ContentItem.content_type, func.count(ContentItem.id))
            .group_by(ContentItem.content_type)
            .all()
        )

        return {
            "total_articles":      total,
            "competitor_counts":   [{"competitor": c, "count": n} for c, n in comp_counts],
            "content_type_counts": [{"type": t or "Blog Post", "count": n} for t, n in ctype_counts],
            "publishing_frequency":    get_publishing_frequency(),
            "content_type_breakdown":  get_content_type_breakdown(),
        }
    finally:
        db.close()


# ─── Topics ───────────────────────────────────────────────────────────────────

@app.get("/api/topics")
def get_topics():
    rows = load_titles()
    return {
        "top_keywords":  [{"word": w, "count": c} for w, c in list(get_keyword_freq(rows).items())[:30]],
        "top_bigrams":   [{"bigram": b, "count": c} for b, c in list(get_bigram_freq(rows).items())[:20]],
        "top_trigrams":  [{"trigram": t, "count": c} for t, c in list(get_trigram_freq(rows).items())[:15]],
        "competitor_keywords": {
            comp: [{"word": w, "count": c} for w, c in kws]
            for comp, kws in get_competitor_keyword_freq().items()
        },
    }


# ─── Opportunities ────────────────────────────────────────────────────────────

@app.get("/api/opportunities")
def get_opportunities_endpoint():
    return {
        "executive_summary": get_executive_summary(),
        "gaps":              get_gaps(),
        "gap_analyses":      get_gap_analyses(),
        "recommendations":   get_recommendations(),
        "db_opportunities":  get_opportunities_from_db(),
    }


# ─── Competitors ──────────────────────────────────────────────────────────────

@app.get("/api/competitors")
def get_competitors():
    db = SessionLocal()
    try:
        comps = db.query(ContentItem.competitor_name).distinct().all()
        return {"competitors": [c[0] for c in comps]}
    finally:
        db.close()


# ─── AI Analysis ──────────────────────────────────────────────────────────────

def run_analysis_job():
    _scrape_status["running"]    = True
    _scrape_status["message"]    = "Running AI analysis..."
    _scrape_status["stdout"]     = ""
    _scrape_status["stderr"]     = ""
    _scrape_status["returncode"] = None

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "analysis" / "ai.py")],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=str(BASE_DIR)
)

        _scrape_status["stdout"]     = result.stdout or ""
        _scrape_status["stderr"]     = result.stderr or ""
        _scrape_status["returncode"] = result.returncode

        if result.returncode == 0:
            _scrape_status["message"] = "✅ Analysis complete!"
        else:
            _scrape_status["message"] = f"❌ Analysis failed with code {result.returncode}"
            # Print stderr to server console for debugging
            if result.stderr:
                print("AI analysis stderr:", result.stderr)

    except Exception as e:
        _scrape_status["stderr"]  = str(e)
        _scrape_status["message"] = f"❌ Error: {e}"

    finally:
        _scrape_status["running"]  = False
        _scrape_status["last_run"] = str(datetime.utcnow())


@app.post("/api/analyze")
def trigger_analysis(background_tasks: BackgroundTasks):
    if _scrape_status["running"]:
        return {"status": "already_running", "message": "Analysis already running"}
    background_tasks.add_task(run_analysis_job)
    return {"status": "started", "message": "AI analysis running in background"}


@app.get("/api/analyze/status")
def analysis_status():
    return _scrape_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)