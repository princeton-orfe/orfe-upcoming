"""Event enrichment utilities.

Currently supports fetching an event subtitle (<div class="event-subtitle">)
from each event's detail page URL and inserting it into the `title` field.

Opt-in via CLI flag --enrich-titles or environment variable ENRICH_TITLES=1.
Network failures or parsing misses leave the existing title unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
import os
import requests
from bs4 import BeautifulSoup  # type: ignore


DEFAULT_TIMEOUT = 15


@dataclass
class TitleEnrichmentStats:
    attempted: int = 0
    updated: int = 0
    skipped_missing_url: int = 0
    errors: int = 0


def fetch_subtitle(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch a page and return normalized subtitle text.

    Adds a desktop User-Agent to avoid 403 responses and collapses internal
    whitespace/newlines to single spaces.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, timeout=timeout, headers=headers)
    # If site still blocks, return empty silently (caller treats as miss)
    try:
        resp.raise_for_status()
    except Exception:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    div = soup.find("div", class_="event-subtitle")
    if not div:
        return ""
    # get_text with separator to retain spacing, then collapse any runs
    raw = div.get_text(separator=" ", strip=True)
    normalized = " ".join(raw.split())
    return normalized


def enrich_titles(events: List[Dict], enable: bool, session_cache: Optional[Dict[str, str]] = None) -> TitleEnrichmentStats:
    """Mutate events list in-place adding subtitle to 'title' when available.

    Args:
        events: list of event dicts with 'urlRef'.
        enable: if False, no-op.
        session_cache: optional dict for caching url->subtitle.
    Returns:
        TitleEnrichmentStats summarizing operation.
    """
    stats = TitleEnrichmentStats()
    if not enable:
        return stats
    cache = session_cache if session_cache is not None else {}
    for ev in events:
        url = ev.get("urlRef") or ""
        if not url:
            stats.skipped_missing_url += 1
            continue
        stats.attempted += 1
        if url in cache:
            subtitle = cache[url]
        else:
            try:
                subtitle = fetch_subtitle(url)
            except Exception:
                stats.errors += 1
                cache[url] = ""
                continue
            cache[url] = subtitle
        if subtitle:
            # Only update if existing placeholder empty
            if not ev.get("title"):
                ev["title"] = subtitle
                stats.updated += 1
    return stats


def enrichment_enabled(cli_flag: bool) -> bool:
    if cli_flag:
        return True
    return os.getenv("ENRICH_TITLES", "0") in {"1", "true", "yes", "on"}
