import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from database.models import ContentItem, SessionLocal


async def scrape_authbridge():
    print("Starting AuthBridge scraper")

    session = SessionLocal()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://authbridge.com/resources/blogs/?ref_page=resources/blogs"
        await page.goto(url, wait_until="networkidle")

        await page.wait_for_selector("div.b_box")

        page_num = 1

        while True:
            print(f"\nScraping page {page_num}")

            await page.wait_for_selector("div.b_box")

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            blogs = soup.find_all("div", class_="b_box")
            print(f"Found {len(blogs)} blogs")

            for blog in blogs:
                try:
                    link_tag = blog.find("a")
                    title_tag = blog.find("h3")
                    date_tag = blog.find("span")

                    title = title_tag.get_text(strip=True) if title_tag else None
                    url = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
                    published_date = date_tag.get_text(strip=True) if date_tag else None

                    if not url:
                        continue

                    print(title)

                    existing = session.query(ContentItem).filter_by(url=url).first()
                    if existing:
                        continue

                    item = ContentItem(
                        competitor_name="AuthBridge",
                        content_type="blog",
                        title=title,
                        url=url,
                        published_date=published_date,
                        topics="Unknown"
                    )

                    session.add(item)
                    session.commit()

                except Exception as e:
                    print(f"Error: {e}")
                    session.rollback()


            try:
                next_button = page.locator("text=>").first

                if await next_button.count() == 0:
                    print("No next button found. Stopping.")
                    break

                parent_class = await next_button.get_attribute("class")
                if parent_class and "disabled" in parent_class:
                    print("Last page reached.")
                    break

                print("Clicking next page...")
                await next_button.click()

                await page.wait_for_timeout(2000)

                page_num += 1

            except Exception:
                print("Pagination ended or error occurred")
                break

        await browser.close()
        session.close()

        print("Scraping complete")


if __name__ == "__main__":
    asyncio.run(scrape_authbridge())