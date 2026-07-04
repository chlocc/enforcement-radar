"""HTML scrapers for OFAC, FinCEN, and IRS digital-asset sources."""

import re
from datetime import datetime
from urllib.parse import urljoin

import requests

from keywords import matches_digital_assets
from normalize import make_item

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}


def _parse_ofac_date(text):
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})", text)
    if not m:
        return ""
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def fetch_ofac():
    base = "https://ofac.treasury.gov"
    resp = requests.get(f"{base}/recent-actions", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = []
    for path, date_key, title in re.findall(
        r'href="(/recent-actions/(\d{8})(?:_\d+)?)"[^>]*>([^<]+)</a>',
        resp.text,
    ):
        if path.endswith(("regulations-and-guidance", "sanctions-list-updates")):
            continue
        title = re.sub(r"\s+", " ", title).strip()
        if not matches_digital_assets(title):
            continue
        try:
            published = datetime.strptime(date_key, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            published = _parse_ofac_date(title)
        items.append(
            make_item(
                agency="OFAC",
                title=title,
                link=urljoin(base, path),
                published=published,
                source_id="ofac-recent-actions",
                external_id=path,
                development_type="sanctions",
            )
        )
    print(f"[scrape] ofac-recent-actions: {len(items)} items")
    return items


def fetch_fincen_press():
    base = "https://www.fincen.gov"
    resp = requests.get(f"{base}/news/press-releases", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = []
    for block in re.findall(r'<div class="fincen-news-article">(.*?)</div>\s*</div>', resp.text, re.S):
        time_m = re.search(r'<time datetime="([^"]+)"', block)
        link_m = re.search(r'class="fincen-news-article__title"><a href="([^"]+)"[^>]*>([^<]+)</a>', block)
        if not link_m:
            continue
        path, title = link_m.group(1), re.sub(r"\s+", " ", link_m.group(2)).strip()
        if not matches_digital_assets(title):
            continue
        published = time_m.group(1) if time_m else ""
        items.append(
            make_item(
                agency="FinCEN",
                title=title,
                link=urljoin(base, path),
                published=published,
                source_id="fincen-press",
                external_id=path,
            )
        )
    print(f"[scrape] fincen-press: {len(items)} items")
    return items


def fetch_fincen_advisories():
    base = "https://www.fincen.gov"
    resp = requests.get(f"{base}/resources/advisoriesbulletinsfact-sheets/advisories", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = []
    for path, title, date_text in re.findall(
        r'<tr>.*?<td[^>]*>.*?<a href="([^"]+)"[^>]*>([^<]+)</a>.*?<td[^>]*>([^<]+)</td>',
        resp.text,
        re.S,
    ):
        title = re.sub(r"\s+", " ", title).strip()
        if not matches_digital_assets(title):
            continue
        date_text = re.sub(r"\s+", " ", date_text).strip()
        try:
            published = datetime.strptime(date_text, "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            published = date_text
        items.append(
            make_item(
                agency="FinCEN",
                title=title,
                link=urljoin(base, path),
                published=published,
                source_id="fincen-advisories",
                external_id=path,
                development_type="advisory",
            )
        )
    print(f"[scrape] fincen-advisories: {len(items)} items")
    return items


def fetch_irs_digital_assets():
    base = "https://www.irs.gov"
    resp = requests.get(f"{base}/filing/digital-assets", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = []
    seen = set()
    for path, title in re.findall(r'<a href="([^"]+)"[^>]*>([^<]{8,120})</a>', resp.text):
        title = re.sub(r"\s+", " ", title).strip()
        if path.startswith("#") or "determine how" in title.lower():
            continue
        if not any(k in title.lower() for k in ("revenue", "notice", "ruling", "procedure", "regulation", "fact sheet", "news release", "ir-")):
            if not matches_digital_assets(title):
                continue
        link = urljoin(base, path)
        if link in seen:
            continue
        seen.add(link)
        items.append(
            make_item(
                agency="IRS",
                title=title,
                link=link,
                published="",
                source_id="irs-digital-assets",
                external_id=path,
                development_type="guidance",
            )
        )
    print(f"[scrape] irs-digital-assets: {len(items)} items")
    return items


def fetch_all():
    items = []
    for fn in (fetch_ofac, fetch_fincen_press, fetch_fincen_advisories, fetch_irs_digital_assets):
        try:
            items.extend(fn())
        except Exception as e:
            print(f"[warn] {fn.__name__}: {e}")
    return items
