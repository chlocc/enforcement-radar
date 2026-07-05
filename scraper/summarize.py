"""Fetch AI summaries for feed items that don't have one yet.

Uses Claude to produce a 2-sentence briefing-style summary for each item.
Skips items that already have an `ai_summary` field set.
Persists results back to feed.json after each batch so a partial run isn't lost.
"""

import os
import re
import sys
import time

import anthropic
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EnforcementRadar/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

PROMPT = (
    "You are a regulatory lawyer doing your morning briefing. "
    "In exactly 2 sentences, summarize this regulatory document: "
    "what it is, which agency issued it, and what it requires, changes, or signals. "
    "Be concrete and precise. Do not start with 'This document'."
)

MAX_CHARS = 12_000
RATE_SLEEP = 1.5


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _fetch_text(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "html" not in ct and "text" not in ct:
            return None
        return _strip_html(resp.text)[:MAX_CHARS]
    except Exception as e:
        print(f"  [fetch] {url[:60]}… error: {e}")
        return None


def _summarize(client: anthropic.Anthropic, title: str, body: str) -> str | None:
    content = f"Title: {title}\n\n{body}"
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": f"{PROMPT}\n\n{content}"}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"  [claude] error: {e}")
        return None


def fetch_summaries(items: list[dict], out_path: str) -> list[dict]:
    """Add `ai_summary` to items that lack one. Writes incrementally to out_path."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[summarize] skipped — set ANTHROPIC_API_KEY to enable AI summaries")
        return items

    client = anthropic.Anthropic(api_key=api_key)
    import json

    needed = [i for i in items if not i.get("ai_summary") and i.get("link")]
    print(f"[summarize] {len(needed)} items need summaries ({len(items) - len(needed)} already have one)")

    for idx, item in enumerate(needed, 1):
        title = item.get("title", "")
        url = item["link"]
        print(f"  [{idx}/{len(needed)}] {title[:70]}…")

        body = _fetch_text(url)
        if not body:
            item["ai_summary"] = None
            continue

        summary = _summarize(client, title, body)
        item["ai_summary"] = summary
        print(f"    → {summary[:100]}…" if summary else "    → (no summary)")

        # Persist after every item so partial runs aren't lost
        with open(out_path, "w") as f:
            json.dump(items, f, indent=2)

        time.sleep(RATE_SLEEP)

    print(f"[summarize] done — {sum(1 for i in items if i.get('ai_summary'))} items have summaries")
    return items
