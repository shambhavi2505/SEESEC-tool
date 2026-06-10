import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal

def scrape_digio():
    print("Starting Digio scraper")
    session = SessionLocal()
    url = "https://www.digio.in/blog/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print("Failed to fetch Digio Blog")
        return
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("div", attrs={"role": "link"})
    for article in articles:
        try:
            title_tag = article.find("p", class_=lambda c: c and "text-tertiary-40" in c)
            title = title_tag.text.strip() if title_tag else None
            url_tag = article.find("a", href=True)
            article_url = "https://www.digio.in" + url_tag["href"] if url_tag else None
            category_tag = article.find("small")
            category = category_tag.text.strip() if category_tag else "Unknown"
            summary_tag = article.find("p", class_=lambda c: c and "text-neutral-25" in c)
            summary = summary_tag.text.strip() if summary_tag else ""
            if not title or not article_url:
                continue
            existing = session.query(ContentItem).filter_by(url=article_url).first()
            if existing:
                continue
            item = ContentItem(
                competitor_name="Digio",
                content_type="blog",
                title=title,
                url=article_url,
                published_date="Unknown",
                topics=category,
                summary=summary
            )
            session.add(item)
            session.commit()
            print(f"Saved: {title}")
        except Exception as e:
            print(f"Error: {e}")
            session.rollback()
            continue

    session.close()
    print("Digio scraping complete")

if __name__ == "__main__":
    scrape_digio()