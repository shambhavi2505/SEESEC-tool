"""
analysis/topics.py

Lightweight keyword-based topic classifier.

SEESEC operates in the KYC / identity verification / fintech compliance
space. This module tags scraped articles with topics from that domain so
we can later compute what a competitor is focusing on, and where SEESEC
has content gaps.

This is intentionally simple (keyword matching, not ML/NLP) so it runs
instantly during the live scrape pipeline with no extra API calls.
"""

TOPIC_KEYWORDS = {
    "KYC": [
        "kyc", "know your customer", "video kyc", "ekyc", "e-kyc",
    ],
    "KYB": [
        "kyb", "know your business", "business verification",
    ],
    "AML": [
        "aml", "anti-money laundering", "money laundering",
    ],
    "Fraud Detection": [
        "fraud", "deepfake", "liveness", "spoof", "injection attack",
        "fake id", "forgery",
    ],
    "Identity Verification": [
        "identity verification", "id verification", "document verification",
        "driver's license", "driving license", "digital id", "digital identity",
        "age assurance", "age verification", "mobile driver",
    ],
    "Risk & Compliance": [
        "compliance", "risk", "regulation", "regulatory", "rbi", "sebi",
        "pmla", "directive", "guideline",
    ],
    "Banking & Lending": [
        "banking", "lending", "loan", "nbfc", "credit", "casa",
        "loan recovery",
    ],
    "DPDP & Privacy": [
        "privacy", "dpdp", "gdpr", "data protection", "pdp bill", "ccpa",
    ],
    "Digital Onboarding": [
        "onboarding", "digital onboarding", "merchant onboarding",
    ],
    "Fintech & Payments": [
        "fintech", "payment", "payments", "upi", "enach",
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber security", "encryption", "cryptography",
    ],
    "Background Verification": [
        "background verification", "background check",
    ],
    "HR & Employment": [
        "hr ", "human resources", "employment", "hiring", "recruitment",
    ],
    "Global & Cross-Border": [
        "cross-border", "cross border", "global", "international",
        " usa ", " uk ", " eu ",
    ],
}


def tag_topics(title, description=""):
    """
    Classify an article into one or more SEESEC-domain topics based on
    keyword matches in its title + description.

    Returns a comma-separated string of matched topics, e.g.
    "KYC, Fraud Detection". Returns "Other" if nothing matches.
    """

    text = f" {title or ''} {description or ''} ".lower()

    matched = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                matched.append(topic)
                break

    if not matched:
        return "Other"

    return ", ".join(matched)