import json

from src import heartbeat


def test_decide_heartbeat_before_threshold():
    decision = heartbeat.decide_heartbeat(
        last_commit_epoch=0,
        now_epoch=34 * heartbeat.SECONDS_PER_DAY,
        threshold_days=35,
    )
    assert decision.should_write is False
    assert decision.age_days == 34


def test_decide_heartbeat_at_threshold():
    decision = heartbeat.decide_heartbeat(
        last_commit_epoch=0,
        now_epoch=35 * heartbeat.SECONDS_PER_DAY,
        threshold_days=35,
    )
    assert decision.should_write is True
    assert decision.age_days == 35


def test_build_payload_contains_expected_metadata():
    payload = heartbeat.build_payload(
        now_epoch=heartbeat.SECONDS_PER_DAY,
        last_commit_epoch=0,
        ref_name="main",
        source_sha="abc123",
        threshold_days=35,
    )
    assert payload == {
        "updatedAt": "1970-01-02T00:00:00Z",
        "previousCommitAt": "1970-01-01T00:00:00Z",
        "ref": "main",
        "sourceSha": "abc123",
        "thresholdDays": 35,
    }


def test_main_writes_heartbeat_file_when_threshold_exceeded(tmp_path, monkeypatch):
    output_file = tmp_path / ".ci" / "heartbeat.json"
    github_output = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(heartbeat.time, "time", lambda: 50 * heartbeat.SECONDS_PER_DAY)

    exit_code = heartbeat.main(
        [
            "--last-commit-epoch",
            "0",
            "--threshold-days",
            "35",
            "--ref-name",
            "main",
            "--source-sha",
            "deadbeef",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["ref"] == "main"
    assert payload["sourceSha"] == "deadbeef"
    assert "changed=true" in github_output.read_text(encoding="utf-8")


def test_main_skips_write_when_recent_activity(tmp_path, monkeypatch):
    output_file = tmp_path / ".ci" / "heartbeat.json"
    github_output = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(heartbeat.time, "time", lambda: 10 * heartbeat.SECONDS_PER_DAY)

    exit_code = heartbeat.main(
        [
            "--last-commit-epoch",
            "0",
            "--threshold-days",
            "35",
            "--ref-name",
            "main",
            "--source-sha",
            "deadbeef",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert output_file.exists() is False
    assert "changed=false" in github_output.read_text(encoding="utf-8")
