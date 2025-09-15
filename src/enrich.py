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
        # Site-provided bypass header for bot protection (value optional)
        "x-wdsoit-bot-bypass": os.getenv("BOT_BYPASS_HEADER_VALUE", "1"),
    }
    debug = os.getenv("ENRICH_DEBUG") in {"1", "true", "yes", "on"}
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
    except Exception as e:
        if debug:
            print(f"[enrich] request-error url={url} err={e}")
        return ""
    try:
        resp.raise_for_status()
    except Exception as e:
        if debug:
            print(f"[enrich] bad-status url={url} code={getattr(resp,'status_code',None)} err={e}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    div = soup.find("div", class_="event-subtitle")
    if not div:
        if debug:
            print(f"[enrich] subtitle-missing url={url} length={len(resp.text)}")
        return ""
    # get_text with separator to retain spacing, then collapse any runs
    raw = div.get_text(separator=" ", strip=True)
    normalized = " ".join(raw.split())
    if debug:
        print(f"[enrich] subtitle-found url={url} len={len(normalized)}")
    return normalized


def enrich_titles(events: List[Dict], enable: bool, session_cache: Optional[Dict[str, str]] = None, overwrite: bool = False) -> TitleEnrichmentStats:
    """Mutate events list in-place adding subtitle to 'title' when available.

    Debugging:
        Set ENRICH_DEBUG=1 to emit detailed skip/update logging to stdout.

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
    debug = os.getenv("ENRICH_DEBUG") in {"1", "true", "yes", "on"}
    for idx, ev in enumerate(events):
        url = ev.get("urlRef") or ""
        if not url:
            stats.skipped_missing_url += 1
            if debug:
                print(f"[enrich] skip(no-url) event_index={idx}")
            continue
        stats.attempted += 1
        if url in cache:
            subtitle = cache[url]
            if debug:
                print(f"[enrich] cache-hit url={url} subtitle_len={len(subtitle)}")
        else:
            try:
                subtitle = fetch_subtitle(url)
            except Exception as e:
                stats.errors += 1
                cache[url] = ""
                if debug:
                    print(f"[enrich] error fetching url={url} err={e}")
                continue
            cache[url] = subtitle
            if debug:
                print(f"[enrich] fetched url={url} subtitle_len={len(subtitle)}")
        if not subtitle:
            if debug:
                print(f"[enrich] skip(no-subtitle) url={url}")
            continue
        existing = ev.get("title")
        # Decide whether to overwrite
        should_overwrite = overwrite or existing is None or str(existing).strip() == ""
        if should_overwrite:
            ev["title"] = subtitle
            stats.updated += 1
            if debug:
                action = "overwrote" if (existing and overwrite) else "updated"
                print(f"[enrich] {action} url={url} new_title_len={len(subtitle)}")
        else:
            if debug:
                snippet = str(existing)[:40].replace('\n', ' ')
                print(f"[enrich] skip(has-title) url={url} existing_snippet={snippet!r} overwrite={overwrite}")
    return stats


def enrichment_enabled(cli_flag: bool) -> bool:
    if cli_flag:
        return True
    return os.getenv("ENRICH_TITLES", "0") in {"1", "true", "yes", "on"}


def enrichment_overwrite_enabled(cli_flag: bool) -> bool:
    if cli_flag:
        return True
    return os.getenv("ENRICH_OVERWRITE", "0") in {"1", "true", "yes", "on"}


def fill_title_fallback(events: List[Dict], overwrite: bool = False) -> int:
    """Fill empty title from speaker field as a safety fallback.

    Returns number of titles filled. If overwrite=True, replaces non-empty titles.
    """
    count = 0
    for ev in events:
        speaker = ev.get("speaker")
        if not speaker:
            continue
        existing = ev.get("title")
        if overwrite or not existing or str(existing).strip() == "":
            ev["title"] = speaker
            count += 1
    return count
