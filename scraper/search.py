from ddgs import DDGS
from ddgs.exceptions import DDGSException
import re
import time


def find_website(company_name):
    query = company_name + " official website"
    candidates = []

    # Retry a couple of times since DuckDuckGo search occasionally
    # rate-limits or returns "No results found" transiently.
    attempts = 3

    for attempt in range(1, attempts + 1):
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=8)

                for r in results:
                    url = r["href"]
                    skip = ["linkedin", "facebook", "twitter", "wikipedia",
                            "youtube", "glassdoor", "crunchbase", "indiamart"]
                    if any(s in url for s in skip):
                        continue
                    match = re.match(r'https?://[^/]+', url)
                    if match:
                        root = match.group(0)
                        if root not in candidates:
                            candidates.append(root)
                    if len(candidates) >= 3:
                        break

            # Success (even if candidates is empty, DDG didn't error)
            return candidates

        except DDGSException as e:
            print(f"[WARN] DDGS search failed (attempt {attempt}/{attempts}): {e}")

            if attempt < attempts:
                time.sleep(1.5)
                continue

            # All attempts exhausted - return empty list instead of
            # crashing the API endpoint with a 500.
            return []

    return candidates