"""Normalize raw source records into the enforcement-radar feed schema."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

AGENCY_META = {
    "SEC": {"category_index": "securities", "jurisdiction": "federal"},
    "CFTC": {"category_index": "commodities", "jurisdiction": "federal"},
    "DOJ": {"category_index": "enforcement", "jurisdiction": "federal"},
    "FTC": {"category_index": "enforcement", "jurisdiction": "federal"},
    "Congress": {"category_index": "congress", "jurisdiction": "federal"},
    "OCC": {"category_index": "banking", "jurisdiction": "federal"},
    "Federal Reserve": {"category_index": "banking", "jurisdiction": "federal"},
    "FDIC": {"category_index": "banking", "jurisdiction": "federal"},
    "OFAC": {"category_index": "aml", "jurisdiction": "federal"},
    "FinCEN": {"category_index": "aml", "jurisdiction": "federal"},
    "IRS": {"category_index": "enforcement", "jurisdiction": "federal"},
    "Federal Register": {"category_index": "rulemaking", "jurisdiction": "federal"},
    "CFPB": {"category_index": "banking", "jurisdiction": "federal"},
}


def normalize_date(raw):
    if not raw:
        return ""
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=timezone.utc)
        return raw.isoformat()
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).isoformat()
        except Exception:
            return str(raw)


def infer_development_type(title, source_id=None):
    t = title.lower()
    if source_id == "congress-gov" or "—" in title and any(
        p in t for p in (" hr ", " s ", " h.r.", " h.j.res", " s.j.res")
    ):
        return "bill"
    if any(p in t for p in ("designation", "sdn", "sanctions list", "blocked")):
        return "sanctions"
    if "advisory" in t or "alert" in t:
        return "advisory"
    if "proposed rule" in t or "nprm" in t or "seek" in t and "comment" in t:
        return "proposed-rule"
    if "final rule" in t or "adopts rule" in t:
        return "final-rule"
    if any(p in t for p in ("indict", "charge", "enforcement", "settlement", "pleads")):
        return "enforcement"
    if any(p in t for p in ("revenue ruling", "revenue procedure", "notice 20")):
        return "guidance"
    if source_id in ("sec-speeches", "cftc-speeches"):
        return "guidance"
    if "hearing" in t:
        return "hearing"
    if "no-action" in t or "no action" in t:
        return "no-action"
    if "bulletin" in t or "sr " in t or "letter" in t or "speech" in t or "statement" in t:
        return "guidance"
    return "press"


def make_item(
    *,
    agency,
    title,
    link,
    published,
    source_id,
    external_id=None,
    sub_agency=None,
    development_type=None,
    summary=None,
):
    meta = AGENCY_META.get(agency, {"category_index": "enforcement", "jurisdiction": "federal"})
    published_iso = normalize_date(published)
    return {
        "agency": agency,
        "sub_agency": sub_agency,
        "jurisdiction": meta["jurisdiction"],
        "category_index": meta["category_index"],
        "development_type": development_type or infer_development_type(title, source_id),
        "source_id": source_id,
        "external_id": external_id or link,
        "title": title.strip(),
        "summary": summary,
        "link": link,
        "published": published if isinstance(published, str) else published_iso,
        "published_iso": published_iso,
    }


def dedupe_key(item):
    return (item.get("source_id") or item["agency"], item.get("external_id") or item["link"])
