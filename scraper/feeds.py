"""Agency feed definitions and fetch logic for Enforcement Radar."""
import feedparser
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}

FEEDS = [
    {"agency": "SEC", "url": "https://www.sec.gov/news/pressreleases.rss"},
    {"agency": "CFTC", "url": "https://www.cftc.gov/RSS/RSSGP/rssgp.xml"},
    {"agency": "DOJ", "url": "https://www.justice.gov/news/rss?type=press_release&m=opa"},
]


def fetch_feed(agency, url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    items = []
    for entry in parsed.entries:
        items.append({
            "agency": agency,
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
        })
    return items


def fetch_all():
    items = []
    for feed in FEEDS:
        try:
            items.extend(fetch_feed(feed["agency"], feed["url"]))
        except Exception as e:
            print(f"[warn] failed to fetch {feed['agency']}: {e}")
    return items
