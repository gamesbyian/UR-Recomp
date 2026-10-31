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
from pathlib import Path
from urllib.request import Request, urlopen

REPOSITORY = "gamesbyian/UR-Recomp"
WORKFLOWS = {
    "product_windows": ("owner-hp-main-windows-smoke.yml", ("push", "workflow_dispatch")),
    "unattended_2p": ("owner-hp-seeded-2p-research.yml", ("schedule",)),
}
OVERDUE_HOURS = 8
MAX_RUNS = 30


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
        if not isinstance(row, dict) or row.get("head_branch") != "main":
            continue
        event = row.get("event")
        if lane == "unattended_2p" and event == "workflow_dispatch":
            manual += 1
        if event not in allowed:
            continue
        when = timestamp(row.get("created_at"))
        if when > now:
            raise ValueError("future Actions event")
        eligible.append((when, row))
    eligible.sort(key=lambda item: item[0], reverse=True)
    if not eligible:
        return {"status": "NOT_YET_OBSERVED", "last_run_id": None,
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
           f"{workflow}/runs?per_page={MAX_RUNS}")
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


def render(report: dict) -> str:
    lines = ["## HP unattended compute watchdog", "",
             "Read-only source-bound Actions observations. "
             "Scheduled results are independent of the five LLM agents.", "",
             "| Lane | Current status | Most recent run | Age (hours) | Completed (24h) |",
             "|:--|:--|:--|--:|--:|"]
    for lane, row in report["lanes"].items():
        run = row.get("last_run_id")
        url = (f"[#{run}](https://github.com/{REPOSITORY}/actions/runs/{run})"
               if run else "none")
        lines.append(f"| {lane} | **{row['status']}** | {url} | "
                     f"{row.get('age_hours', 'n/a')} | {row.get('completed_24h', 'n/a')} |")
    lines += ["", "An observed manual research trial does not establish that "
              "GitHub's recurring cron actually fired.",
              "An old product build alone is not a failure: that lane is triggered "
              "by source changes, not a timer.",
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
