"""Regulations.gov API ingestion — rulemaking dockets and documents."""

import os

import requests

from keywords import matches_tracker_item
from normalize import make_item

API_BASE = "https://api.regulations.gov/v4/documents"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}
SEARCH_TERMS = [
    "artificial intelligence",
    "digital asset",
    "cryptocurrency",
    "stablecoin",
    "genius act",
    "prediction market",
    "event contract",
    "security-based swap",
    "commodity futures",
]


def fetch_all():
    api_key = os.environ.get("REGULATIONS_API_KEY", "DEMO_KEY")
    if api_key == "DEMO_KEY":
        print("[regulations-gov] using DEMO_KEY (limited rate; set REGULATIONS_API_KEY for production)")

    seen = set()
    items = []
    headers = {**HEADERS, "X-Api-Key": api_key}

    for term in SEARCH_TERMS:
        try:
            resp = requests.get(
                API_BASE,
                headers=headers,
                params={
                    "filter[searchTerm]": term,
                    "sort": "-postedDate",
                    "page[size]": 20,
                },
                timeout=30,
            )
            resp.raise_for_status()
            for doc in resp.json().get("data", []):
                attrs = doc.get("attributes", {})
                title = (attrs.get("title") or "").strip()
                summary = attrs.get("summary") or ""
                candidate = {"title": title, "summary": summary}
                if not title or not matches_tracker_item(candidate):
                    continue
                doc_id = doc.get("id")
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                link = f"https://www.regulations.gov/document/{doc_id}"
                items.append(
                    make_item(
                        agency="Federal Register",
                        title=title,
                        link=link,
                        published=attrs.get("postedDate", ""),
                        source_id="regulations-gov",
                        external_id=doc_id,
                        summary=summary[:500] if summary else None,
                        development_type="proposed-rule",
                    )
                )
        except Exception as e:
            print(f"[warn] regulations-gov ({term}): {e}")

    print(f"[regulations-gov] regulations-gov: {len(items)} items")
    return items
