import asyncio
import sys
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Ensure correct pathing for your custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import ContentItem, SessionLocal

async def scrape_bureau():
    print("Starting Bureau scraper...")
    session = SessionLocal()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to the target page
        await page.goto("https://bureau.id/resources/all-blog", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # --- Debug & Diagnostics Section ---
        print("TITLE:", await page.title())
        anchor_count = await page.locator("a").count()
        print("TOTAL ANCHORS SEEN BY PLAYWRIGHT:", anchor_count)
        
        # Extract and print the first 30 raw links to verify formatting
        all_links = await page.evaluate("() => [...document.querySelectorAll('a')].map(a => a.href)")
        print("\nFIRST 30 RAW LINKS DETECTED:")
        for link in all_links[:30]:
            print(f" - {link}")
        print("-" * 50)
        # -------------------------------------

        # Extract target blog URLs using the browser-verified filter
        blog_urls = await page.evaluate("""
            () => {
                return [...new Set(
                    [...document.querySelectorAll('a')]
                        .map(a => a.href)
                        .filter(href => href.includes('/resources/blog/'))
                )];
            }
        """)

        print(f"Found {len(blog_urls)} unique blog URLs to process.")

        # Iterate and scrape each gathered URL
        for url in blog_urls:
            try:
                existing = session.query(ContentItem).filter_by(url=url).first()
                if existing:
                    print(f"Skipping (Already Exists): {url}")
                    continue

                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(1500)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Get title
                title_tag = soup.find("h1")
                title = title_tag.text.strip() if title_tag else await page.title()

                # Get date
                date_tag = soup.find("time")
                published_date = date_tag.text.strip() if date_tag else "Unknown"

                # Get category/topic from meta tags
                meta_desc = soup.find("meta", attrs={"name": "description"})
                summary = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

                if not title or not url:
                    continue

                item = ContentItem(
                    competitor_name="Bureau",
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
                print(f"Error scraping {url}: {e}")
                session.rollback()
                continue

        await browser.close()
        
    session.close()
    print("Bureau scraping complete.")

if __name__ == "__main__":
    asyncio.run(scrape_bureau())