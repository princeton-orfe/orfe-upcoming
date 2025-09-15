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
    """Fetch a page and return the first .event-subtitle div text (stripped)."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    div = soup.find("div", class_="event-subtitle")
    if not div:
        return ""
    text = div.get_text(separator=" ", strip=True)
    return text or ""


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
