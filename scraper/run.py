"""Fetch all agency feeds, normalize dates, dedupe against existing data, write site/data/feed.json."""
import json
import os
from datetime import datetime
from email.utils import parsedate_to_datetime

from feeds import fetch_all

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "site", "data", "feed.json")


def normalize_date(raw):
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw


def main():
    items = fetch_all()
    for item in items:
        item["published_iso"] = normalize_date(item["published"])

    existing = []
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f)

    seen = {(i["agency"], i["link"]) for i in existing}
    merged = existing + [i for i in items if (i["agency"], i["link"]) not in seen]
    merged.sort(key=lambda i: i.get("published_iso") or "", reverse=True)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"[{datetime.now().isoformat()}] wrote {len(merged)} items ({len(items)} fetched this run) to {OUT_PATH}")


if __name__ == "__main__":
    main()
