from unittest.mock import patch
from pathlib import Path
import json
from src import main

ICS_SAMPLE = (
    "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test Corp//Test Calendar 1.0//EN\nBEGIN:VEVENT\nSUMMARY:Test Event\n"
    "DTSTART:20250915T120000Z\nDTEND:20250915T130000Z\nDESCRIPTION:Sample\nEND:VEVENT\nEND:VCALENDAR"
)

ICS_WITH_SERIES = (
    "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test Corp//Test Calendar 1.0//EN\n"
    "BEGIN:VEVENT\nUID:uid-1\nSUMMARY:Keep Event\nDTSTART:20250915T120000Z\nDTEND:20250915T130000Z\nCATEGORIES:Keep Me\nEND:VEVENT\n"
    "BEGIN:VEVENT\nUID:uid-2\nSUMMARY:Drop Event\nDTSTART:20250916T120000Z\nDTEND:20250916T130000Z\nCATEGORIES:FPO\nEND:VEVENT\n"
    "END:VCALENDAR"
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
    assert "guid" in data[0]
    out.unlink()


@patch("src.main.fetch_ics", return_value=ICS_WITH_SERIES)
def test_generate_events_json_excludes_series_via_env(mock_fetch, monkeypatch, tmp_path):  # noqa: ARG001
    target = tmp_path / "filtered_events.json"
    monkeypatch.setenv("EXCLUDE_SERIES", "FPO")
    written = main.generate_events_json(
        ics_url="unused", repo_variable="var", output_path=target
    )
    data = json.loads(written.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["series"] == "Keep Me"


@patch("src.main.fetch_ics", return_value=ICS_WITH_SERIES)
def test_main_cli_exclude_series_flag(mock_fetch, monkeypatch, capsys):  # noqa: ARG001
    monkeypatch.delenv("EXCLUDE_SERIES", raising=False)
    exit_code = main.main([
        "--ics-url",
        "unused",
        "--exclude-series",
        "FPO",
        "--print-only",
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "removed 1 events" in captured.err
    json_payload = captured.out[captured.out.find("[") :].strip()
    data = json.loads(json_payload)
    assert len(data) == 1
    assert data[0]["series"] == "Keep Me"
