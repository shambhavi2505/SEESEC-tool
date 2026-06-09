import requests
from bs4 import BeautifulSoup
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal

def scrape_signzy():
    print("Starting Signzy scraper...")
    session = SessionLocal()
    base_url = "https://www.signzy.com/category-blog?page={}"
    total_pages = 20

    for page in range(1, total_pages + 1):
        url = base_url.format(page)
        print(f"Scraping page {page}: {url}")

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to fetch page {page}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("a", class_="product_ProductCard__sfRxu")

        if not articles:
            print(f"No articles found on page {page}, stopping.")
            break

        for article in articles:
            try:
                title = article.find("h2", class_="product_ProductDescription__kzy99").text.strip()
                url = "https://www.signzy.com" + article.get("href", "")
                category = article.find("p", class_="product_ProductTitle__tzGQG").text.strip()

                date_tag = article.find("div", class_="product_ProductMeta__Ey93T")
                published_date = date_tag.text.strip() if date_tag else "Unknown"

                if not title or not url:
                    continue

                existing = session.query(ContentItem).filter_by(url=url).first()
                if existing:
                    continue

                item = ContentItem(
                    competitor_name="Signzy",
                    content_type="blog",
                    title=title,
                    url=url,
                    published_date=published_date,
                    topics=category
                )
                session.add(item)
                session.commit()
                print(f"Saved: {title}")

            except Exception as e:
                print(f"Error scraping article: {e}")
                session.rollback()
                continue

        time.sleep(2)

    session.close()
    print("Signzy scraping complete.")

if __name__ == "__main__":
    scrape_signzy()