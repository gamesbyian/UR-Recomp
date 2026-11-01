#!/usr/bin/env python3
"""Owner-initiated Windows fallback for missed GitHub Actions HP research schedules.

Use only with the owner's already authenticated gh CLI. Never runs repository
source or touches the self-hosted runner. Does not replace GitHub cron.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable

REPO = "gamesbyian/UR-Recomp"
RESEARCH = "owner-hp-seeded-2p-research.yml"
PRIORITY = ("owner-hp-main-windows-smoke.yml", "owner-hp-windows-benchmark.yml")
COOLDOWN = timedelta(minutes=90)
RUN_STATES = frozenset(("queued", "in_progress", "waiting", "pending", "requested"))
MAX_RECORDS = 30
GH_TIMEOUT_SECONDS = 30


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("unexpected Actions timestamp")
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("naive Actions timestamp")
    return value.astimezone(timezone.utc)


def api(args: list[str], *, timeout: int = GH_TIMEOUT_SECONDS) -> dict | None:
    """Do not dump gh stderr/stdout on auth failures (possible sensitive data)."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, check=False)
    if proc.returncode:
        raise RuntimeError("GitHub CLI API request failed; check login/network manually")
    if not proc.stdout.strip():
        return None  # dispatch returns 204 and no JSON
    result = json.loads(proc.stdout)
    if not isinstance(result, dict):
        raise ValueError("unexpected GitHub JSON object")
    return result


def workflow_runs(name: str, request: Callable[[list[str]], dict | None]) -> list[dict]:
    # Workflow endpoint, rather than global /actions/runs: high PR/comment
    # volume could push the relevant last research event off a global page.
    payload = request([f"repos/{REPO}/actions/workflows/{name}/runs?per_page={MAX_RECORDS}"])
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        raise ValueError("missing Actions workflow run census")
    rows = payload["workflow_runs"]
    if len(rows) > MAX_RECORDS or any(not isinstance(row, dict) for row in rows):
        raise ValueError("malformed Actions workflow run census")
    return rows


def main_sha(request: Callable[[list[str]], dict | None]) -> str:
    payload = request([f"repos/{REPO}/git/ref/heads/main"])
    ref = payload.get("object") if isinstance(payload, dict) else None
    sha = ref.get("sha") if isinstance(ref, dict) else None
    if (not isinstance(payload, dict) or payload.get("ref") != "refs/heads/main"
            or not isinstance(sha, str)
            or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha)):
        raise ValueError("main ref cannot be verified")
    return sha


def classify(rows: list[dict], *, expected_workflow: str) -> list[dict]:
    result = []
    for row in rows:
        # An unrecognized row cannot be safely interpreted as no work.
        if (row.get("name") not in ("HP unattended seeded 2P gameplay research",
                                     "HP current-source native Windows smoke",
                                     "Owner HP Windows runner benchmark (isolated)")
                or row.get("path") != f".github/workflows/{expected_workflow}"
                or row.get("head_branch") != "main"
                or not isinstance(row.get("id"), int)
                or row.get("event") not in ("schedule", "workflow_dispatch", "push")
                or not isinstance(row.get("head_sha"), str)
                or len(row["head_sha"]) != 40):
            raise ValueError(f"untrusted/malformed {expected_workflow} workflow row")
        status = row.get("status")
        if status not in RUN_STATES and status != "completed":
            raise ValueError(f"unknown {expected_workflow} status")
        date = parse_utc(row.get("created_at"))
        result.append({"id": row["id"], "sha": row["head_sha"],
                       "status": status, "conclusion": row.get("conclusion"),
                       "created": date, "event": row["event"]})
    return sorted(result, key=lambda x: (x["created"], x["id"]), reverse=True)


def decision(now: datetime, sha: str, research: list[dict], priority: list[dict]) -> str:
    if now.tzinfo is None:
        raise ValueError("must use UTC now")
    if any(row["status"] in RUN_STATES for row in research):
        return "skip:research-already-active"
    if any(row["status"] in RUN_STATES for row in priority):
        return "skip:priority-windows-build-active"
    if research:
        latest = research[0]
        if latest["created"] > now + timedelta(minutes=3):
            raise ValueError("Actions clock is in the future")
        if now - latest["created"] < COOLDOWN:
            return "skip:recent-research"
        if latest["sha"] == sha and latest["conclusion"] != "success":
            return "skip:latest-source-research-not-successful"
    return "dispatch:missed-research-window"


@contextmanager
def single_instance(folder: Path):
    """OS process lock: no second local timer/manual invocation can dispatch."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "dispatch.lock"
    with path.open("a+b") as f:
        if f.tell() == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("another fallback instance is active") from exc
            try:
                yield
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("another fallback instance is active") from exc
            try:
                yield
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def execute(now: datetime, request: Callable[[list[str]], dict | None], *, dry_run: bool) -> dict:
    sha = main_sha(request)
    research = classify(workflow_runs(RESEARCH, request), expected_workflow=RESEARCH)
    priority = []
    for name in PRIORITY:
        priority.extend(classify(workflow_runs(name, request), expected_workflow=name))
    result = decision(now, sha, research, priority)
    receipt = {"utc": now.isoformat(), "repo": REPO, "main_sha": sha,
               "latest_research_run": research[0]["id"] if research else None,
               "decision": result, "dispatched": False, "dry_run": dry_run}
    if result.startswith("dispatch:") and not dry_run:
        # Narrow the race against a newly arrived genuine schedule or rerun.
        second = classify(workflow_runs(RESEARCH, request), expected_workflow=RESEARCH)
        if second != research or any(x["status"] in RUN_STATES for x in second):
            receipt["decision"] = "skip:research-census-changed"
            return receipt
        # Priority workflows have distinct concurrency scopes: a main build or
        # benchmark can arrive while the first three workflow reads are underway.
        # Re-read them immediately before dispatch, not just the science caller.
        priority_second = []
        for name in PRIORITY:
            priority_second.extend(classify(workflow_runs(name, request), expected_workflow=name))
        if (priority_second != priority
                or any(x["status"] in RUN_STATES for x in priority_second)):
            receipt["decision"] = "skip:priority-census-changed"
            return receipt
        # Recheck main after all workflow censuses. An intervening branch
        # update invalidates the original source-bound dispatch decision.
        if main_sha(request) != sha:
            receipt["decision"] = "skip:main-ref-changed"
            return receipt
        # Fail closed: no external inputs, PR sha, arbitrary workflow or token.
        # A genuine GitHub schedule may appear after our census; the shared
        # workflow concurrency group still serializes all HP research jobs.
        request(["--method", "POST", "-f", "ref=main",
                 f"repos/{REPO}/actions/workflows/{RESEARCH}/dispatches"])
        receipt["dispatched"] = True
    return receipt


def publish_status(folder: Path, report: dict) -> None:
    """Bounded local machine-readable result, no secret or unbounded log."""
    folder.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (folder, folder / "last-status.json")):
        raise ValueError("redirected fallback state path")
    fd, name = tempfile.mkstemp(prefix=".last-status-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(report, output, sort_keys=True, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, folder / "last-status.json")
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Perform one guarded dispatch check")
    parser.add_argument("--dry-run", action="store_true", help="Run full census without dispatch")
    parser.add_argument("--state-dir", type=Path,
                        default=Path(os.getenv("LOCALAPPDATA", str(Path.home()))) /
                        "UR-Recomp" / "HPResearchFallback")
    args = parser.parse_args(argv)
    if not args.once and not args.dry_run:
        parser.error("--once or --dry-run required; no daemon or background process")
    try:
        with single_instance(args.state_dir):
            # All mutations of shared status must be inside the acquired OS
            # lock, including failures. A second (losing) timer must NEVER
            # overwrite the first timer's source-bound dispatch receipt.
            try:
                report = execute(utc_now(), api, dry_run=args.dry_run)
                try:
                    publish_status(args.state_dir, report)
                except (OSError, ValueError) as exc:
                    if report.get("dispatched"):
                        # GitHub already accepted POST. Do not misreport it as
                        # no confirmed dispatch or overwrite another receipt.
                        print(json.dumps({"status": "error", "category": type(exc).__name__,
                                          "detail": "GitHub accepted dispatch request; local receipt persistence failed; inspect Actions before retry",
                                          "dispatch_request_accepted": True,
                                          "main_sha": report["main_sha"]}))
                        return 2
                    raise
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                report = {"status": "error", "category": type(exc).__name__,
                          "detail": "no confirmed dispatch; inspect gh auth status and network"}
                try:
                    publish_status(args.state_dir, report)
                except (OSError, ValueError):
                    pass
                print(json.dumps(report))
                return 2
    except (OSError, ValueError, RuntimeError) as exc:
        # Lock acquisition failed, so only a bounded *stdout* diagnostic is
        # permitted. Never touch last-status.json outside the ownership lock.
        print(json.dumps({"status": "error", "category": type(exc).__name__,
                          "detail": "no dispatch confirmed; lock/state unavailable"}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())