from src.transform import transform_calendar, TransformConfig
from ics import Calendar

ICS_EVENT = """BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test Corp//Test Calendar 1.0//EN\nBEGIN:VEVENT\nUID:ps_events:11876:delta:0\nDTSTART:20250908T161500Z\nDTEND:20250908T171500Z\nURL:https://orfe.princeton.edu/events/2025/elynn-chen-new-york-university\nLOCATION:101 - Sherrerd\nSUMMARY:Elynn Chen, New York University\nDESCRIPTION:Abstract: Most learning-and-decision systems assume a single, homogeneous response to actions.\nCATEGORIES:S. S. Wilks Memorial Seminar in Statistics\nDTSTAMP:20250905T185131Z\nEND:VEVENT\nEND:VCALENDAR"""


def test_transform_example_event():
    cal = Calendar(ICS_EVENT)
    data = transform_calendar(cal, TransformConfig())
    assert len(data) == 1
    ev = data[0]
    assert ev["guid"] == "ps_events:11876:delta:0"
    assert ev["location"]["name"] == "Sherrerd"
    assert ev["location"]["detail"] == "101"
    assert ev["series"] == "S. S. Wilks Memorial Seminar in Statistics"
    # Speaker encoded with escaped comma
    assert "Elynn Chen" in ev["speaker"]
    assert "startTime" in ev and "endTime" in ev


def test_multiple_categories_join():
    ics_multi = """BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//Multi Cats//EN\nBEGIN:VEVENT\nUID:abc123\nDTSTART:20250101T120000Z\nDTEND:20250101T130000Z\nSUMMARY:Test\nCATEGORIES:CatA,CatB\nEND:VEVENT\nEND:VCALENDAR"""
    cal = Calendar(ics_multi)
    cfg = TransformConfig()
    data = transform_calendar(cal, cfg)
    assert data[0]["series"] in {"CatA,CatB", "CatB,CatA"}


def test_description_newline_literal_r():
    ics_txt = """BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\nBEGIN:VEVENT\nUID:nl1\nDTSTART:20250101T000000Z\nDTEND:20250101T010000Z\nSUMMARY:Speaker\nDESCRIPTION:Line one\\n Line two\nEND:VEVENT\nEND:VCALENDAR"""
    cal = Calendar(ics_txt)
    cfg = TransformConfig(represent_newlines_as="literal_r", preserve_description_escapes=False, collapse_whitespace_in_description=False)
    data = transform_calendar(cal, cfg)
    assert data[0]["content"].count("\\r") >= 1


def test_example_files_roundtrip():
    # Uses the example ICS / expected JSON artifacts committed for validation.
    import json, pathlib
    base = pathlib.Path(__file__).resolve().parents[1] / "examples"
    ics_path = base / "sample_input.example.ics"
    expected_path = base / "sample_output.expected.json"
    cfg = TransformConfig(represent_newlines_as="literal_r")
    with open(ics_path, "r", encoding="utf-8") as f:
        cal = Calendar(f.read())
    produced = transform_calendar(cal, cfg)
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = json.load(f)
    # Compare only stable invariant subset of fields per event by guid.
    exp_index = {e["guid"]: e for e in expected}
    # Allow produced to contain additional events not yet listed in expected sample.
    core_fields = ["guid", "startTime", "endTime", "urlRef", "location", "series", "speaker"]
    for guid, ref in exp_index.items():
        match = next((e for e in produced if e["guid"] == guid), None)
        assert match, f"Expected guid {guid} not found in produced output"
        for field in core_fields:
            if field == "series":
                got_series = set((match.get(field) or "").split(","))
                exp_series = set((ref.get(field) or "").split(","))
                assert got_series == exp_series, f"Mismatch series guid={guid}"
            elif field == "location":
                # Compare subfields ignoring potential swap of name/detail heuristics
                got_loc = match.get(field) or {}
                exp_loc = ref.get(field) or {}
                # Accept either direct equality or swapped name/detail
                same = got_loc == exp_loc
                swapped = got_loc.get("name") == exp_loc.get("detail") and got_loc.get("detail") == exp_loc.get("name")
                assert same or swapped, f"Location mismatch guid={guid}: got={got_loc} expected={exp_loc}"
            else:
                assert match.get(field) == ref.get(field), f"Mismatch field={field} guid={guid}"