from src.enrich import fill_title_fallback


def test_fill_title_fallback_blank_and_tbd():
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
