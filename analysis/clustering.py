import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from database.models import SessionLocal, ContentItem

TOPIC_MAP = {
    "Video KYC": [
        "video kyc", "vkyc", "video-based kyc", "video verification",
        "liveness", "face match", "video call kyc", "video based"
    ],
    "KYC": [
        "kyc", "ekyc", "e-kyc", "know your customer", "ckyc",
        "central kyc", "kyc compliance", "kyc process", "kyc solution",
        "kyc verification", "kyc onboarding", "kyc check", "kyc norms",
        "kyc guide", "kyc tool", "kyc platform", "kyc software"
    ],
    "KYB": [
        "kyb", "know your business", "business verification",
        "ubo", "ultimate beneficial owner", "company verification",
        "business onboarding", "vendor verification", "vendor due diligence",
        "vendor screening", "supplier verification"
    ],
    "AML": [
        "aml", "anti-money laundering", "anti money laundering",
        "money laundering", "transaction monitoring", "suspicious transaction",
        "pep screening", "pep", "sanctions screening", "sanctions",
        "watchlist", "terrorist financing", "fatf", "financial crime"
    ],
    "DPDP & Privacy": [
        "dpdp", "digital personal data", "data protection",
        "data privacy", "privacy law", "gdpr", "pdpa",
        "consent management", "personal data", "data principal"
    ],
    "Fraud Detection": [
        "fraud", "fraud detection", "fraud prevention", "fraud risk",
        "identity theft", "account takeover", "ato", "synthetic identity",
        "deepfake", "document fraud", "fake id", "scam",
        "mule account", "chargeback"
    ],
    "Background Verification": [
        "background verification", "background check", "bgv",
        "employee verification", "employee screening", "employment verification",
        "criminal record", "criminal background", "police verification",
        "reference check", "address verification", "education verification"
    ],
    "Identity Verification": [
        "identity verification", "id verification", "identity proofing",
        "document verification", "aadhaar", "pan verification", "pan card",
        "passport verification", "driving licence", "voter id",
        "ocr", "face verification", "biometric", "digilocker", "id document"
    ],
    "Digital Onboarding": [
        "onboarding", "customer onboarding", "digital onboarding",
        "account opening", "paperless onboarding", "remote onboarding",
        "onboarding experience", "onboarding flow", "drop-off"
    ],
    "Risk & Compliance": [
        "compliance", "regulatory", "regulation", "rbi", "sebi", "irdai",
        "fema", "pmla", "risk-based", "due diligence", "enhanced due diligence",
        "edd", "cdd", "customer due diligence", "risk management",
        "risk assessment", "audit", "fincen", "ofac"
    ],
    "Banking & Lending": [
        "bank", "banking", "lending", "loan", "nbfc", "credit",
        "bank account", "bank statement", "account aggregator",
        "credit bureau", "cibil", "credit score", "underwriting",
        "digital lending", "bnpl", "buy now pay later"
    ],
    "Fintech & Payments": [
        "fintech", "payment", "upi", "neobank", "digital wallet",
        "payment gateway", "prepaid", "remittance", "insurtech",
        "wealthtech", "embedded finance", "open banking"
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber security", "data breach",
        "ransomware", "zero trust", "mfa", "two factor",
        "otp", "phone risk", "sim swap", "device fingerprint"
    ],
    "HR & Employment": [
        "hr", "human resource", "hiring", "recruitment",
        "workforce", "gig worker", "moonlighting", "candidate screening",
        "pre-employment", "staffing"
    ],
    "Global & Cross-Border": [
        "global", "international", "cross-border", "uae", "europe",
        "singapore", "middle east", "itin", "ssn", "rfc", "mexico", "africa"
    ],
}


def detect_topics(title: str) -> list:
    text = title.lower()
    found, seen = [], set()
    for topic, keywords in TOPIC_MAP.items():
        for kw in keywords:
            if kw in text and topic not in seen:
                found.append(topic)
                seen.add(topic)
                break
    return found if found else ["Other"]


def update_all_articles():
    db = SessionLocal()
    articles = db.query(ContentItem).all()
    for a in articles:
        a.topics = ", ".join(detect_topics(a.title or ""))
    db.commit()
    count = len(articles)
    db.close()
    print(f" Updated {count} articles")
    return count


def print_topic_stats():
    db = SessionLocal()
    articles = db.query(ContentItem).all()
    db.close()

    topic_counts = defaultdict(int)
    competitor_topics = defaultdict(lambda: defaultdict(int))
    other_titles = []

    for a in articles:
        topics = [t.strip() for t in (a.topics or "Other").split(",")]
        for t in topics:
            topic_counts[t] += 1
            competitor_topics[a.competitor_name][t] += 1
        if "Other" in topics:
            other_titles.append(a.title)

    total = len(articles)

    print(f"\n{'='*60}")
    print(f"  TOPIC DISTRIBUTION  ({total} articles)")
    print(f"{'='*60}")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * min(int(count / total * 50), 50)
        pct = count / total * 100
        print(f"  {topic:<28} {bar:<50} {count:>4} ({pct:.1f}%)")

    print(f"\n{'='*60}")
    print(f"  TOP TOPICS PER COMPETITOR")
    print(f"{'='*60}")
    for comp, topics in sorted(competitor_topics.items()):
        top = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:4]
        print(f"\n  {comp}")
        for t, c in top:
            print(f"    {t:<28} {c}")

    other_count = topic_counts.get("Other", 0)
    print(f"\n{'='*60}")
    print(f"  UNCATEGORIZED: {other_count} ({other_count/total*100:.1f}%)")
    print(f"{'='*60}")
    for t in other_titles[:10]:
        print(f"  - {t}")


if __name__ == "__main__":
    update_all_articles()
    print_topic_stats()
