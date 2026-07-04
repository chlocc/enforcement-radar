"""Federal Register API ingestion — digital-asset and AI rulemaking."""

from datetime import datetime, timedelta, timezone

import requests

from keywords import matches_tracker_item
from normalize import make_item

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}
API_BASE = "https://www.federalregister.gov/api/v1/documents.json"
SEARCH_TERMS = [
    "cryptocurrency",
    "stablecoin",
    "virtual currency",
    "digital asset",
    "genius act",
    "artificial intelligence",
    "machine learning",
    "algorithmic trading",
    "prediction market",
    "event contract",
    "commodity futures",
    "security-based swap",
]


def fetch_all(days_back=30):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    seen = set()
    items = []

    for term in SEARCH_TERMS:
        try:
            resp = requests.get(
                API_BASE,
                params={
                    "conditions[term]": term,
                    "conditions[publication_date][gte]": cutoff,
                    "per_page": 20,
                    "order": "newest",
                    "fields[]": ["title", "publication_date", "html_url", "document_number", "abstract"],
                },
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            for doc in resp.json().get("results", []):
                title = doc.get("title", "").strip()
                abstract = doc.get("abstract") or ""
                candidate = {"title": title, "summary": abstract}
                if not title or not matches_tracker_item(candidate):
                    continue
                doc_num = doc.get("document_number")
                if doc_num in seen:
                    continue
                seen.add(doc_num)
                items.append(
                    make_item(
                        agency="Federal Register",
                        title=title,
                        link=doc.get("html_url", ""),
                        published=doc.get("publication_date", ""),
                        source_id="federal-register",
                        external_id=doc_num,
                        summary=abstract[:500] if abstract else None,
                    )
                )
        except Exception as e:
            print(f"[warn] federal-register ({term}): {e}")

    print(f"[federal-register] federal-register: {len(items)} items")
    return items
