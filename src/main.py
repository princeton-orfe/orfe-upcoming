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
from .transform import transform_calendar, TransformConfig, load_config

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
    p.add_argument(
        "--config",
        default=None,
        help="Optional path to JSON transform config (default: transform_config.json if present)",
    )
    p.add_argument(
        "--print-only",
        action="store_true",
        help="Print transformed JSON to stdout instead of writing file",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of events in output (for local iteration)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    # Determine config path fallback
    config_path = ns.config or ("transform_config.json" if os.path.exists("transform_config.json") else None)
    raw = fetch_ics(ns.ics_url)
    calendar = Calendar(raw)
    manipulated = manipulate_data(calendar, ns.repo_variable)
    cfg = load_config(config_path)
    data = transform_calendar(manipulated, cfg)
    if ns.limit is not None:
        data = data[: ns.limit]
    if ns.print_only:
        print(json.dumps(data, indent=2))
        return 0
    out_path = Path(ns.output)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(data)} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
