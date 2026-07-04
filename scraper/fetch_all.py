"""Orchestrate Phase 2 ingestion sources."""

from sources import congress, federal_register, regulations_gov, rss, scrape


def fetch_all():
    items = []
    for source in (rss, federal_register, regulations_gov, congress, scrape):
        try:
            items.extend(source.fetch_all())
        except Exception as e:
            print(f"[warn] source {source.__name__}: {e}")
    return items
