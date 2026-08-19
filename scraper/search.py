from ddgs import DDGS
import re

def find_website(company_name):
    query = company_name + " official website"
    candidates = []

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

    return candidates