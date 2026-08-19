import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import SessionLocal, Company, ContentItem
from datetime import datetime


def save_company_data(company_name, website, articles):
    """
    Save a company and its scraped articles into the database.
    """

    db = SessionLocal()

    try:

        # ==========================================
        # 1. CHECK IF COMPANY ALREADY EXISTS
        # ==========================================

        company = db.query(Company).filter(
            Company.name == company_name
        ).first()

        if company:

            print(
                f"\nCompany already exists: {company_name}"
            )

        else:

            # ==========================================
            # 2. CREATE NEW COMPANY
            # ==========================================

            company = Company(
                name=company_name,
                website=website,
                last_scraped=datetime.utcnow()
            )

            db.add(company)

            db.commit()

            db.refresh(company)

            print(
                f"\nCompany saved: {company_name}"
            )

        # ==========================================
        # 3. SAVE ARTICLES
        # ==========================================

        saved_count = 0
        skipped_count = 0

        for article in articles:

            # Check whether this URL already exists
            existing_article = db.query(ContentItem).filter(
                ContentItem.url == article["url"]
            ).first()

            if existing_article:

                print(
                    f"Skipping existing article: "
                    f"{article['title']}"
                )

                skipped_count += 1

                continue

            # ==========================================
            # 4. CREATE CONTENT ITEM
            # ==========================================

            content_item = ContentItem(

                competitor_name=company_name,

                content_type="Blog",

                title=article["title"],

                url=article["url"],

                published_date=article["date"],

                summary=article["content"]
            )

            db.add(content_item)

            saved_count += 1

        # ==========================================
        # 5. UPDATE LAST SCRAPED TIME
        # ==========================================

        company.last_scraped = datetime.utcnow()

        # ==========================================
        # 6. SAVE EVERYTHING
        # ==========================================

        db.commit()

        print("\n-----------------------------")
        print("DATABASE SAVE COMPLETE")
        print("-----------------------------")

        print(
            f"Company: {company_name}"
        )

        print(
            f"New articles saved: {saved_count}"
        )

        print(
            f"Existing articles skipped: {skipped_count}"
        )

        print(
            f"Total articles received: {len(articles)}"
        )

    except Exception as e:

        db.rollback()

        print(
            f"\nDatabase error: {e}"
        )

    finally:

        db.close()

if __name__ == "__main__":

    from scraper.generic import scrape_articles

    company_name = input(
        "Enter company name: "
    )

    website = input(
        "Enter company website: "
    )

    articles = scrape_articles(website)

    save_company_data(
        company_name,
        website,
        articles
    )