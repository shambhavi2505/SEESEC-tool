"""
SEESEC - Company Data Storage

Takes the output from the generic scraper and stores it
in the existing SQLite database.

This module is deliberately kept separate from scraping.
The scraper collects data.
This module stores data.
"""

from datetime import datetime, timezone

from database.models import (
    SessionLocal,
    Company,
    ContentItem,
)


def save_company_data(
    company_name: str,
    website: str,
    scrape_result: dict,
):
    """
    Save a complete company scraping result.

    Expected scrape_result:

    {
        "website": "...",
        "pages_discovered": 98,
        "pages_scanned": 20,
        "articles_found": 20,
        "articles": [...],
        "social_links": [...]
    }
    """

    db = SessionLocal()

    try:

        company_name = company_name.strip()
        website = website.strip()

        # --------------------------------------------------
        # 1. Find or create company
        # --------------------------------------------------

        company = (
            db.query(Company)
            .filter(
                Company.name == company_name
            )
            .first()
        )

        if not company:

            company = Company(
                name=company_name,
                website=website,
            )

            db.add(company)
            db.flush()

        else:

            company.website = website

        # --------------------------------------------------
        # 2. Update company metadata
        # --------------------------------------------------

        company.last_scraped = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

        if hasattr(company, "pages_discovered"):
            company.pages_discovered = scrape_result.get(
                "pages_discovered", 0
            )

        if hasattr(company, "pages_scanned"):
            company.pages_scanned = scrape_result.get(
                "pages_scanned", 0
            )

        if hasattr(company, "articles_found"):
            company.articles_found = scrape_result.get(
                "articles_found", 0
            )

        if hasattr(company, "scrape_status"):
            company.scrape_status = "completed"

        # --------------------------------------------------
        # 3. Save articles
        # --------------------------------------------------

        articles = scrape_result.get(
            "articles",
            []
        )

        saved_count = 0
        skipped_count = 0

        for article in articles:

            url = article.get("url")

            title = article.get("title")

            if not url or not title:
                skipped_count += 1
                continue

            # --------------------------------------------------
            # Check whether this URL already exists
            # --------------------------------------------------

            existing = (
                db.query(ContentItem)
                .filter(
                    ContentItem.url == url
                )
                .first()
            )

            if existing:

                # Update useful fields rather than
                # creating duplicate rows.

                existing.title = title

                existing.content_type = (
                    article.get("content_type")
                    or existing.content_type
                    or "Blog"
                )

                existing.published_date = (
                    article.get("published_date")
                    or existing.published_date
                )

                existing.summary = (
                    article.get("description")
                    or existing.summary
                )

                existing.competitor_name = (
                    company_name
                )

                skipped_count += 1

                continue

            # --------------------------------------------------
            # Create new article
            # --------------------------------------------------

            item = ContentItem(

                competitor_name=company_name,

                content_type=(
                    article.get("content_type")
                    or "Blog"
                ),

                title=title,

                url=url,

                published_date=(
                    article.get("published_date")
                ),

                summary=(
                    article.get("description")
                ),

                scraped_time=datetime.now(
                    timezone.utc
                ).replace(tzinfo=None),
            )

            db.add(item)

            saved_count += 1

        # --------------------------------------------------
        # 4. Commit everything
        # --------------------------------------------------

        db.commit()

        print()
        print("=" * 60)
        print("SEESEC DATABASE SAVE")
        print("=" * 60)

        print(
            f"Company: {company_name}"
        )

        print(
            f"New articles: {saved_count}"
        )

        print(
            f"Existing articles: {skipped_count}"
        )

        print("=" * 60)

        return {
            "success": True,
            "company": company_name,
            "new_articles": saved_count,
            "existing_articles": skipped_count,
            "total_articles": len(articles),
        }

    except Exception as e:

        db.rollback()

        print(
            f"[ERROR] Failed to save "
            f"{company_name}: {e}"
        )

        raise

    finally:

        db.close()