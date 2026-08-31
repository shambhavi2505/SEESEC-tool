import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from analysis.techstack import detect_tech_stack


# ============================================================
# CONFIGURATION
# ============================================================

ARTICLE_PATH_KEYWORDS = [
    "blog",
    "blogs",
    "article",
    "articles",
    "news",
    "insight",
    "insights",
    "resource",
    "resources",
    "whitepaper",
    "whitepapers",
    "case-study",
    "case-studies",
    "webinar",
    "press-release",
    "press-releases",
    "knowledge",
    "stories",
    "post",
    "posts",
]

# Bare hub/index pages (e.g. /blog with no further path segments).
# These are landing pages, not individual articles — they should be
# crawled INTO for real content, not treated as articles themselves.
HUB_PATH_NAMES = {
    "blog", "blogs", "news", "insights", "resources",
    "articles", "press", "press-release", "press-releases",
    "case-study", "case-studies", "stories",
}


def is_bare_hub_url(url):
    """
    True if the URL is just a hub root like /blog or /news,
    with no further path segments (i.e. not an individual post).
    """

    if not url:
        return False

    segments = [
        s for s in urlparse(url).path.lower().split("/") if s
    ]

    return (
        len(segments) == 1
        and segments[0] in HUB_PATH_NAMES
    )


CONTENT_TYPE_RULES = {
    "Case Study": [
        "case-study",
        "case_study",
        "case study",
        "casestudy",
    ],
    "Whitepaper": [
        "whitepaper",
        "white-paper",
        "white paper",
    ],
    "Webinar": [
        "webinar",
        "webinars",
    ],
    "Press Release": [
        "press-release",
        "press-releases",
        "press release",
        "pressroom",
        "newsroom",
    ],
    "News": [
        "/news/",
        "/news",
    ],
    "Resource": [
        "resource",
        "resources",
    ],
    "Insight": [
        "insight",
        "insights",
    ],
}

SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin",
    "twitter.com": "twitter",
    "x.com": "x",
    "youtube.com": "youtube",
    "instagram.com": "instagram",
    "facebook.com": "facebook",
}


# ============================================================
# URL HELPERS
# ============================================================

def normalize_url(url):
    """
    Normalize URLs to make duplicate detection easier.
    """

    if not url:
        return None

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove fragments
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    if not parsed.netloc:
        return None

    scheme = parsed.scheme.lower()
    domain = parsed.netloc.lower()

    # Remove default ports
    domain = domain.replace(":80", "").replace(":443", "")

    path = parsed.path or "/"

    # Remove trailing slash except homepage
    if path != "/":
        path = path.rstrip("/")

    clean = f"{scheme}://{domain}{path}"

    # Preserve useful query parameters only when necessary.
    # For scraping we generally don't want tracking parameters.
    return clean


def same_domain(base_url, target_url):
    """
    Check whether target URL belongs to the same site as the base URL.

    Treats subdomains as the same site (e.g. blog.example.com counts
    as the same site as www.example.com / example.com), since many
    companies host their blog/resources section on a subdomain.
    """

    if not base_url or not target_url:
        return False

    base_domain = (
        urlparse(base_url)
        .netloc
        .lower()
        .replace("www.", "")
    )

    target_domain = (
        urlparse(target_url)
        .netloc
        .lower()
        .replace("www.", "")
    )

    if base_domain == target_domain:
        return True

    base_root = ".".join(base_domain.split(".")[-2:])
    target_root = ".".join(target_domain.split(".")[-2:])

    return bool(base_root) and base_root == target_root


def is_valid_http_url(url):
    """
    Check whether URL is a normal HTTP/HTTPS URL.
    """

    if not url:
        return False

    parsed = urlparse(url)

    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_asset_url(url):
    """
    Ignore images, videos, documents and static assets.
    """

    path = urlparse(url).path.lower()

    ignored_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".css",
        ".js",
        ".json",
        ".xml",
        ".zip",
        ".mp4",
        ".mp3",
        ".wav",
        ".avi",
        ".mov",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
    )

    return path.endswith(ignored_extensions)


# ============================================================
# ARTICLE DETECTION
# ============================================================

def looks_like_article_url(url):
    """
    Determine whether a URL looks like an article/resource page.
    """

    if not url:
        return False

    # Bare hub/index pages (e.g. /blog) are landing pages, not
    # individual articles.
    if is_bare_hub_url(url):
        return False

    path = urlparse(url).path.lower()

    # Strong article/resource signals
    for keyword in ARTICLE_PATH_KEYWORDS:

        if keyword in path:
            return True

    # Date-based URLs:
    # /2026/08/article-name
    # /2025/12/15/article-name
    if re.search(r"/20\d{2}/\d{1,2}/", path):
        return True

    # Avoid obvious non-content pages
    ignored_paths = [
        "/about",
        "/contact",
        "/careers",
        "/career",
        "/login",
        "/signup",
        "/sign-up",
        "/privacy",
        "/terms",
        "/pricing",
        "/products",
        "/product",
        "/solutions",
        "/services",
        "/demo",
    ]

    if any(path.rstrip("/").endswith(p) for p in ignored_paths):
        return False

    return False


def score_article_url(url):
    """
    Give a URL an article-likelihood score.

    Higher score = more likely to be an article.
    """

    if not url:
        return 0

    path = urlparse(url).path.lower()

    score = 0

    strong_keywords = [
        "blog",
        "article",
        "insight",
        "case-study",
        "whitepaper",
        "webinar",
        "press-release",
        "news",
    ]

    medium_keywords = [
        "resource",
        "knowledge",
        "story",
        "stories",
        "post",
    ]

    for keyword in strong_keywords:
        if keyword in path:
            score += 5

    for keyword in medium_keywords:
        if keyword in path:
            score += 3

    # Date URL
    if re.search(r"/20\d{2}/\d{1,2}/", path):
        score += 4

    # More path segments usually means deeper content page
    segments = [
        x for x in path.split("/")
        if x
    ]

    if len(segments) >= 2:
        score += 1

    if len(segments) >= 3:
        score += 1

    return score


# ============================================================
# CONTENT TYPE
# ============================================================

def guess_content_type(url, title=""):
    """
    Guess content type using URL and title.
    """

    value = f"{url} {title}".lower()

    for content_type, keywords in CONTENT_TYPE_RULES.items():

        for keyword in keywords:

            if keyword in value:
                return content_type

    return "Blog"


# ============================================================
# PAGE FETCHING
# ============================================================

async def fetch_page(page, url):
    """
    Open a page with Playwright and return HTML.
    """

    try:

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        if not response:
            return None

        # Give JavaScript-rendered content some time
        try:
            await page.wait_for_load_state(
                "networkidle",
                timeout=5000,
            )
        except Exception:
            pass

        await page.wait_for_timeout(1000)

        return await page.content()

    except Exception as e:

        print(f"[WARN] Failed to fetch: {url}")
        print(f"       {e}")

        return None


# ============================================================
# LINK EXTRACTION
# ============================================================

def extract_links(base_url, html):
    """
    Extract internal links from a page.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = set()

    for anchor in soup.find_all("a", href=True):

        href = anchor.get("href")

        if not href:
            continue

        href = href.strip()

        if href.startswith(
            (
                "#",
                "mailto:",
                "tel:",
                "javascript:",
                "data:",
            )
        ):
            continue

        full_url = urljoin(
            base_url,
            href,
        )

        full_url = normalize_url(
            full_url
        )

        if not full_url:
            continue

        if not is_valid_http_url(full_url):
            continue

        if not same_domain(
            base_url,
            full_url,
        ):
            continue

        if is_asset_url(full_url):
            continue

        links.add(full_url)

    return links


# ============================================================
# SOCIAL LINKS
# ============================================================

def extract_social_links(html):
    """
    Extract public social media profiles.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    results = {}

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = anchor.get("href")

        if not href:
            continue

        href_lower = href.lower()

        for domain, platform in SOCIAL_DOMAINS.items():

            if domain in href_lower:

                # Don't save tracking duplicates
                if platform not in results:
                    results[platform] = href

    return results


# ============================================================
# COMPANY DESCRIPTION
# ============================================================

def extract_description(html):
    """
    Extract a basic company/page description.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # OpenGraph description
    meta = soup.find(
        "meta",
        attrs={"property": "og:description"},
    )

    if meta and meta.get("content"):
        return meta["content"].strip()

    # Standard meta description
    meta = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if meta and meta.get("content"):
        return meta["content"].strip()

    # First meaningful paragraph
    paragraphs = soup.find_all("p")

    for paragraph in paragraphs:

        text = paragraph.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 80:
            return text[:500]

    return None


# ============================================================
# DATE EXTRACTION
# ============================================================

def clean_date(value):
    """
    Clean and normalize date text.
    """

    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value[:100]


def extract_date_from_jsonld(soup):
    """
    Look for article dates inside JSON-LD structured data.
    """

    scripts = soup.find_all(
        "script",
        type="application/ld+json",
    )

    for script in scripts:

        try:

            raw = script.string

            if not raw:
                continue

            data = json.loads(raw)

            objects = []

            if isinstance(data, dict):
                objects.append(data)

                if "@graph" in data and isinstance(
                    data["@graph"],
                    list,
                ):
                    objects.extend(
                        data["@graph"]
                    )

            elif isinstance(data, list):
                objects.extend(data)

            for item in objects:

                if not isinstance(item, dict):
                    continue

                for field in (
                    "datePublished",
                    "dateCreated",
                    "dateModified",
                ):

                    if item.get(field):
                        return clean_date(
                            item[field]
                        )

        except Exception:
            continue

    return None


def extract_date(soup):
    """
    Extract publication date using multiple strategies.
    """

    # 1. <time>
    time_tags = soup.find_all("time")

    for tag in time_tags:

        value = (
            tag.get("datetime")
            or tag.get_text(
                " ",
                strip=True,
            )
        )

        if value:
            return clean_date(value)

    # 2. JSON-LD
    date = extract_date_from_jsonld(
        soup
    )

    if date:
        return date

    # 3. Meta tags
    meta_names = [
        "article:published_time",
        "date",
        "publish-date",
        "datePublished",
        "publication_date",
    ]

    for name in meta_names:

        tag = soup.find(
            "meta",
            attrs={"name": name},
        )

        if tag and tag.get("content"):
            return clean_date(
                tag["content"]
            )

    # OpenGraph
    og_tag = soup.find(
        "meta",
        attrs={"property": "article:published_time"},
    )

    if og_tag and og_tag.get("content"):
        return clean_date(
            og_tag["content"]
        )

    # 4. Search visible text
    text = soup.get_text(
        " ",
        strip=True,
    )

    date_patterns = [
        # 2026-08-20
        r"\b20\d{2}-\d{1,2}-\d{1,2}\b",

        # 20/08/2026
        r"\b\d{1,2}[/-]\d{1,2}[/-]20\d{2}\b",

        # August 20, 2026
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+\d{1,2},\s+20\d{2}\b",

        # 20 August 2026
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+20\d{2}\b",
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return clean_date(
                match.group()
            )

    return None


# ============================================================
# ARTICLE EXTRACTION
# ============================================================

def extract_article(html, url):
    """
    Extract article metadata from a page.

    Returns None if the page doesn't look like a useful
    content page.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = None

    h1 = soup.find("h1")

    if h1:

        title = h1.get_text(
            " ",
            strip=True,
        )

    # OpenGraph title
    if not title:

        og_title = soup.find(
            "meta",
            attrs={"property": "og:title"},
        )

        if og_title:
            title = og_title.get(
                "content"
            )

    # Page title
    if not title and soup.title:

        title = soup.title.get_text(
            " ",
            strip=True,
        )

    if not title:
        return None

    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    # Ignore extremely short titles
    if len(title) < 5:
        return None

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = extract_description(
        html
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    published_date = extract_date(
        soup
    )

    # --------------------------------------------------------
    # CONTENT TYPE
    # --------------------------------------------------------

    content_type = guess_content_type(
        url,
        title,
    )

    # --------------------------------------------------------
    # ARTICLE SCORE
    # --------------------------------------------------------

    article_score = score_article_url(
        url
    )

    return {
        "title": title,
        "url": url,
        "published_date": published_date,
        "content_type": content_type,
        "description": description,
        "article_score": article_score,
    }


# ============================================================
# SITEMAP DISCOVERY
# ============================================================

async def discover_sitemaps(page, website):
    """
    Try common sitemap locations.
    """

    parsed = urlparse(website)

    root = (
        f"{parsed.scheme}://{parsed.netloc}"
    )

    candidates = [
        f"{root}/sitemap.xml",
        f"{root}/sitemap_index.xml",
        f"{root}/sitemap-index.xml",
        f"{root}/post-sitemap.xml",
        f"{root}/blog-sitemap.xml",
    ]

    found = []

    for sitemap_url in candidates:

        try:

            response = await page.goto(
                sitemap_url,
                wait_until="domcontentloaded",
                timeout=10000,
            )

            if response and response.ok:

                content = await page.content()

                if (
                    "<urlset" in content.lower()
                    or "<sitemapindex" in content.lower()
                ):

                    found.append(
                        sitemap_url
                    )

        except Exception:
            continue

    return found


async def extract_sitemap_urls(
    page,
    sitemap_urls,
    base_url,
    max_urls=200,
):
    """
    Extract URLs from sitemap files.
    """

    results = set()

    for sitemap_url in sitemap_urls:

        try:

            response = await page.goto(
                sitemap_url,
                wait_until="domcontentloaded",
                timeout=15000,
            )

            if not response:
                continue

            text = await page.locator(
                "body"
            ).inner_text()

            # XML is sometimes rendered as text
            urls = re.findall(
                r"https?://[^\s<>\"']+",
                text,
            )

            for url in urls:

                url = normalize_url(url)

                if not url:
                    continue

                if not same_domain(
                    base_url,
                    url,
                ):
                    continue

                if is_asset_url(url):
                    continue

                results.add(url)

                if len(results) >= max_urls:
                    return results

        except Exception:
            continue

    return results


# ============================================================
# CONCURRENT ARTICLE SCRAPING
# ============================================================

async def scrape_article(
    context,
    url,
    index,
    total,
):
    """
    Scrape a single article page.
    """

    page = await context.new_page()

    try:

        print(
            f"   [{index}/{total}] {url}"
        )

        html = await fetch_page(
            page,
            url,
        )

        if not html:
            return None

        return extract_article(
            html,
            url,
        )

    except Exception as e:

        print(
            f"   [WARN] Article failed: {url}"
        )
        print(
            f"          {e}"
        )

        return None

    finally:

        await page.close()


# ============================================================
# MAIN GENERIC SCRAPER
# ============================================================

async def scrape_company(
    website,
    max_pages=30,
    concurrency=5,
):
    """
    Generic company scraper.
    """

    website = normalize_url(website)

    if not website:
        raise ValueError("Invalid website URL")

    print("=" * 70)
    print("SEESEC GENERIC COMPANY SCRAPER")
    print("=" * 70)
    print(f"Website: {website}")

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                # Required for Chromium to run reliably inside
                # containers (Docker/Render) — without these it can
                # crash or hang unpredictably.
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        try:
            # STEP 1 — HOMEPAGE
            print("\n[1/6] Fetching homepage...")

            homepage_html = await fetch_page(page, website)

            if not homepage_html:
                await browser.close()
                return {
                    "website": website,
                    "company_description": None,
                    "pages_discovered": 0,
                    "pages_scanned": 0,
                    "articles_found": 0,
                    "articles": [],
                    "social_links": {},
                    "tech_stack": [],
                    "failed_urls": [],
                }

            company_description = extract_description(homepage_html)
            social_links = extract_social_links(homepage_html)
            tech_stack = detect_tech_stack(homepage_html)

            # STEP 2 — INTERNAL LINKS
            print("[2/6] Discovering internal links...")

            homepage_links = extract_links(website, homepage_html)

            print(f"Found {len(homepage_links)} internal links.")

            # STEP 3 — SITEMAP
            print("[3/6] Checking sitemap...")

            sitemap_urls = await discover_sitemaps(page, website)
            sitemap_links = set()

            if sitemap_urls:
                print(f"Found {len(sitemap_urls)} sitemap(s).")

                sitemap_links = await extract_sitemap_urls(
                    page,
                    sitemap_urls,
                    website,
                    max_urls=max(200, max_pages * 5),
                )

                print(
                    f"Sitemap yielded {len(sitemap_links)} URLs."
                )
            else:
                print("No sitemap detected.")

            # STEP 3.5 — HUB EXPANSION
            all_links = homepage_links | sitemap_links

            hub_urls = [
                url for url in all_links
                if is_bare_hub_url(url)
            ][:5]

            if hub_urls:
                print(
                    f"[3.5/6] Expanding {len(hub_urls)} hub page(s)..."
                )

                for hub_url in hub_urls:
                    hub_html = await fetch_page(page, hub_url)

                    if hub_html:
                        hub_links = extract_links(
                            hub_url,
                            hub_html,
                        )

                        all_links |= hub_links

            # STEP 4 — CANDIDATE DISCOVERY
            print(
                "[4/6] Finding article/resource candidates..."
            )

            candidates = []

            for url in all_links:
                if not looks_like_article_url(url):
                    continue

                score = score_article_url(url)

                if score > 0:
                    candidates.append((score, url))

            candidates.sort(
                key=lambda x: (-x[0], x[1])
            )

            seen = set()
            article_candidates = []

            for score, url in candidates:
                if url in seen:
                    continue

                seen.add(url)
                article_candidates.append(url)

            article_candidates = article_candidates[:max_pages]

            print(
                f"Selected {len(article_candidates)} "
                f"article/resource candidates."
            )

            # STEP 5 — SCRAPE ARTICLES
            print(
                "[5/6] Scraping article/resource pages..."
            )

            articles = []
            failed_urls = []
            semaphore = asyncio.Semaphore(concurrency)

            async def scrape_with_limit(index, url):
                async with semaphore:
                    result = await scrape_article(
                        context,
                        url,
                        index,
                        len(article_candidates),
                    )

                    if result:
                        return result

                    failed_urls.append(url)
                    return None

            tasks = [
                scrape_with_limit(index, url)
                for index, url in enumerate(
                    article_candidates,
                    1,
                )
            ]

            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    articles.append(result)

            # STEP 6 — FINAL PROCESSING
            print("[6/6] Cleaning and deduplicating...")

            unique_articles = {}

            for article in articles:
                article_url = article.get("url")

                if article_url:
                    unique_articles[article_url] = article

            articles = list(unique_articles.values())

            articles.sort(
                key=lambda x: (
                    -x.get("article_score", 0),
                    x.get("title", "").lower(),
                )
            )

            result = {
                "website": website,
                "company_description": company_description,
                "pages_discovered": len(all_links),
                "pages_scanned": len(article_candidates),
                "articles_found": len(articles),
                "articles": articles,
                "social_links": social_links,
                "tech_stack": tech_stack,
                "failed_urls": failed_urls,
            }

            print("\n" + "=" * 70)
            print(
                f"Pages discovered: "
                f"{result['pages_discovered']}"
            )
            print(
                f"Pages scanned: "
                f"{result['pages_scanned']}"
            )
            print(
                f"Articles found: "
                f"{result['articles_found']}"
            )
            print(
                f"Social profiles: "
                f"{len(result['social_links'])}"
            )
            print(
                f"Failed pages: "
                f"{len(result['failed_urls'])}"
            )
            print("=" * 70)

            return result

        finally:
            await page.close()
            await browser.close()


# ============================================================
# SYNCHRONOUS WRAPPER
# ============================================================

def scrape(
    website,
    max_pages=30,
    concurrency=5,
):
    """
    Synchronous wrapper so the scraper can be called from
    normal Python/FastAPI code.
    """

    return asyncio.run(
        scrape_company(
            website,
            max_pages=max_pages,
            concurrency=concurrency,
        )
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = scrape(
        "https://signzy.com",
        max_pages=20,
        concurrency=5,
    )

    print("\n")
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        f"\nWebsite: "
        f"{result['website']}"
    )

    print(
        f"Pages discovered: "
        f"{result['pages_discovered']}"
    )

    print(
        f"Pages scanned: "
        f"{result['pages_scanned']}"
    )

    print(
        f"Articles found: "
        f"{result['articles_found']}"
    )

    print(
        f"\nCompany description:\n"
        f"{result['company_description']}"
    )

    print(
        "\nSocial profiles:"
    )

    for platform, url in (
        result["social_links"].items()
    ):

        print(
            f"  {platform}: {url}"
        )

    print(
        "\nArticles:"
    )

    for article in result[
        "articles"
    ][:10]:

        print(
            f"\nTITLE: "
            f"{article['title']}"
        )

        print(
            f"URL: "
            f"{article['url']}"
        )

        print(
            f"DATE: "
            f"{article['published_date']}"
        )

        print(
            f"TYPE: "
            f"{article['content_type']}"
        )

        print(
            f"DESCRIPTION: "
            f"{article['description']}"
        )