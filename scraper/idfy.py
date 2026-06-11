import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal

def scrape_idfy():
    print("Starting IDfy scraper...")
    session = SessionLocal()
    
    base_url = "https://idfyblogs.idfy.com/api/posts"
    params = {
        "limit": 12,
        "where[_status][equals]": "published",
        "sort": "-publishedAt"
    }
    
    total_pages = 35

    for page in range(1, total_pages + 1):
        print(f"Scraping page {page}...")
        params["page"] = page
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            articles = data.get("docs", [])
            
            for article in articles:
                try:
                    title = article.get("title")
                    slug = article.get("slug")
                    url = f"https://www.idfy.com/blog/{slug}/" if slug else None
                    summary = article.get("description", "")
                    published_date = article.get("publishedAt", "Unknown")
                    
                    if not title or not url:
                        continue
                    
                    existing = session.query(ContentItem).filter_by(url=url).first()
                    if existing:
                        continue
                    
                    item = ContentItem(
                        competitor_name="IDfy",
                        content_type="blog",
                        title=title,
                        url=url,
                        published_date=published_date,
                        topics="Unknown",
                        summary=summary
                    )
                    session.add(item)
                    session.commit()
                    print(f"Saved: {title}")
                    
                except Exception as e:
                    print(f"Error saving article: {e}")
                    session.rollback()
                    
        except Exception as e:
            print(f"Error on page {page}: {e}")
            continue

    session.close()
    print("IDfy scraping complete.")

if __name__ == "__main__":
    scrape_idfy()