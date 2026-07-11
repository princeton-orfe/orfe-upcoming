import pytest

from src import mirror_release


def test_build_release_payload_marks_latest_and_target():
    payload = mirror_release.build_release_payload(
        tag="latest",
        title="Latest Events",
        notes="body",
        latest=True,
        prerelease=False,
        target_commitish="main",
    )
    assert payload["tag_name"] == "latest"
    assert payload["name"] == "Latest Events"
    assert payload["body"] == "body"
    assert payload["make_latest"] == "true"
    assert payload["prerelease"] is False
    assert payload["target_commitish"] == "main"


def test_build_release_payload_marks_non_latest_release():
    payload = mirror_release.build_release_payload(
        tag="dev",
        title="Development Events",
        notes="body",
        latest=False,
        prerelease=True,
        target_commitish=None,
    )
    assert payload["make_latest"] == "false"
    assert payload["prerelease"] is True
    assert "target_commitish" not in payload


def test_build_upload_url_escapes_asset_names():
    upload_url = "https://uploads.github.com/repos/octo/repo/releases/1/assets{?name,label}"
    built = mirror_release.build_upload_url(upload_url, "events nofpo.json")
    assert built == "https://uploads.github.com/repos/octo/repo/releases/1/assets?name=events%20nofpo.json"


def test_resolve_token_prefers_target_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "source-token")
    monkeypatch.setenv("TARGET_GITHUB_TOKEN", "target-token")
    assert mirror_release.resolve_token() == "target-token"


def test_resolve_token_requires_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("TARGET_GITHUB_TOKEN", raising=False)
    with pytest.raises(mirror_release.GitHubApiError):
        mirror_release.resolve_token()
