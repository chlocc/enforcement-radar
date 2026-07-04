"""Fetch all agency feeds, normalize dates, dedupe, prune, write site/data/feed.json."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from fetch_all import fetch_all as fetch_sources
from normalize import dedupe_key, normalize_date

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "site", "data", "feed.json")
RETENTION_DAYS = 30


def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _parse_iso(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(raw)
        except Exception:
            return None


def main():
    _load_env()
    items = fetch_sources()
    for item in items:
        if not item.get("published_iso"):
            item["published_iso"] = normalize_date(item.get("published", ""))

    existing = []
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f)

    seen = {dedupe_key(i) for i in existing}
    merged = existing + [i for i in items if dedupe_key(i) not in seen]

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    pruned = []
    for item in merged:
        dt = _parse_iso(item.get("published_iso"))
        if dt is None:
            pruned.append(item)
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt >= cutoff:
            pruned.append(item)

    pruned.sort(key=lambda i: i.get("published_iso") or "", reverse=True)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(pruned, f, indent=2)

    print(
        f"[{datetime.now().isoformat()}] wrote {len(pruned)} items "
        f"({len(items)} fetched this run, {len(merged) - len(pruned)} pruned >{RETENTION_DAYS}d) "
        f"to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
