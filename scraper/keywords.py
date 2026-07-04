"""Keyword lists for topic matching."""

DIGITAL_ASSET_KEYWORDS = [
    "digital asset",
    "digital assets",
    "cryptocurrency",
    "crypto",
    "virtual currency",
    "convertible virtual currency",
    "cvc",
    "stablecoin",
    "payment stablecoin",
    "token",
    "nft",
    "non-fungible",
    "blockchain",
    "distributed ledger",
    "web3",
    "defi",
    "decentralized finance",
    "smart contract",
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "digital commodity",
    "crypto exchange",
    "digital asset exchange",
    "custody",
    "crypto custody",
    "wallet",
    "mixer",
    "tumbler",
    "clarity act",
    "genius act",
    "market clarity",
    "bank secrecy act",
    "bsa",
    "kiosk operator",
    "broker reporting",
    "form 1099-da",
    "staking reward",
    "ponzi",
    "initial coin offering",
    "ico",
    "bank-fintech",
    "fintech",
    "crypto-asset",
    "crypto asset",
    "huione",
    "virtual asset",
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
    "algorithmic",
    "automated decision",
    "automated trading",
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
    "active listening",
    "deepfake",
    " a.i.",
]


def _haystack(text):
    return f" {text.lower()} "


def matches_digital_assets(text):
    return any(kw in _haystack(text) for kw in DIGITAL_ASSET_KEYWORDS)


def matches_ai(text):
    haystack = _haystack(text)
    if " ai " in haystack or haystack.startswith("ai ") or " ai." in haystack:
        return True
    return any(kw in haystack for kw in AI_KEYWORDS if kw != " a.i.")
