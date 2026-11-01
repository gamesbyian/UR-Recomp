#!/usr/bin/env python3
"""Read-only GitHub Actions watchdog for owner HP Windows compute.

A scheduled science experiment is useful only if the actual scheduler keeps
firing. Inspect main-build events and true cron research events separately.
No issue creation, dispatch, Git write, machine access, ROM or credentials in
output. Unknown evidence never becomes a green status.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

REPOSITORY = "gamesbyian/UR-Recomp"
WORKFLOWS = {
    "product_windows": ("owner-hp-main-windows-smoke.yml", ("push",)),
    "unattended_2p": ("owner-hp-seeded-2p-research.yml", ("schedule",)),
}
# This read-only watchdog source is the sole main-push invalidation path of
# ops-live-snapshot; its definition must not trigger itself (CI policy).
OVERDUE_HOURS = 2  # Bounded two-hour cadence alert after four nominal half-hour slots.
MAX_RUNS = 30
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
# #2895 entered main at 02:22 UTC on October 31; its first cron is 03:17.
# An indefinitely empty Actions history must eventually raise an alert.
FIRST_ELIGIBLE_2P_UTC = datetime(2026, 10, 31, 3, 17, tzinfo=timezone.utc)
RUN_STATUSES = frozenset({"queued", "in_progress", "completed",
                          "requested", "waiting", "pending"})
RUN_CONCLUSIONS = frozenset({"success", "failure", "cancelled", "skipped",
                             "timed_out", "action_required", "neutral",
                             "stale", "startup_failure"})


def validate_run(row: dict, now: datetime) -> datetime:
    """Refuse malformed Actions evidence before filtering events/branches."""
    if not isinstance(row, dict):
        raise ValueError("invalid Actions run record")
    if type(row.get("id")) is not int or row["id"] <= 0:
        raise ValueError("invalid Actions run ID")
    if row.get("event") not in ("push", "schedule", "workflow_dispatch"):
        raise ValueError("invalid Actions event")
    branch = row.get("head_branch")
    if (not isinstance(branch, str) or not branch
            or branch != branch.strip() or any(c.isspace() for c in branch)):
        raise ValueError("invalid Actions branch")
    sha = row.get("head_sha")
    if not isinstance(sha, str) or not SHA1.fullmatch(sha):
        raise ValueError("invalid Actions source SHA")
    when = timestamp(row.get("created_at"))
    if when > now:
        raise ValueError("future Actions event")
    state, conclusion = row.get("status"), row.get("conclusion")
    if state not in RUN_STATUSES:
        raise ValueError("invalid Actions run status")
    if state == "completed":
        if conclusion not in RUN_CONCLUSIONS:
            raise ValueError("completed Actions run without valid conclusion")
    elif conclusion is not None:
        raise ValueError("unfinished Actions run with conclusion")
    return when


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp without UTC offset")
    return parsed.astimezone(timezone.utc)


def observe(lane: str, runs: list[dict], now: datetime) -> dict:
    if lane not in WORKFLOWS or not isinstance(runs, list):
        raise ValueError("invalid workflow response")
    allowed = WORKFLOWS[lane][1]
    eligible = []
    manual = 0
    for row in runs[:MAX_RUNS]:
        when = validate_run(row, now)
        if row["head_branch"] != "main":
            continue
        event = row["event"]
        # Manual trials are counted, never treated as proof that an
        # automatic push build or recurring research cron is healthy.
        if event == "workflow_dispatch":
            manual += 1
        if event not in allowed:
            continue
        eligible.append((when, row))
    eligible.sort(key=lambda item: item[0], reverse=True)
    if not eligible:
        missing_cron = (lane == "unattended_2p" and
                        (now - FIRST_ELIGIBLE_2P_UTC).total_seconds() > OVERDUE_HOURS * 3600)
        return {"status": "SCHEDULE_OVERDUE" if missing_cron else "NOT_YET_OBSERVED",
                "last_run_id": None,
                "age_hours": None, "sampled_runs": min(len(runs), MAX_RUNS),
                "recent_manual_trials": manual, "last_conclusion": None}
    when, run = eligible[0]
    run_id = run.get("id")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("invalid Actions run ID")
    age = round((now - when).total_seconds() / 3600, 2)
    status = run.get("status")
    conclusion = run.get("conclusion")
    if lane == "unattended_2p" and age > OVERDUE_HOURS:
        disposition = "SCHEDULE_OVERDUE"
    elif status != "completed":
        disposition = "IN_FLIGHT"
    elif conclusion == "success":
        disposition = "LAST_RUN_PASSED"
    else:
        disposition = "LAST_RUN_NOT_PASSED"
    recent = [(t, r) for t, r in eligible
              if (now - t).total_seconds() <= 24 * 3600 and r.get("status") == "completed"]
    successes = sum(r.get("conclusion") == "success" for _, r in recent)
    failures = sum(r.get("conclusion") != "success" for _, r in recent)
    return {"status": disposition, "last_run_id": run_id, "last_event": run.get("event"),
            "last_head_sha": run.get("head_sha"), "age_hours": age,
            "sampled_runs": min(len(runs), MAX_RUNS), "recent_manual_trials": manual,
            "last_conclusion": conclusion,
            "completed_24h": len(recent), "success_24h": successes,
            "non_success_24h": failures}


def fetch_runs(workflow: str, token: str) -> list[dict]:
    url = (f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/"
           f"{workflow}/runs?branch=main&per_page={MAX_RUNS}")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "UR-Recomp-owner-hp-compute-watch",
    })
    with urlopen(request, timeout=15) as reply:
        data = json.load(reply)
    rows = data.get("workflow_runs")
    if not isinstance(rows, list):
        raise ValueError("GitHub returned an unrecognized run list")
    return rows


def fetch_workflow_state(workflow: str, token: str) -> str:
    """Inspect GitHub's workflow registration, not merely past cron events.

    An active workflow with missing schedule events needs different recovery
    from an explicitly disabled/inactivity-disabled workflow. This query is
    read-only and neither re-enables nor dispatches anything.
    """
    if workflow not in (name for name, _ in WORKFLOWS.values()):
        raise ValueError("unknown owner HP workflow")
    url = (f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/"
           f"{workflow}")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "UR-Recomp-owner-hp-compute-watch",
    })
    with urlopen(request, timeout=15) as reply:
        payload = json.load(reply)
    if (not isinstance(payload, dict)
            or payload.get("path") != f".github/workflows/{workflow}"
            or payload.get("state") not in
               ("active", "deleted", "disabled_fork",
                "disabled_manually", "disabled_inactivity")):
        raise ValueError("unverifiable GitHub workflow registration")
    return payload["state"]


def render(report: dict) -> str:
    lines = ["## HP unattended compute watchdog", "",
             "Read-only source-bound Actions observations. "
             "Scheduled results are independent of the five LLM agents.", "",
             "| Lane | Registered workflow state | Delivery status | Most recent run | Age (hours) | Completed (24h) |",
             "|:--|:--|:--|:--|--:|--:|"]
    for lane, row in report["lanes"].items():
        run = row.get("last_run_id")
        url = (f"[#{run}](https://github.com/{REPOSITORY}/actions/runs/{run})"
               if run else "none")
        lines.append(f"| {lane} | `{row.get('workflow_state', 'UNAVAILABLE')}` | "
                     f"**{row['status']}** | {url} | "
                     f"{row.get('age_hours', 'n/a')} | {row.get('completed_24h', 'n/a')} |")
    lines += ["", "A research schedule with no observed cron run becomes overdue "
              "after its first eligible slot plus a two-hour grace period.",
              "An observed manual research trial does not establish that "
              "GitHub's recurring cron actually fired.",
              "A registered `active` workflow is not proof that any scheduled "
              "event was delivered. A disabled or deleted registration "
              "warrants owner review "
              "in GitHub Actions before further cron edits.",
              "An old product build alone is not a failure: that lane is triggered "
              "by source changes, not a timer. Manual builds cannot conceal "
              "failed automatic push verification.",
              "No automatic research acceptance or release-gate credit.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        parser.error("requires read-only token on the exact repository")
    now = datetime.now(timezone.utc)
    lanes = {}
    for lane, (workflow, _) in WORKFLOWS.items():
        try:
            lanes[lane] = observe(lane, fetch_runs(workflow, token), now)
        except Exception as exc:
            lanes[lane] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                           "last_run_id": None}
        # Registration status is an independent read. Failure here must not
        # erase a valid run census or be misrepresented as disabled.
        try:
            lanes[lane]["workflow_state"] = fetch_workflow_state(workflow, token)
        except Exception as exc:
            lanes[lane]["workflow_state"] = "UNAVAILABLE"
            lanes[lane]["workflow_state_error_type"] = type(exc).__name__
    report = {"schema": "ur-hp-compute-watch/1",
              "observed_utc": now.isoformat(), "repository": REPOSITORY,
              "lanes": lanes, "release_gate_credit": 0}
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render(report), encoding="utf-8")
    print("HP_COMPUTE_WATCH=" + ",".join(
        f"{key}:{value['status']}" for key, value in lanes.items()))
    return 0 if all(row["status"] != "UNAVAILABLE" for row in lanes.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
