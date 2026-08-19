import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.search import find_website
from scraper.generic import scrape_articles
from scraper.save_company import save_company_data
from analysis.comp_ai import generate_competitor_summary

def run_full_analysis(company_name):
    
    print(f"\nSearching for {company_name} website...")
    candidates = find_website(company_name)
    
    if not candidates:
        print("No website found.")
        return
    
    print("\nFound these websites:")
    for i, site in enumerate(candidates, 1):
        print(f"{i}. {site}")
    
    choice = input("\nWhich one is correct? (1/2/3): ")
    website = candidates[int(choice) - 1]
    
    print(f"\nScraping {website}...")
    articles = scrape_articles(website)
    
    print(f"\nSaving {len(articles)} articles to database...")
    save_company_data(company_name, website, articles)
    
    print("\nGenerating AI summary...")
    summary = generate_competitor_summary(company_name, articles)
    
    print("\nAI SUMMARY:")
    print(summary)

if __name__ == "__main__":
    company = input("Enter company name: ")
    run_full_analysis(company)