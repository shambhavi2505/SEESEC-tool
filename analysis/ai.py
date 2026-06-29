import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import json
from collections import defaultdict
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load .env from project root more reliably
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))

from database.models import SessionLocal, ContentItem, Opportunity  # noqa: E402


IMPORTANCE = {
    "AML": 1.5,
    "Fraud Detection": 1.5,
    "Risk & Compliance": 1.4,
    "KYC": 1.3,
    "KYB": 1.3,
    "Identity Verification": 1.2,
    "Banking & Lending": 1.2,
    "DPDP & Privacy": 1.2,
    "Video KYC": 1.1,
    "Digital Onboarding": 1.0,
    "Fintech & Payments": 1.0,
    "Cybersecurity": 1.0,
    "Background Verification": 0.9,
    "HR & Employment": 0.8,
    "Global & Cross-Border": 0.8,
}


EMPTY_INSIGHTS = {
    "executive_summary": "",
    "gap_analyses": [],
    "content_recommendations": [],
}


def load_data():
    db = SessionLocal()
    try:
        rows = db.query(
            ContentItem.competitor_name,
            ContentItem.topics,
            ContentItem.title
        ).all()
        return rows
    finally:
        db.close()


def build_maps(rows):
    topic_counts = defaultdict(int)
    topic_by_comp = defaultdict(set)
    comp_topic = defaultdict(lambda: defaultdict(int))
    comp_titles = defaultdict(list)

    for comp, topics, title in rows:
        comp = (comp or "Unknown").strip()
        title = (title or "").strip()

        if not topics:
            continue

        cleaned_topics = [x.strip() for x in topics.split(",") if x.strip()]
        if not cleaned_topics:
            continue

        for topic in cleaned_topics:
            topic_counts[topic] += 1
            topic_by_comp[topic].add(comp)
            comp_topic[comp][topic] += 1

        if title:
            comp_titles[comp].append(title)

    return topic_counts, topic_by_comp, comp_topic, comp_titles


def score_gaps(topic_counts, topic_by_comp):
    total = sum(topic_counts.values())
    gaps = []

    for topic, count in topic_counts.items():
        if topic == "Other":
            continue

        coverage_pct = (count / total * 100) if total > 0 else 0
        num_competitors = len(topic_by_comp[topic])
        importance = IMPORTANCE.get(topic, 1.0)
        gap_score = round((num_competitors * importance * 10) / max(coverage_pct, 0.5), 2)

        gaps.append({
            "topic": topic,
            "article_count": count,
            "coverage_pct": round(coverage_pct, 1),
            "num_competitors": num_competitors,
            "competitors": sorted(topic_by_comp[topic]),
            "gap_score": gap_score,
        })

    return sorted(gaps, key=lambda x: x["gap_score"], reverse=True)


def extract_text_from_message(message):
    parts = []
    for block in getattr(message, "content", []):
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()

def parse_json_response(raw):
    raw = raw.strip()

    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines:
            first = lines[0].strip().lower()
            if first.startswith("```json") or first == "```":
                if lines[-1].strip().startswith("```"):
                    raw = "\n".join(lines[1:-1]).strip()
                else:
                    raw = "\n".join(lines[1:]).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse issue: {e}. Attempting structural repair...")

        last_brace = raw.rfind("}")
        last_bracket = raw.rfind("]")
        cutoff = max(last_brace, last_bracket)

        if cutoff > 0:
            repaired = raw[:cutoff + 1]
            attempts = [repaired, repaired + "]}", repaired + "}"]
            for attempt in attempts:
                try:
                    return json.loads(attempt)
                except json.JSONDecodeError:
                    continue

    return EMPTY_INSIGHTS.copy()


def generate_ai_insights(gaps, comp_topic, comp_titles):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY in environment variables.")

    client = anthropic.Anthropic(api_key=api_key)

    comp_summary_lines = []
    for comp, topics in comp_topic.items():
        top4 = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:4]
        summary = ", ".join(f"{topic}({count})" for topic, count in top4)
        comp_summary_lines.append(f"  {comp}: {summary}")
    comp_summary = "\n".join(comp_summary_lines) if comp_summary_lines else "  No competitor topic summary available."

    gap_lines = "\n".join(
        f"  - {g['topic']}: {g['article_count']} articles, "
        f"{g['num_competitors']} competitors ({', '.join(g['competitors'])}), "
        f"gap score {g['gap_score']}"
        for g in gaps[:10]
    ) or "  No gap data available."

    sample_lines = []
    for g in gaps[:3]:
        for comp in g["competitors"][:1]:
            parts = g["topic"].split("&")
            kw = parts[0].strip().lower().split()[0] if parts and parts[0].strip() else ""
            if not kw:
                continue

            samples = [t for t in comp_titles.get(comp, []) if kw in t.lower()][:2]
            if samples:
                sample_lines.append(f"  [{comp} on {g['topic']}]: " + " | ".join(samples))

    sample_section = "\n".join(sample_lines) if sample_lines else "  No sample titles available."

    prompt = f"""You are a senior competitive intelligence analyst and content strategist. Today is June 2026.

COMPANY: SEESEC — B2B SaaS platform offering KYC automation, identity verification, fraud detection, and compliance tools. Based in India. Target customers: fintechs, NBFCs, banks, enterprises.

COMPETITOR CONTENT FOCUS (topic → article count):
{comp_summary}

CONTENT GAPS (topics competitors cover that SEESEC should target — ranked by opportunity score):
{gap_lines}

SAMPLE COMPETITOR TITLES FOR CONTEXT:
{sample_section}

YOUR TASK:
Generate a full competitive intelligence report as JSON with:
1. Top 5 gap analyses (one per topic) with strategic depth
2. 6 specific content recommendations for SEESEC
3. A 3-sentence executive summary

Rules:
- Keep every text field concise: 1-2 sentences max per field
- Titles must be specific, SEO-friendly, include 2025/2026 where relevant
- India-specific angles preferred (RBI, DPDP Act, PMLA, UIDAI, DigiLocker, NBFC)
- Be opinionated and specific
- estimated_impact must be "High", "Medium", or "Low"
- IMPORTANT: Keep the entire JSON response complete — do not truncate.

Respond ONLY with valid JSON, no markdown, no conversational explanation text:
{{
  "executive_summary": "3 sentences here",
  "gap_analyses": [
    {{
      "topic": "AML",
      "gap_score": 14.2,
      "strategic_importance": "CRITICAL",
      "why_competitors_underperform": "...",
      "seesec_opportunity": "...",
      "seo_titles": ["title 1", "title 2", "title 3"],
      "positioning_strategy": "...",
      "target_audience": "..."
    }}
  ],
  "content_recommendations": [
    {{
      "title": "...",
      "topic": "...",
      "content_type": "Blog Post",
      "target_keyword": "...",
      "why_now": "...",
      "estimated_impact": "High",
      "outline": ["section 1", "section 2"]
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    raw = extract_text_from_message(message)
    if not raw:
        return EMPTY_INSIGHTS.copy()

    return parse_json_response(raw)


def save_to_db(gaps, recommendations):
    db = SessionLocal()
    try:
        db.query(Opportunity).delete()

        for g in gaps[:10]:
            suggested = ""
            if recommendations:
                suggested = next(
                    (
                        r.get("title", "")
                        for r in recommendations
                        if isinstance(r, dict) and r.get("topic") == g["topic"]
                    ),
                    ""
                )

            db.add(
                Opportunity(
                    topics=g["topic"],
                    competitor_count=g["num_competitors"],
                    competitor_name_covering=", ".join(g["competitors"]),
                    suggested_title=suggested,
                    reason=(
                        f"Gap score {g['gap_score']} — "
                        f"{g['coverage_pct']}% coverage across {g['num_competitors']} competitors"
                    ),
                )
            )

        db.commit()
        print(f"Saved {min(len(gaps), 10)} opportunities to DB")

    except Exception as e:
        db.rollback()
        print(f"DB error: {e}")

    finally:
        db.close()


def print_results(gaps, insights):
    print("\n" + "=" * 65)
    print("SEESEC COMPETITIVE INTELLIGENCE REPORT")
    print("=" * 65)

    if insights and insights.get("executive_summary"):
        print("\nEXECUTIVE SUMMARY\n" + "-" * 60)
        print(insights["executive_summary"])
        print()

    print("CONTENT GAP SCORES\n" + "-" * 60)
    print(f"{'TOPIC':<26} {'ARTICLES':>8} {'COMPETITORS':>12} {'SCORE':>8}")
    print("-" * 60)
    for g in gaps[:12]:
        bar = "#" * min(int(g["gap_score"] / 2), 25)
        print("DEBUG:", repr(g["topic"]))
        print(
            f"{g['topic']:<26} {g['article_count']:>8} "
            f"{g['num_competitors']:>12} {g['gap_score']:>8.1f}  {bar}"
            )

    if insights and insights.get("gap_analyses"):
        print("\nAI GAP ANALYSIS\n" + "-" * 60)

        for a in insights["gap_analyses"]:
            imp_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "⚪",
            }.get(a.get("strategic_importance", "").upper(), "⚪")

            print(
                f"\n{imp_icon} {a.get('topic', '')} "
                f"(score: {a.get('gap_score', '')})"
            )
            print(f"   Opportunity: {a.get('seesec_opportunity', '')}")
            print(f"   Audience: {a.get('target_audience', '')}")
            print("   SEO Titles:")

            for title in a.get("seo_titles", []):
                print(f"   → {title}")

    if insights and insights.get("content_recommendations"):
        print("\nCONTENT RECOMMENDATIONS FOR SEESEC\n" + "-" * 60)

        for i, r in enumerate(insights["content_recommendations"], 1):
            impact = r.get("estimated_impact", "")
            icon = (
                "🔴" if impact == "High"
                else "🟡" if impact == "Medium"
                else "⚪"
            )

            print(f"\n{i}. {r.get('title', '')}")
            print(
                f"   {icon} {r.get('content_type', '')} | "
                f"Keyword: {r.get('target_keyword', '')}"
            )
            print(f"   Why now: {r.get('why_now', '')}")

            if r.get("outline"):
                print(f"   Outline: {' → '.join(r['outline'][:4])}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SEESEC AI Competitive Intelligence")
    parser.add_argument("--no-ai", action="store_true", help="Skip Claude API, show gap scores only")
    args = parser.parse_args()

    print("Loading articles from database...")
    rows = load_data()
    print(f"{len(rows)} articles loaded")

    topic_counts, topic_by_comp, comp_topic, comp_titles = build_maps(rows)
    gaps = score_gaps(topic_counts, topic_by_comp)

    insights = EMPTY_INSIGHTS.copy()

    if not args.no_ai:
        print("\nCalling Claude API...")
        try:
            insights = generate_ai_insights(gaps, comp_topic, comp_titles)
            print("AI insights generated")

            save_to_db(gaps, insights.get("content_recommendations", []))

            os.makedirs("output", exist_ok=True)
            with open("output/ai_insights.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "gaps": gaps[:15],
                        "insights": insights,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            print("Saved to output/ai_insights.json")

        except Exception as e:
            print(f"API or processing error: {e}")
            print("Showing statistical gap scores only due to processing exception.")
    else:
        print("\nSkipping AI (--no-ai flag set)")

    print_results(gaps, insights)