import os
from src.enrich import fill_title_fallback


def test_fill_title_fallback_blank_and_tbd(monkeypatch):
    # Ensure no prefix from environment interferes with baseline expectations
    monkeypatch.delenv("FALLBACK_PREPEND_TEXT", raising=False)
    events = [
        {"guid": "1", "speaker": "Alice", "title": ""},
        {"guid": "2", "speaker": "Bob", "title": "  TBD  "},
        {"guid": "3", "speaker": "Carol", "title": None},
        {"guid": "4", "speaker": "Dave", "title": "Existing"},
        {"guid": "5", "speaker": "", "title": ""},  # no speaker -> unchanged
    ]
    filled = fill_title_fallback(events, overwrite=False)
    assert filled == 3
    assert events[0]["title"] == "Alice"
    assert events[1]["title"] == "Bob"
    assert events[2]["title"] == "Carol"
    assert events[3]["title"] == "Existing"
    assert events[4]["title"] == ""


def test_fill_title_fallback_with_prefix(monkeypatch):
    monkeypatch.setenv("FALLBACK_PREPEND_TEXT", "Seminar:")
    events = [
        {"guid": "1", "speaker": "Alice", "title": ""},
    ]
    filled = fill_title_fallback(events, overwrite=False)
    assert filled == 1
    assert events[0]["title"] == "Seminar: Alice"


def test_fill_title_fallback_with_overlong_prefix(monkeypatch):
    monkeypatch.setenv("FALLBACK_PREPEND_TEXT", "X" * 500)
    events = [
        {"guid": "1", "speaker": "Alice", "title": None},
    ]
    filled = fill_title_fallback(events, overwrite=False)
    assert filled == 1
    # Overlong prefix should be ignored
    assert events[0]["title"] == "Alice"


def test_fill_title_fallback_with_series_placeholder(monkeypatch):
    # Template includes {series}; should insert value and collapse spaces if missing
    monkeypatch.setenv("FALLBACK_PREPEND_TEXT", "A {series} Talk by")
    events = [
        {"guid": "1", "speaker": "Alice", "title": "", "series": "Optimization Seminar"},
        {"guid": "2", "speaker": "Bob", "title": "", "series": ""},
        {"guid": "3", "speaker": "Carol", "title": ""},  # no series key
    ]
    filled = fill_title_fallback(events, overwrite=False)
    assert filled == 3
    assert events[0]["title"] == "A Optimization Seminar Talk by Alice"
    # For missing/blank series, ensure we don't get double spaces
    assert events[1]["title"] == "A Talk by Bob"
    assert events[2]["title"] == "A Talk by Carol"
