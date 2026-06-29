import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from database.models import SessionLocal, ContentItem

STOP_WORDS = {
    "and", "or", "the", "in", "for", "to", "of", "on", "what", "why",
    "how", "is", "are", "was", "were", "a", "an", "with", "by", "from",
    "its", "it", "at", "be", "has", "have", "do", "does", "as", "this",
    "that", "your", "our", "their", "we", "you", "can", "will", "all",
    "new", "get", "use", "vs", "via", "into", "about", "more", "just",
    "not", "but", "also", "which", "when", "where", "who", "they", "them",
    "complete", "comprehensive", "guide", "need", "know", "everything",
    "ultimate", "top", "best", "essential", "key", "important", "things",
    "tips", "ways", "step", "steps", "should", "must", "want", "looking",
    # competitor brand names
    "signzy", "hyperverge", "authbridge", "idfy", "bureau", "digitap",
    # years
    "2023", "2024", "2025", "2026",
}

TEMPLATE_BIGRAMS = {
    "complete guide", "comprehensive guide", "need know", "everything need",
    "ultimate guide", "step step", "best practices guide", "things know",
    "must know", "should know", "key things", "top things"
}


def clean(word):
    return word.lower().strip(",.:()?!\"'-[]")


def is_valid_word(w):
    if not w:
        return False
    if w in STOP_WORDS:
        return False
    if w.isdigit():
        return False
    if w.startswith("[") or w.endswith("]"):
        return False
    if len(w) < 3:
        return False
    return True


def load_titles():
    db = SessionLocal()
    rows = db.query(ContentItem.competitor_name, ContentItem.title).all()
    db.close()
    return rows


def get_keyword_freq(rows=None):
    if rows is None:
        rows = load_titles()
    freq = defaultdict(int)
    for _, title in rows:
        for word in title.split():
            w = clean(word)
            if is_valid_word(w):
                freq[w] += 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_bigram_freq(rows=None):
    if rows is None:
        rows = load_titles()
    freq = defaultdict(int)
    for _, title in rows:
        words = [clean(w) for w in title.split()]
        words = [w for w in words if is_valid_word(w)]
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram not in TEMPLATE_BIGRAMS:
                freq[bigram] += 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_trigram_freq(rows=None):
    if rows is None:
        rows = load_titles()
    freq = defaultdict(int)
    for _, title in rows:
        words = [clean(w) for w in title.split()]
        words = [w for w in words if is_valid_word(w)]
        for i in range(len(words) - 2):
            freq[f"{words[i]} {words[i+1]} {words[i+2]}"] += 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_publishing_frequency():
    db = SessionLocal()
    results = db.query(ContentItem.competitor_name, ContentItem.published_date).all()
    db.close()
    freq = defaultdict(int)
    for comp, date in results:
        if date:
            freq[comp] += 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_competitor_keyword_freq():
    rows = load_titles()
    comp_kw = defaultdict(lambda: defaultdict(int))
    for comp, title in rows:
        for word in title.split():
            w = clean(word)
            if is_valid_word(w):
                comp_kw[comp][w] += 1
    return {
        comp: sorted(kw.items(), key=lambda x: x[1], reverse=True)[:20]
        for comp, kw in comp_kw.items()
    }


def get_content_type_breakdown():
    db = SessionLocal()
    results = db.query(ContentItem.competitor_name, ContentItem.content_type).all()
    db.close()
    breakdown = defaultdict(lambda: defaultdict(int))
    for comp, ctype in results:
        breakdown[comp][ctype or "Blog Post"] += 1
    return {comp: dict(types) for comp, types in breakdown.items()}


if __name__ == "__main__":
    rows = load_titles()

    print(f"\n{'='*55}\n  TOP KEYWORDS\n{'='*55}")
    for word, count in list(get_keyword_freq(rows).items())[:20]:
        bar = "#" * min(count // 10, 30)
        print(f"  {word:<25} {bar} {count}")

    print(f"\n{'='*55}\n  TOP BIGRAMS\n{'='*55}")
    for bigram, count in list(get_bigram_freq(rows).items())[:15]:
        print(f"  {bigram:<30} {count}")

    print(f"\n{'='*55}\n  TOP TRIGRAMS\n{'='*55}")
    for trigram, count in list(get_trigram_freq(rows).items())[:15]:
        print(f"  {trigram:<40} {count}")

    print(f"\n{'='*55}\n  PUBLISHING FREQUENCY\n{'='*55}")
    for comp, count in get_publishing_frequency().items():
        print(f"  {comp:<20} {count} articles")

    print(f"\n{'='*55}\n  COMPETITOR KEYWORDS\n{'='*55}")
    for comp, kws in get_competitor_keyword_freq().items():
        print(f"\n  {comp}")
        for word, count in kws[:8]:
            print(f"    {word:<20} {count}")