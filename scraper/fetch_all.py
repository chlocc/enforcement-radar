"""Orchestrate Phase 2 ingestion sources (Congress.gov on hold)."""

from sources import federal_register, regulations_gov, rss, scrape

# Congress.gov disabled until CONGRESS_API_KEY is configured.
# from sources import congress


def fetch_all():
    items = []
    for source in (rss, federal_register, regulations_gov, scrape):
        try:
            items.extend(source.fetch_all())
        except Exception as e:
            print(f"[warn] source {source.__name__}: {e}")
    return items
