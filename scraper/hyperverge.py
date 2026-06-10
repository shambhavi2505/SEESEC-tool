import requests
from bs4 import BeautifulSoup
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal
def scrape_HyperVerge():
    print("Starting the HyperVerge Scraper")
    session=SessionLocal()
    base_url= "https://hyperverge.co/blog/page/{}/" 
    total_pages=45

    for page in range (1, total_pages+1):
        url=base_url.format(page)
        print(f"Scraping page {page}: {url}")
        response=requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        if response.status_code!=200:
            print("Failed to fetch the page!")
            break
        soup=BeautifulSoup(response.text, "html.parser")
        articles=soup.find_all("div", class_="post-item")
        if not articles:
            print(f"No articles found on {page}, stopping")
            break
        for article in articles:
            try:
                title = article.find("h2", class_="post-title").text.strip()
                url = article.find("h2", class_="post-title").find("a")["href"]
                category = article.find("a", class_="post-category").text.strip()
                article_response=requests.get(url,headers={"User-Agent":"Mozilla/5.0"})
                article_soup=BeautifulSoup(article_response.text, "html.parser")
                date_tag=article_soup.find("div", class_="publishDate")
                published_date=date_tag.text.strip() if date_tag else "Unknown"
                if not title or not url:
                    continue
                existing=session.query(ContentItem).filter_by(url=url).first()
                if existing:
                    continue
                item=ContentItem(
                    competitor_name="HyperVerge",
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
                print(f"Error: {e}")
                session.rollback()
                continue
            time.sleep(2)

    session.close()
    print("HyperVerge scraping complete")

if __name__ == "__main__":
    scrape_HyperVerge()