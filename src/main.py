"""Core module to fetch an ICS feed, (optionally) manipulate it, and emit events.json.

Flask was removed; JSON delivery now happens by committing / publishing the generated
file (e.g. via GitHub Action artifact or GitHub Pages). A tiny helper to optionally
serve the file locally via `python -m http.server` can be used if desired.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import requests
from ics import Calendar
from .transform import transform_calendar, TransformConfig

ICS_URL = os.getenv("ICS_URL", "https://example.com/calendar.ics")
REPO_VARIABLE = os.getenv("REPO_VARIABLE", "default")
OUTPUT_FILE_ENV = os.getenv("OUTPUT_FILE", "events.json")


def fetch_ics(url: str) -> str:
    """Download raw ICS text from the given URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def manipulate_data(calendar: Calendar, variable: str) -> Calendar:
    """Placeholder for domain-specific event manipulation.

    Currently passes calendar through unchanged.
    """
    # TODO: Implement data manipulation logic
    _ = variable  # keep reference to show intended use
    return calendar


def calendar_to_json(calendar: Calendar) -> list[dict]:  # legacy fallback
    return transform_calendar(calendar)


def generate_events_json(
    ics_url: str = ICS_URL,
    repo_variable: str = REPO_VARIABLE,
    output_path: str | os.PathLike = "events.json",
) -> Path:
    """Fetch, manipulate and write events JSON.

    Returns the Path to the written file.
    """
    raw = fetch_ics(ics_url)
    calendar = Calendar(raw)
    manipulated = manipulate_data(calendar, repo_variable)
    # Apply transformation config (future: load custom config)
    cfg = TransformConfig()
    data = transform_calendar(manipulated, cfg)
    out_path = Path(output_path)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate events.json from an ICS feed")
    p.add_argument("--ics-url", default=ICS_URL, help="ICS feed URL (env ICS_URL overrides)")
    p.add_argument(
        "--repo-variable",
        default=REPO_VARIABLE,
        help="Arbitrary repo variable used during manipulation",
    )
    p.add_argument(
        "--output",
        default=OUTPUT_FILE_ENV,
        help="Output JSON filepath (default comes from env OUTPUT_FILE or 'events.json')",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    path = generate_events_json(ns.ics_url, ns.repo_variable, ns.output)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
