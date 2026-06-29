"""
Generate a professional HTML report from output/ai_insights.json.

Open in browser -> Print -> Save as PDF
Usage:
    python reports/generator.py
"""

import os
import sys
import json
import html
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from database.models import SessionLocal, ContentItem


INSIGHTS_PATH = "output/ai_insights.json"


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def truncate(text, limit):
    text = "" if text is None else str(text)
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def load_insights():
    if os.path.exists(INSIGHTS_PATH):
        with open(INSIGHTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"gaps": [], "insights": {}}


def fetch_report_data():
    db = SessionLocal()
    try:
        comp_counts = (
            db.query(ContentItem.competitor_name, func.count(ContentItem.id))
            .group_by(ContentItem.competitor_name)
            .order_by(func.count(ContentItem.id).desc())
            .all()
        )

        total = db.query(func.count(ContentItem.id)).scalar() or 0

        recent = (
            db.query(ContentItem)
            .order_by(ContentItem.scraped_time.desc())
            .limit(20)
            .all()
        )

        return comp_counts, total, recent
    finally:
        db.close()


def format_date(value):
    if value is None or value == "":
        return "—"

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    return esc(value)


def generate_report(output_path=None):
    comp_counts, total, recent = fetch_report_data()

    data = load_insights()
    gaps = data.get("gaps", []) or []
    insights = data.get("insights", {}) or {}

    summary = insights.get(
        "executive_summary",
        "Run python analysis/ai.py to generate insights."
    )
    recs = insights.get("content_recommendations", []) or []
    analyses = insights.get("gap_analyses", []) or []

    date_str = datetime.utcnow().strftime("%B %d, %Y")

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = f"output/reports/seesec_report_{timestamp}.html"

    def comp_rows():
        if not comp_counts:
            return (
                "<tr><td colspan='3' style='color:#999'>"
                "No competitor data available.</td></tr>"
            )

        rows = []
        for competitor, count in comp_counts:
            competitor = esc(competitor or "Unknown")
            count = int(count or 0)
            activity_bar = esc("█" * min(max(count // 20, 0), 30))

            rows.append(
                f"<tr>"
                f"<td>{competitor}</td>"
                f"<td style='font-weight:600'>{count}</td>"
                f"<td style='color:#6366f1'>{activity_bar}</td>"
                f"</tr>"
            )
        return "".join(rows)

    def gap_rows():
        if not gaps:
            return (
                "<tr><td colspan='4' style='color:#999'>"
                "Run python analysis/ai.py</td></tr>"
            )

        rows = []
        for g in gaps[:10]:
            topic = esc(g.get("topic", "Untitled"))
            article_count = esc(g.get("article_count", 0))
            num_competitors = esc(g.get("num_competitors", 0))
            gap_score = esc(g.get("gap_score", 0))

            rows.append(
                f"<tr>"
                f"<td><strong>{topic}</strong></td>"
                f"<td>{article_count}</td>"
                f"<td>{num_competitors}</td>"
                f"<td style='color:#6366f1;font-weight:600'>{gap_score}</td>"
                f"</tr>"
            )
        return "".join(rows)

    def rec_rows():
        if not recs:
            return (
                "<tr><td colspan='4' style='color:#999'>"
                "Run python analysis/ai.py</td></tr>"
            )

        rows = []
        for r in recs:
            title = esc(r.get("title", "Untitled"))
            content_type = esc(r.get("content_type", "Content"))
            target_keyword = esc(r.get("target_keyword", ""))
            why_now = esc(truncate(r.get("why_now", ""), 100))

            if why_now:
                why_now += "…"

            rows.append(
                f"<tr>"
                f"<td><strong>{title}</strong></td>"
                f"<td><span class='badge'>{content_type}</span></td>"
                f"<td style='color:#6366f1'>{target_keyword}</td>"
                f"<td style='color:#666;font-size:12px'>{why_now}</td>"
                f"</tr>"
            )
        return "".join(rows)

    def recent_rows():
        if not recent:
            return (
                "<tr><td colspan='4' style='color:#999'>"
                "No recent scraped articles available.</td></tr>"
            )

        rows = []
        for item in recent:
            competitor_name = esc(getattr(item, "competitor_name", None) or "Unknown")
            title_raw = getattr(item, "title", None) or "Untitled"
            title_short = esc(truncate(title_raw, 80))
            title_suffix = "…" if len(str(title_raw)) > 80 else ""
            url = esc(getattr(item, "url", None) or "#")
            content_type = esc(getattr(item, "content_type", None) or "Blog Post")
            published_date = format_date(getattr(item, "published_date", None))

            rows.append(
                f"<tr>"
                f"<td style='color:#6366f1;font-weight:600'>{competitor_name}</td>"
                f"<td><a href='{url}' target='_blank' rel='noopener noreferrer'>"
                f"{title_short}{title_suffix}</a></td>"
                f"<td>{content_type}</td>"
                f"<td style='color:#999'>{published_date}</td>"
                f"</tr>"
            )
        return "".join(rows)

    def gap_cards():
        if not analyses:
            return ""

        colors = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f59e0b",
            "MEDIUM": "#06b6d4",
        }

        cards = []
        for a in analyses[:6]:
            importance = str(a.get("strategic_importance", "") or "").upper()
            color = colors.get(importance, "#6366f1")
            topic = esc(a.get("topic", "Untitled"))
            opportunity = esc(a.get("seesec_opportunity", ""))
            audience = esc(a.get("target_audience", ""))
            importance_badge = esc(importance)

            titles = "".join(
                f"<li>{esc(title)}</li>"
                for title in a.get("seo_titles", []) or []
            )

            cards.append(
                f"""
                <div class="gap-card" style="border-left:4px solid {color}">
                  <div class="gap-title" style="color:{color}">
                    {topic}
                    <span class="importance-badge"
                          style="background:{color}22;color:{color};border:1px solid {color}44">
                      {importance_badge}
                    </span>
                  </div>
                  <p class="gap-opp">{opportunity}</p>
                  <div class="gap-audience">Target: {audience}</div>
                  <div class="seo-titles">
                    <strong>SEO Title Ideas:</strong>
                    <ul>{titles}</ul>
                  </div>
                </div>
                """
            )

        return "".join(cards)

    html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEESEC Competitive Intelligence Report — {esc(date_str)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1a1a2e;
    background: #f7f8fc;
    line-height: 1.5;
  }}

  .cover {{
    background: linear-gradient(135deg, #0e0e1f 0%, #1a1a3e 100%);
    color: white;
    padding: 56px 52px;
  }}

  .cover-label {{
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #a5b4fc;
    margin-bottom: 10px;
  }}

  .cover h1 {{
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.5px;
    line-height: 1.2;
  }}

  .cover h1 span {{
    color: #818cf8;
  }}

  .cover-sub {{
    color: #c7d2fe;
    font-size: 15px;
    margin: 10px 0 20px;
  }}

  .cover-meta {{
    color: #e0e7ff;
    font-size: 12px;
  }}

  .content {{
    padding: 36px 52px;
    max-width: 1100px;
    margin: 0 auto;
  }}

  .section {{
    margin-bottom: 36px;
  }}

  .section-title {{
    font-size: 16px;
    font-weight: 700;
    color: #1a1a2e;
    border-left: 4px solid #6366f1;
    padding-left: 12px;
    margin-bottom: 14px;
  }}

  .exec-box {{
    background: #f0f0ff;
    border: 1px solid #c8c8f0;
    border-radius: 8px;
    padding: 16px 20px;
    color: #2a2a4e;
    line-height: 1.75;
    font-size: 13.5px;
    white-space: pre-wrap;
  }}

  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
  }}

  .stat-card {{
    background: white;
    border: 1px solid #e0e0f0;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }}

  .stat-num {{
    font-size: 26px;
    font-weight: 800;
    color: #6366f1;
  }}

  .stat-lbl {{
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
    background: white;
    border: 1px solid #ececf8;
    border-radius: 10px;
    overflow: hidden;
  }}

  th {{
    background: #1a1a2e;
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
  }}

  td {{
    padding: 10px 12px;
    border-bottom: 1px solid #eeeef8;
    vertical-align: top;
  }}

  tr:nth-child(even) td {{
    background: #f5f5fb;
  }}

  a {{
    color: #6366f1;
    text-decoration: none;
  }}

  a:hover {{
    text-decoration: underline;
  }}

  .badge {{
    display: inline-block;
    background: #e0e7ff;
    color: #4338ca;
    border-radius: 20px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
  }}

  .gap-card {{
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border-left: 4px solid #6366f1;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  }}

  .gap-title {{
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }}

  .importance-badge {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    font-weight: 700;
    letter-spacing: 0.06em;
  }}

  .gap-opp {{
    color: #444;
    line-height: 1.6;
    margin-bottom: 8px;
    font-size: 13px;
  }}

  .gap-audience {{
    color: #777;
    font-size: 12px;
    margin-bottom: 8px;
  }}

  .seo-titles {{
    background: #f5f5fb;
    border-radius: 6px;
    padding: 10px 14px;
  }}

  .seo-titles ul {{
    margin-left: 18px;
    color: #6366f1;
    font-size: 12.5px;
  }}

  .seo-titles li {{
    margin-bottom: 4px;
  }}

  footer {{
    text-align: center;
    color: #aaa;
    font-size: 11px;
    margin-top: 40px;
    padding: 20px 0;
    border-top: 1px solid #e0e0f0;
  }}

  @media (max-width: 900px) {{
    .content,
    .cover {{
      padding: 24px;
    }}

    .stat-grid {{
      grid-template-columns: repeat(2, 1fr);
    }}
  }}

  @media (max-width: 600px) {{
    .stat-grid {{
      grid-template-columns: 1fr;
    }}

    body {{
      font-size: 12px;
    }}

    .cover h1 {{
      font-size: 28px;
    }}

    table {{
      font-size: 12px;
      display: block;
      overflow-x: auto;
      white-space: nowrap;
    }}
  }}

  @media print {{
    .cover {{
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    body {{
      background: white;
    }}

    .section,
    .gap-card,
    .stat-card,
    table {{
      break-inside: avoid;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}
  }}
</style>
</head>
<body>

<div class="cover">
  <div class="cover-label">Confidential — Internal Use Only</div>
  <h1>Competitive Intelligence<br><span>Report</span></h1>
  <div class="cover-sub">KYC &amp; Identity Verification — India Market</div>
  <div class="cover-meta">
    Generated: {esc(date_str)} &nbsp;·&nbsp;
    Articles Analyzed: {total} &nbsp;·&nbsp;
    SEESEC Intelligence Platform
  </div>
</div>

<div class="content">
  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-num">{total}</div>
      <div class="stat-lbl">Articles Tracked</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{len(comp_counts)}</div>
      <div class="stat-lbl">Competitors</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{len(gaps)}</div>
      <div class="stat-lbl">Content Gaps Found</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{len(recs)}</div>
      <div class="stat-lbl">AI Recommendations</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Executive Summary</div>
    <div class="exec-box">{esc(summary)}</div>
  </div>

  <div class="section">
    <div class="section-title">Competitor Content Volume</div>
    <table>
      <tr>
        <th>Competitor</th>
        <th>Articles</th>
        <th>Activity</th>
      </tr>
      {comp_rows()}
    </table>
  </div>

  <div class="section">
    <div class="section-title">Content Gap Scores</div>
    <p style="color:#666;font-size:12.5px;margin-bottom:12px">
      Higher gap score = more competitors covering it + high strategic importance + low current coverage
    </p>
    <table>
      <tr>
        <th>Topic</th>
        <th>Articles</th>
        <th>Competitors Covering</th>
        <th>Gap Score</th>
      </tr>
      {gap_rows()}
    </table>
  </div>

  <div class="section">
    <div class="section-title">AI Gap Analysis</div>
    {gap_cards() or '<p style="color:#999">Run python analysis/ai.py to generate analysis.</p>'}
  </div>

  <div class="section">
    <div class="section-title">Content Recommendations for SEESEC</div>
    <table>
      <tr>
        <th>Title</th>
        <th>Type</th>
        <th>Target Keyword</th>
        <th>Why Now</th>
      </tr>
      {rec_rows()}
    </table>
  </div>

  <div class="section">
    <div class="section-title">Recently Scraped Articles</div>
    <table>
      <tr>
        <th>Competitor</th>
        <th>Title</th>
        <th>Type</th>
        <th>Date</th>
      </tr>
      {recent_rows()}
    </table>
  </div>

  <footer>
    Generated by SEESEC Competitor Intelligence Platform &nbsp;·&nbsp; {esc(date_str)}<br>
    <span style="color:#bbb">Open in browser → File → Print → Save as PDF</span>
  </footer>
</div>

</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    abs_path = os.path.abspath(output_path)

    print("\n" + "=" * 60)
    print("REPORT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Saved To : {abs_path}")
    print("=" * 60 + "\n")

    return output_path


if __name__ == "__main__":
    generate_report()