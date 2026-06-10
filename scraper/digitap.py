import requests
from bs4 import BeautifulSoup
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal

def scrape_DigiTap():
    print("Starting the DigiTap Scraper")
    session=SessionLocal()
    base_url= "https://blog.digitap.ai/page/{}/" 
    total_pages=10
    urls_to_scrape = ["https://blog.digitap.ai/"] + [base_url.format(i) for i in range(2, total_pages+1)]

    for page, url in enumerate(urls_to_scrape, 1):
        print(f"Scraping page {page}: {url}")
        response=requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        if response.status_code!=200:
            print("Failed to fetch the page!")
            break
        soup=BeautifulSoup(response.text, "html.parser")
        articles=soup.find_all("li", class_="wp-block-post")
        if not articles:
            print(f"No articles found on {page}, stopping")
            break
        for article in articles:
            try:
                title = article.find("h2", class_="wp-block-post-title").text.strip()
                url = article.find("h2", class_="wp-block-post-title").find("a")["href"]
                summary = article.find("div", class_="wp-block-post-excerpt")
                summary = summary.text.strip() if summary else ""
                article_response=requests.get(url,headers={"User-Agent":"Mozilla/5.0"})
                article_soup=BeautifulSoup(article_response.text, "html.parser")
                date_tag=article_soup.find("div", class_="wp-block-post-date")
                published_date=date_tag.text.strip() if date_tag else "Unknown"
                if not title or not url:
                    continue
                existing=session.query(ContentItem).filter_by(url=url).first()
                if existing:
                    continue
                item=ContentItem(
                    competitor_name="DigiTap",
                    content_type="blog",
                    title=title,
                    url=url,
                    published_date=published_date,
                    summary=summary
                )
                session.add(item)
                session.commit()
                print(f"Saved: {title}")
            except Exception as e:
                print(f"Error: {e}")
                session.rollback()
                continue

        time.sleep(2)

    session.close()
    print("DigiTap scraping complete")

if __name__ == "__main__":
    scrape_DigiTap()