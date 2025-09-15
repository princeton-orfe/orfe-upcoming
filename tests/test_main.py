from unittest.mock import patch
from pathlib import Path
import json
from src import main

ICS_SAMPLE = (
    "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test Corp//Test Calendar 1.0//EN\nBEGIN:VEVENT\nSUMMARY:Test Event\n"
    "DTSTART:20250915T120000Z\nDTEND:20250915T130000Z\nDESCRIPTION:Sample\nEND:VEVENT\nEND:VCALENDAR"
)


@patch("src.main.requests.get")
def test_fetch_ics(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = ICS_SAMPLE
    result = main.fetch_ics("http://fake.url")
    assert "BEGIN:VCALENDAR" in result


@patch("src.main.manipulate_data")
def test_manipulate_data_success(mock_manipulate):
    calendar = main.Calendar(ICS_SAMPLE)
    mock_manipulate.return_value = calendar
    manipulated = main.manipulate_data(calendar, "test")
    assert manipulated == calendar


@patch("src.main.fetch_ics", return_value=ICS_SAMPLE)
def test_generate_events_json(mock_fetch):  # noqa: ARG001
    out = Path("test_events.json")
    if out.exists():
        out.unlink()
    written = main.generate_events_json(
        ics_url="unused", repo_variable="var", output_path=out
    )
    assert written.exists()
    data = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["name"] == "Test Event"
    out.unlink()
