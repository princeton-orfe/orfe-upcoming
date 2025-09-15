"""ICS event transformation utilities.

Provides configurable mapping, masking, placeholder injection, and
time/location normalization for calendar events.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Iterable
import os
import re
import arrow  # type: ignore


@dataclass
class TransformConfig:
    target_timezone: str = os.getenv("TARGET_TZ", "America/New_York")
    time_format: str = "YYYY-MM-DDTHH:mm:ss"
    # Mapping from logical ICS attribute name -> output field name
    # NOTE: Summary intentionally mapped to 'speaker' per provided example, while 'title' left blank.
    field_mappings: Dict[str, str] = field(
        default_factory=lambda: {
            "uid": "guid",
            "begin": "startTime",
            "end": "endTime",
            "url": "urlRef",
            "categories": "series",
            "description": "content",
            "name": "speaker",  # ICS 'SUMMARY'
        }
    )
    # Fields from the raw event to ignore entirely
    masked_fields: Set[str] = field(
        default_factory=lambda: {"dtstamp", "sequence", "transp", "class"}
    )
    # Static placeholder values always added / overriding.
    placeholders: Dict[str, str] = field(
        default_factory=lambda: {
            "title": "",
            "cancelled": "",
            "bannerImage": "",
            "itemType": "advertisement",
        }
    )
    # Copy operations: new_field -> existing mapped field (post-mapping) to duplicate
    copies: Dict[str, str] = field(default_factory=dict)


def clean_text(value: str) -> str:
    if not value:
        return ""
    # Collapse whitespace produced by ICS line folding
    value = value.replace("\r", "\n")
    value = re.sub(r"\n+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def escape_commas(value: str) -> str:
    # Example output retains backslashes before commas, ensure we preserve them.
    return value.replace(",", "\\,")


def parse_location(raw: str | None) -> dict:
    if not raw:
        return {"name": "", "id": "", "detail": ""}
    parts = [p.strip() for p in raw.split("-", 1)]
    if len(parts) == 2:
        detail, name = parts
    else:
        detail = parts[0]
        name = ""
    return {"name": name, "id": "", "detail": detail}


def format_time(arrow_dt, cfg: TransformConfig) -> str:
    if arrow_dt is None:
        return ""
    try:
        localized = arrow_dt.to(cfg.target_timezone)
    except Exception:
        localized = arrow_dt
    return localized.format(cfg.time_format)


def transform_event(event, cfg: TransformConfig) -> dict:
    out: Dict[str, object] = {}

    # Map core fields
    for attr, target in cfg.field_mappings.items():
        if attr in cfg.masked_fields:
            continue
        val = getattr(event, attr, None)
        if val is None:
            continue
        if attr in {"begin", "end"}:
            out[target] = format_time(val, cfg)
        elif attr == "description":
            out[target] = clean_text(str(val))
        elif attr == "name":
            out[target] = escape_commas(str(val))
        elif attr == "categories":
            # ICS library returns a set
            if isinstance(val, (set, list, tuple)):
                out[target] = next(iter(val), "")
            else:
                out[target] = str(val)
        else:
            out[target] = str(val)

    # Location parsing
    out["location"] = parse_location(getattr(event, "location", None))

    # Placeholders
    for k, v in cfg.placeholders.items():
        out.setdefault(k, v)

    # Copy fields
    for new_field, source_field in cfg.copies.items():
        if source_field in out:
            out[new_field] = out[source_field]

    return out


def transform_calendar(calendar, cfg: TransformConfig | None = None) -> List[dict]:
    cfg = cfg or TransformConfig()
    events = [transform_event(ev, cfg) for ev in sorted(calendar.events, key=lambda e: e.begin or "")]
    return events
