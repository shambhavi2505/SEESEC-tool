import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


headers = {
    "User-Agent": "Mozilla/5.0"
}


def extract_date(soup):

    # Try <time> tags first
    time_tag = soup.find("time")

    if time_tag:

        if time_tag.get("datetime"):
            return time_tag.get("datetime")

        text = time_tag.get_text(strip=True)

        if text:
            return text

    # Search page text for common date formats
    text = soup.get_text(" ", strip=True)

    date_pattern = r"""
        \b
        (?:
            Jan(?:uary)?|
            Feb(?:ruary)?|
            Mar(?:ch)?|
            Apr(?:il)?|
            May|
            Jun(?:e)?|
            Jul(?:y)?|
            Aug(?:ust)?|
            Sep(?:tember)?|
            Oct(?:ober)?|
            Nov(?:ember)?|
            Dec(?:ember)?
        )
        \s+
        \d{1,2},
        \s+
        \d{4}
        \b
    """

    match = re.search(
        date_pattern,
        text,
        re.IGNORECASE | re.VERBOSE
    )

    if match:
        return match.group()

    return None


def scrape_article_page(article_url):

    try:

        response = requests.get(
            article_url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Try to find the article title
        title_tag = soup.find("h1")

        if title_tag:
            title = title_tag.get_text(
                " ",
                strip=True
            )
        else:
            title = None

        # Extract date
        date = extract_date(soup)

        # Get article text
        paragraphs = soup.find_all("p")

        content = " ".join(
            p.get_text(
                " ",
                strip=True
            )
            for p in paragraphs
        )

        # Remove pages with almost no content
        if not content or len(content) < 200:
            return None

        return {
            "title": title,
            "url": article_url,
            "date": date,
            "content": content[:5000]
        }

    except Exception as e:

        print(f"Error scraping article: {article_url}")

        return None

def scrape_articles(website):

    article_urls = []

    paths = [
        "/blog",
        "/blogs",
        "/resources",
        "/insights",
        "/news",
        "/press"
    ]

    website = website.rstrip("/")

    print(f"\nSearching for content on: {website}")

    for path in paths:

        page_url = website + path

        try:

            print(f"Checking: {page_url}")

            response = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:

                print(
                    f"Not found: {response.status_code}"
                )

                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            links = soup.find_all(
                "a",
                href=True
            )

            found_on_page = 0

            for link in links:

                href = link.get("href")

                article_url = urljoin(
                    page_url,
                    href
                )

                # Ignore external websites
                if (
                    urlparse(article_url).netloc
                    !=
                    urlparse(website).netloc
                ):
                    continue

                # Remove # fragments
                article_url = article_url.split("#")[0]

                # Ignore the listing page itself
                if article_url.rstrip("/") == page_url.rstrip("/"):
                    continue

                # IMPORTANT:
                # Only accept URLs related to the
                # content section currently being scraped

                valid_paths = [
                    "/blog/",
                    "/blogs/",
                    "/resources/",
                    "/insights/",
                    "/news/",
                    "/press/"
                ]

                parsed_url = urlparse(article_url)

                if not any(
                    content_path in parsed_url.path
                    for content_path in valid_paths
                ):
                    continue

                # Get link text
                title = link.get_text(
                    " ",
                    strip=True
                )

                # Skip empty links
                if not title:
                    continue

                # Skip very short links
                if len(title) < 15:
                    continue

                skip_words = [
                    "contact",
                    "login",
                    "sign up",
                    "privacy",
                    "terms",
                    "cookie",
                    "home",
                    "about",
                    "careers",
                    "products",
                    "solutions",
                    "read more",
                    "learn more",
                    "view all",
                    "explore"
                ]

                if title.lower() in skip_words:
                    continue

                # Avoid duplicates
                if article_url in article_urls:
                    continue

                article_urls.append(
                    article_url
                )

                found_on_page += 1

            print(
                f"Found {found_on_page} possible article URLs"
            )

        except Exception as e:

            print(
                f"Error scraping {page_url}: {e}"
            )

    print(
        f"\nFound {len(article_urls)} unique article URLs."
    )

    print(
        "\nNow visiting each article page...\n"
    )

    articles = []

    for index, article_url in enumerate(
        article_urls,
        start=1
    ):

        print(
            f"[{index}/{len(article_urls)}] "
            f"Scraping: {article_url}"
        )

        article = scrape_article_page(
            article_url
        )

        if article:

            articles.append(article)

    return articles


if __name__ == "__main__":

    website = input(
        "Enter company website: "
    )

    results = scrape_articles(website)

    print(
        f"\nTOTAL REAL ARTICLES FOUND: "
        f"{len(results)}\n"
    )

    for article in results[:10]:

        print(
            f"TITLE: {article['title']}"
        )

        print(
            f"URL: {article['url']}"
        )

        print(
            f"DATE: {article['date']}"
        )

        print(
            f"CONTENT: "
            f"{article['content'][:300]}..."
        )

        print("-" * 70)