"""Mirror release assets into a legacy GitHub repository."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"


class GitHubApiError(RuntimeError):
    """Raised when the GitHub API returns an unexpected response."""


def resolve_token() -> str:
    token = os.getenv("TARGET_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubApiError("TARGET_GITHUB_TOKEN or GITHUB_TOKEN must be set")
    return token


def build_release_payload(
    *,
    tag: str,
    title: str,
    notes: str,
    latest: bool,
    prerelease: bool,
    target_commitish: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tag_name": tag,
        "name": title,
        "body": notes,
        "draft": False,
        "prerelease": prerelease,
        "make_latest": "true" if latest else "false",
    }
    if target_commitish:
        payload["target_commitish"] = target_commitish
    return payload


def build_upload_url(upload_url: str, asset_name: str) -> str:
    return f"{upload_url.split('{', 1)[0]}?name={quote(asset_name)}"


def _request_json(
    *,
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    content_type: str = "application/json",
    accept: str = "application/vnd.github+json",
    allow_not_found: bool = False,
) -> dict[str, Any] | None:
    data: bytes | None = None
    headers = {
        "Accept": accept,
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = content_type

    request = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(request) as response:
            body = response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if allow_not_found and exc.code == 404:
            return None
        raise GitHubApiError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc

    if not body:
        return {}
    return json.loads(body)


def _upload_asset(upload_url: str, asset_path: Path, token: str) -> None:
    body = asset_path.read_bytes()
    content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
    request = Request(
        build_upload_url(upload_url, asset_path.name),
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    try:
        with urlopen(request):
            return
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise GitHubApiError(
            f"POST {request.full_url} failed with HTTP {exc.code}: {body_text}"
        ) from exc


def get_release_by_tag(repo: str, tag: str, token: str) -> dict[str, Any] | None:
    return _request_json(
        method="GET",
        url=f"{API_ROOT}/repos/{repo}/releases/tags/{quote(tag)}",
        token=token,
        allow_not_found=True,
    )


def delete_release(repo: str, tag: str, token: str) -> None:
    release = get_release_by_tag(repo, tag, token)
    if release is None:
        return
    release_id = release["id"]
    _request_json(
        method="DELETE",
        url=f"{API_ROOT}/repos/{repo}/releases/{release_id}",
        token=token,
    )


def create_release(
    *,
    repo: str,
    tag: str,
    title: str,
    notes: str,
    latest: bool,
    prerelease: bool,
    target_commitish: str | None,
    token: str,
) -> dict[str, Any]:
    payload = build_release_payload(
        tag=tag,
        title=title,
        notes=notes,
        latest=latest,
        prerelease=prerelease,
        target_commitish=target_commitish,
    )
    response = _request_json(
        method="POST",
        url=f"{API_ROOT}/repos/{repo}/releases",
        token=token,
        payload=payload,
    )
    if response is None:
        raise GitHubApiError(f"GitHub did not return a release object for {repo}@{tag}")
    return response


def sync_release(
    *,
    repo: str,
    tag: str,
    title: str,
    notes: str,
    assets: list[Path],
    latest: bool,
    prerelease: bool,
    target_commitish: str | None,
    token: str,
) -> None:
    delete_release(repo, tag, token)
    release = create_release(
        repo=repo,
        tag=tag,
        title=title,
        notes=notes,
        latest=latest,
        prerelease=prerelease,
        target_commitish=target_commitish,
        token=token,
    )
    upload_url = release["upload_url"]
    for asset_path in assets:
        _upload_asset(upload_url, asset_path, token)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-repo", required=True, help="owner/name for the legacy repository")
    parser.add_argument("--target-commitish", help="branch or commit for new tags if the tag does not exist")
    parser.add_argument("--tag", required=True, help="Release tag to recreate")
    parser.add_argument("--title", required=True, help="Release title")
    parser.add_argument("--notes", required=True, help="Release notes/body")
    parser.add_argument(
        "--asset",
        dest="assets",
        action="append",
        required=True,
        help="Local asset file to upload; repeat for multiple assets",
    )
    parser.add_argument("--latest", action="store_true", help="Mark the mirrored release as latest")
    parser.add_argument("--prerelease", action="store_true", help="Mark the mirrored release as a prerelease")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    token = resolve_token()
    assets = [Path(asset) for asset in args.assets]
    missing = [str(path) for path in assets if not path.is_file()]
    if missing:
        raise GitHubApiError(f"Asset files not found: {', '.join(missing)}")

    sync_release(
        repo=args.target_repo,
        tag=args.tag,
        title=args.title,
        notes=args.notes,
        assets=assets,
        latest=args.latest,
        prerelease=args.prerelease,
        target_commitish=args.target_commitish,
        token=token,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHubApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
