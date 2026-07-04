"""Keyword lists and topic matching for the enforcement-radar feed."""

import re

DIGITAL_ASSET_KEYWORDS = [
    "digital asset",
    "digital assets",
    "cryptocurrency",
    "crypto",
    "virtual currency",
    "convertible virtual currency",
    "stablecoin",
    "payment stablecoin",
    "non-fungible",
    "nft",
    "blockchain",
    "distributed ledger",
    "web3",
    "defi",
    "decentralized finance",
    "smart contract",
    "bitcoin",
    "ethereum",
    "digital commodity",
    "crypto exchange",
    "digital asset exchange",
    "crypto custody",
    "mixer",
    "tumbler",
    "clarity act",
    "market clarity",
    "kiosk operator",
    "broker reporting",
    "form 1099-da",
    "staking reward",
    "initial coin offering",
    "crypto-asset",
    "crypto asset",
    "huione",
    "virtual asset",
    "fintech",
    "token offering",
    "digital token",
    "crypto broker",
    "crypto asset service",
]

AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "large language model",
    "generative ai",
    "gen ai",
    "generative artificial intelligence",
    "automated decision",
    "robo-adviser",
    "robo adviser",
    "chatbot",
    "predictive model",
    "model risk",
    "ai labeling",
    "ai sovereignty",
    "ai data center",
    "ai utilization",
    "ai-powered",
    "ai system",
    "ai tool",
    "ai service",
    "artificial intelligence act",
    "deepfake",
]

GENIUS_STABLECOIN_KEYWORDS = [
    "genius act",
    "genius",
    "payment stablecoin act",
    "stablecoin legislation",
    "stablecoin regulation",
    "stablecoin bill",
    "stablecoin framework",
    "stablecoin issuer",
    "stablecoin reserve",
    "stablecoin oversight",
]

DERIVATIVES_KEYWORDS = [
    "derivative",
    "derivatives",
    "swap",
    "swaps",
    "security-based swap",
    "uncleared swap",
    "swap dealer",
    "major swap participant",
    "swap execution facility",
    "futures contract",
    "margin requirement",
    "portfolio margining",
    "cross-margin",
    "central counterparty",
    "clearing requirement",
    "algorithmic trading",
    "position limit",
    "isda",
    "dodd-frank",
]

COMMODITIES_KEYWORDS = [
    "commodity futures",
    "commodity exchange act",
    "designated contract market",
    "derivatives clearing organization",
    "futures commission merchant",
    "event contract",
    "prediction market",
    "kalshi",
    "polymarket",
    "off-exchange",
    "leveraged retail",
    "eligible contract participant",
    "commodity pool",
    "commodity trading advisor",
    "insider trading in event",
    "event-based contract",
    "binary option",
    "digital commodity",
    "perpetual futures",
    "perpetual-style",
]

EXCLUDED_TITLE_PATTERNS = [
    "medical device",
    "radiology",
    "biofuel",
    "agricultural",
    "feedstock",
    "food and drug",
    "environmental protection",
    "fish and wildlife",
    "wildlife service",
    "national park",
]

WORD_BOUNDARY_KEYWORDS = {
    "btc", "eth", "cvc", "defi", "ico", "bsa", "ai", "ecp", "dcm", "dco", "fcm", "sef", "ccp", "cta",
    "genius", "swap", "swaps", "nft", "crypto",
}


def _haystack(text):
    return f" {text.lower()} "


def _has_keyword(text, keyword):
    kw = keyword.lower().strip()
    if not kw:
        return False
    if kw in WORD_BOUNDARY_KEYWORDS or (len(kw) <= 4 and " " not in kw):
        return bool(re.search(rf"\b{re.escape(kw)}\b", text.lower()))
    return kw in _haystack(text)


def _matches_any(text, keywords):
    return any(_has_keyword(text, kw) for kw in keywords)


def matches_digital_assets(text):
    return _matches_any(text, DIGITAL_ASSET_KEYWORDS)


def matches_ai(text):
    haystack = _haystack(text)
    if " ai " in haystack or haystack.startswith("ai ") or " ai." in haystack:
        return True
    return _matches_any(text, AI_KEYWORDS)


def matches_genius_stablecoin(text):
    return _matches_any(text, GENIUS_STABLECOIN_KEYWORDS)


def matches_derivatives(text):
    return _matches_any(text, DERIVATIVES_KEYWORDS)


def matches_commodities(text):
    return _matches_any(text, COMMODITIES_KEYWORDS)


def matches_tracker_topics(text):
    """True when text belongs to any tracked topic bucket."""
    return (
        matches_digital_assets(text)
        or matches_ai(text)
        or matches_genius_stablecoin(text)
        or matches_derivatives(text)
        or matches_commodities(text)
    )


def matches_tracker_item(item):
    """Match on title only so summary mentions of agency names do not create false positives."""
    title = item.get("title") or ""
    title_lower = title.lower()
    if any(pattern in title_lower for pattern in EXCLUDED_TITLE_PATTERNS):
        return False
    return matches_tracker_topics(title)


def item_text(item):
    return f"{item.get('title') or ''} {item.get('summary') or ''}"
