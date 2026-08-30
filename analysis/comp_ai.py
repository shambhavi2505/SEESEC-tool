import os
import json
from collections import Counter

from dotenv import load_dotenv
from groq import Groq

from analysis.topics import tag_topics, TOPIC_KEYWORDS

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# SEESEC's own product focus. Used as the baseline domain we compare
# competitor topic coverage against.
SEESEC_DESCRIPTION = (
    "SEESEC is a B2B SaaS platform offering KYC automation, identity "
    "verification, fraud detection, KYB and compliance tooling for "
    "fintechs, NBFCs and banks."
)


def compute_topic_distribution(articles):
    """
    Count how many of this competitor's articles fall into each
    SEESEC-domain topic. Articles may already have topics tagged
    (from save_company_data); if not, tag them on the fly here.
    """

    counter = Counter()

    for article in articles:

        topics_field = article.get("topics")

        if not topics_field:
            topics_field = tag_topics(
                article.get("title", ""),
                article.get("description", ""),
            )

        for topic in [t.strip() for t in topics_field.split(",") if t.strip()]:
            if topic != "Other":
                counter[topic] += 1

    return counter


def generate_competitor_summary(company_name, articles, company_description=None):

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    titles = "\n".join([f"- {a['title']}" for a in articles[:50]])

    topic_counts = compute_topic_distribution(articles)

    all_domain_topics = list(TOPIC_KEYWORDS.keys())

    covered_topics = sorted(
        topic_counts.keys(),
        key=lambda t: -topic_counts[t],
    )

    uncovered_or_light_topics = [
        t for t in all_domain_topics
        if topic_counts.get(t, 0) <= 1
    ]

    coverage_lines = "\n".join(
        f"  - {t}: {topic_counts[t]} articles"
        for t in covered_topics
    ) or "  No topic data available."

    light_coverage_line = (
        ", ".join(uncovered_or_light_topics)
        if uncovered_or_light_topics
        else "None - competitor covers all domain topics"
    )

    prompt = f"""You are a competitive intelligence analyst.

{SEESEC_DESCRIPTION}

Company being analysed: {company_name}
Company's own homepage description (may be empty): {company_description or "Not available"}

Their recent content titles:
{titles}

Their topic coverage, computed from actual scraped articles (topic: article count):
{coverage_lines}

Domain topics {company_name} covers rarely or not at all (0-1 articles):
{light_coverage_line}

Answer these things in JSON format. IMPORTANT: only state facts you can
actually infer from the description and titles above. If something isn't
mentioned anywhere in that content, say so explicitly rather than guessing
or inventing details.

1. marketing_strategy: What is their content strategy in 2-3 sentences?
2. top_topics: List their top 5 content topics (use the computed topic coverage above)
3. products_services: List up to 5 products/services you can actually identify
   from the description and titles above. If none are identifiable, return
   exactly ["Not identifiable from publicly scraped content"].
4. leadership: List any named leadership/founders you can actually identify
   from the description and titles above. If none are mentioned, return
   exactly ["Not publicly disclosed in scraped content"].
5. content_gap_analysis: For each of the top 3 topics where {company_name} is
   strong OR clearly under-covering relative to their overall content volume,
   give an object with:
     - topic
     - competitor_article_count (use the numbers given above)
     - assessment: ONE sentence (max 25 words) on why this gap matters for SEESEC
     - seesec_action: 1 specific, concrete action SEESEC should take (max 20 words)
     - priority: "High", "Medium", or "Low"
6. seesec_recommendations: 3 specific actions SEESEC should take to compete overall

Respond ONLY with valid JSON, no explanation, in this shape:
{{
  "marketing_strategy": "...",
  "top_topics": ["...", "..."],
  "products_services": ["...", "..."],
  "leadership": ["...", "..."],
  "content_gap_analysis": [
    {{
      "topic": "...",
      "competitor_article_count": 0,
      "assessment": "...",
      "seesec_action": "...",
      "priority": "High"
    }}
  ],
  "seesec_recommendations": ["...", "...", "..."]
}}"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.3
    )

    content = response.choices[0].message.content

    # Defensive check: if Groq returns an empty or clearly-non-JSON
    # response, surface that clearly instead of silently saving junk.
    if not content or not content.strip():
        raise RuntimeError(
            "Groq API returned an empty response. "
            "Check your GROQ_API_KEY and account quota/rate limits."
        )

    return content