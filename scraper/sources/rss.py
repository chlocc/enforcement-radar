"""RSS feed ingestion."""

import feedparser
import requests

from keywords import matches_tracker_item
from normalize import make_item

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}

FEEDS = [
    {"agency": "SEC", "source_id": "sec-press", "url": "https://www.sec.gov/news/pressreleases.rss"},
    {"agency": "SEC", "source_id": "sec-speeches", "url": "https://www.sec.gov/news/speeches-statements.rss"},
    {"agency": "CFTC", "source_id": "cftc-press", "url": "https://www.cftc.gov/RSS/RSSGP/rssgp.xml"},
    {"agency": "CFTC", "source_id": "cftc-enforcement", "url": "https://www.cftc.gov/taxonomy/term/111/feed"},
    {"agency": "CFTC", "source_id": "cftc-speeches", "url": "https://www.cftc.gov/RSS/RSSST/rssst.xml"},
    {"agency": "CFPB", "source_id": "cfpb-newsroom", "url": "https://www.consumerfinance.gov/about-us/newsroom/feed/"},
    {"agency": "DOJ", "source_id": "doj-opa", "url": "https://www.justice.gov/news/rss?type=press_release&m=opa"},
    {"agency": "FTC", "source_id": "ftc-press", "url": "https://www.ftc.gov/feeds/press-release.xml"},
    {"agency": "OCC", "source_id": "occ-news", "url": "https://www.occ.gov/rss/occ_news.xml"},
    {"agency": "OCC", "source_id": "occ-bulletins", "url": "https://www.occ.gov/rss/occ_bulletins.xml"},
    {"agency": "Federal Reserve", "source_id": "fed-banking", "url": "https://www.federalreserve.gov/feeds/bankinginfo-rss.xml"},
    {"agency": "FDIC", "source_id": "fdic-fil", "url": "https://public.govdelivery.com/topics/USFDIC_19/feed.rss"},
    {"agency": "FDIC", "source_id": "fdic-press", "url": "https://public.govdelivery.com/topics/USFDIC_26/feed.rss"},
]


def fetch_feed(feed):
    resp = requests.get(feed["url"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    items = []
    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        if not title or not link:
            continue
        summary = entry.get("summary", "")
        candidate = {"title": title, "summary": summary}
        if not matches_tracker_item(candidate):
            continue
        items.append(
            make_item(
                agency=feed["agency"],
                title=title,
                link=link,
                published=entry.get("published", entry.get("updated", "")),
                source_id=feed["source_id"],
                external_id=entry.get("id", link),
                summary=summary[:500] if summary else None,
            )
        )
    return items


def fetch_all():
    items = []
    for feed in FEEDS:
        try:
            batch = fetch_feed(feed)
            items.extend(batch)
            print(f"[rss] {feed['source_id']}: {len(batch)} items")
        except Exception as e:
            print(f"[warn] rss {feed['source_id']}: {e}")
    return items
