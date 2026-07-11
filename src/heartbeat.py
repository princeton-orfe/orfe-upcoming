"""Create a small keepalive file when the default branch has been idle too long."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SECONDS_PER_DAY = 24 * 60 * 60


@dataclass(frozen=True)
class HeartbeatDecision:
    should_write: bool
    age_days: float
    threshold_days: int


def _format_utc(epoch_seconds: int) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def decide_heartbeat(*, last_commit_epoch: int, now_epoch: int, threshold_days: int) -> HeartbeatDecision:
    age_seconds = max(0, now_epoch - last_commit_epoch)
    age_days = age_seconds / SECONDS_PER_DAY
    return HeartbeatDecision(
        should_write=age_seconds >= threshold_days * SECONDS_PER_DAY,
        age_days=age_days,
        threshold_days=threshold_days,
    )


def build_payload(
    *,
    now_epoch: int,
    last_commit_epoch: int,
    ref_name: str,
    source_sha: str,
    threshold_days: int,
) -> dict[str, object]:
    return {
        "updatedAt": _format_utc(now_epoch),
        "previousCommitAt": _format_utc(last_commit_epoch),
        "ref": ref_name,
        "sourceSha": source_sha,
        "thresholdDays": threshold_days,
    }


def write_heartbeat(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def write_github_output(path: Path, decision: HeartbeatDecision) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"changed={'true' if decision.should_write else 'false'}\n")
        handle.write(f"age_days={decision.age_days:.2f}\n")
        handle.write(f"threshold_days={decision.threshold_days}\n")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--last-commit-epoch", required=True, type=int)
    parser.add_argument("--threshold-days", required=True, type=int)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    now_epoch = int(time.time())
    decision = decide_heartbeat(
        last_commit_epoch=args.last_commit_epoch,
        now_epoch=now_epoch,
        threshold_days=args.threshold_days,
    )

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        write_github_output(Path(github_output), decision)

    if decision.should_write:
        payload = build_payload(
            now_epoch=now_epoch,
            last_commit_epoch=args.last_commit_epoch,
            ref_name=args.ref_name,
            source_sha=args.source_sha,
            threshold_days=args.threshold_days,
        )
        write_heartbeat(Path(args.output), payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
