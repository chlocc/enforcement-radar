"""Fetch AI summaries for feed items that don't have one yet.

Uses OpenRouter to produce a 2-sentence briefing-style summary for each item.
Skips items that already have an `ai_summary` field set.
Persists results back to feed.json after each batch so a partial run isn't lost.
"""

import json
import os
import re
import time

import requests

from http_utils import HEADERS

PROMPT = (
    "You are a regulatory lawyer doing your morning briefing. "
    "In exactly 2 sentences, summarize this regulatory document: "
    "what it is, which agency issued it, and what it requires, changes, or signals. "
    "Be concrete and precise. Do not start with 'This document'."
)

MAX_CHARS = 12_000
RATE_SLEEP = 1.5
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _fetch_text(url: str) -> str | None:
    try:
        resp = requests.get(
            url,
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "html" not in ct and "text" not in ct:
            return None
        return _strip_html(resp.text)[:MAX_CHARS]
    except Exception as e:
        print(f"  [fetch] {url[:60]}… error: {e}")
        return None


def _summarize(api_key: str, model: str, title: str, body: str) -> tuple[str | None, str | None]:
    content = f"Title: {title}\n\n{body}"
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chlocc.github.io/enforcement-radar/",
                "X-OpenRouter-Title": "Enforcement Radar",
            },
            json={
                "model": model,
                "max_tokens": 220,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": f"{PROMPT}\n\n{content}"}],
            },
            timeout=60,
        )
        if resp.status_code in (401, 402, 403):
            detail = resp.text[:300]
            raise RuntimeError(f"openrouter_auth: {detail}")
        if resp.status_code == 429:
            print("  [openrouter] rate limited; stopping this run")
            raise RuntimeError("openrouter_rate_limit")
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            print("  [openrouter] response contained no choices")
            return None, data.get("model")
        summary = (choices[0].get("message", {}).get("content") or "").strip()
        return summary or None, data.get("model")
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        print(f"  [openrouter] error: {e}")
        return None, None


def fetch_summaries(items: list[dict], out_path: str) -> list[dict]:
    """Add `ai_summary` to items that lack one. Writes incrementally to out_path."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[summarize] skipped — set OPENROUTER_API_KEY to enable AI summaries")
        return items

    model = os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    needed = [i for i in items if not i.get("ai_summary") and i.get("link")]
    print(
        f"[summarize] {len(needed)} items need summaries "
        f"({len(items) - len(needed)} already have one); model={model}"
    )

    for idx, item in enumerate(needed, 1):
        title = item.get("title", "")
        url = item["link"]
        print(f"  [{idx}/{len(needed)}] {title[:70]}…")

        body = _fetch_text(url) or item.get("summary")
        if not body:
            item["ai_summary"] = None
            continue

        try:
            summary, resolved_model = _summarize(api_key, model, title, body)
        except RuntimeError as e:
            if str(e) == "openrouter_rate_limit":
                break
            if str(e).startswith("openrouter_auth:"):
                print(f"[summarize] stopped — OpenRouter rejected the API key: {str(e).split(': ', 1)[-1]}")
                break
            raise

        item["ai_summary"] = summary
        if summary:
            item["ai_provider"] = "OpenRouter"
            item["ai_model"] = resolved_model or model
        print(f"    → {summary[:100]}…" if summary else "    → (no summary)")

        # Persist after every item so partial runs aren't lost
        with open(out_path, "w") as f:
            json.dump(items, f, indent=2)

        time.sleep(RATE_SLEEP)

    print(f"[summarize] done — {sum(1 for i in items if i.get('ai_summary'))} items have summaries")
    return items
