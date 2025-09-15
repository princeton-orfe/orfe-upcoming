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