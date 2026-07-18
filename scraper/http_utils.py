"""Shared HTTP helpers for scraper sources."""

import os

# SEC and other .gov sites block generic bot user agents.
USER_AGENT = "EnforcementRadar/1.0 (regulatory tracker; contact: chlocc@users.noreply.github.com)"
HEADERS = {"User-Agent": USER_AGENT}


def api_key(env_var: str, default: str = "DEMO_KEY") -> str:
    """Read an API key from the environment, treating empty strings as unset."""
    return os.environ.get(env_var) or default
