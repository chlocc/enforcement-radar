"""Congress.gov API ingestion — digital-asset bills for the current Congress."""

import os
from datetime import datetime

import requests

from keywords import matches_digital_assets
from normalize import make_item

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)"}
API_BASE = "https://api.congress.gov/v3"
CURRENT_CONGRESS = 119


def _bill_label(bill):
    number = bill.get("number")
    bill_type = (bill.get("type") or "").upper()
    prefix = {"HR": "HR", "S": "S", "HJRES": "HJRES", "SJRES": "SJRES", "HRES": "HRES", "SRES": "SRES"}.get(
        bill_type, bill_type
    )
    title = bill.get("title") or ""
    if prefix and number:
        return f"{prefix} {number}—{title}"
    return title


def _chamber_label(bill):
    code = bill.get("originChamberCode") or ""
    if code == "H":
        return "U.S. House of Representatives"
    if code == "S":
        return "U.S. Senate"
    return bill.get("originChamber") or "Congress"


def fetch_all():
    api_key = os.environ.get("CONGRESS_API_KEY")
    if not api_key:
        print("[skip] congress-gov: set CONGRESS_API_KEY to ingest legislative bills")
        return []

    items = []
    offset = 0
    limit = 250

    while True:
        resp = requests.get(
            f"{API_BASE}/bill",
            params={
                "api_key": api_key,
                "format": "json",
                "congress": CURRENT_CONGRESS,
                "limit": limit,
                "offset": offset,
                "sort": "updateDate+desc",
            },
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        bills = data.get("bills", [])
        if not bills:
            break

        for bill in bills:
            title = _bill_label(bill)
            if not matches_digital_assets(title):
                continue
            congress = bill.get("congress", CURRENT_CONGRESS)
            bill_type = (bill.get("type") or "").lower()
            number = bill.get("number")
            link = bill.get("url") or f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}-bill/{number}"
            published = bill.get("updateDate") or bill.get("updateDateIncludingText") or ""
            items.append(
                make_item(
                    agency="Congress",
                    sub_agency=_chamber_label(bill),
                    title=title,
                    link=link,
                    published=published,
                    source_id="congress-gov",
                    external_id=f"{congress}-{bill_type}-{number}",
                    development_type="bill",
                )
            )

        pagination = data.get("pagination", {})
        if not pagination.get("next"):
            break
        offset += limit
        if offset >= 1000:
            break

    print(f"[congress] congress-gov: {len(items)} digital-asset bills")
    return items
