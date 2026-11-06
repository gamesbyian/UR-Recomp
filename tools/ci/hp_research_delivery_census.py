#!/usr/bin/env python3
"""Manual, read-only source-bound census of the existing owner HP research workflow.

No runner operations, new cron, API writes, billing assumptions or release gates.
The observed job interval includes GitHub timing semantics, not measured CPU.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = "gamesbyian/UR-Recomp"
ROOT = f"/repos/{REPO}/actions"
WORKFLOW_ID = 402410752
WORKFLOW_NAME = "HP unattended seeded 2P gameplay research"
WORKFLOW_PATH = ".github/workflows/owner-hp-seeded-2p-research.yml"
RUNNER_NAME = "hpmini-ur-recomp"
JOB_NAME = "source-bound-windows-research / windows"
UTC_BOUND = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
OFFSET_TIME = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z"
)
HEX_SHA = re.compile(r"[a-fA-F0-9]{40}\Z")
MAX_PAGES = 10
MAX_RECORDS = 1000


def utc(value):
    if type(value) is not str or not OFFSET_TIME.fullmatch(value):
        raise ValueError("timestamp must contain a timezone and valid precision")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("timezone missing")
    return result.astimezone(timezone.utc)


def checked_window(start, end):
    if (type(start) is not str or type(end) is not str or
            not UTC_BOUND.fullmatch(start) or not UTC_BOUND.fullmatch(end)):
        raise ValueError("search bounds require UTC YYYY-MM-DDTHH:MM:SSZ")
    duration = utc(end) - utc(start)
    if not timedelta(0) < duration <= timedelta(days=7):
        raise ValueError("search window must be positive and at most seven days")
    return duration.total_seconds() + 1  # inclusive whole-second search bounds


@lru_cache(maxsize=1)
def auth_token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    try:
        p = subprocess.run(["gh", "auth", "token"], check=True, timeout=10,
                           capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise RuntimeError(
            "GitHub read authentication required: GH_TOKEN, GITHUB_TOKEN "
            "or an existing authenticated gh CLI"
        ) from None
    token = p.stdout.strip()
    if not token:
        raise RuntimeError("GitHub CLI returned no access token")
    return token


def api_get(path):
    # The request path is built internally, but still enforce the read-only,
    # repository-specific Actions route before accessing credentials.
    prefix = ROOT + "/"
    allowed = (
        path.startswith(prefix + f"workflows/{WORKFLOW_ID}/runs?")
        or re.fullmatch(re.escape(prefix) + r"runs/[1-9]\d*/jobs\?.+", path)
    )
    if not allowed:
        raise ValueError("outside allowed read-only workflow/job API routes")
    request = Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ur-hp-research-delivery-census/1",
            "Authorization": "Bearer " + auth_token(),
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_pages(get, base, field):
    expected = None
    found = []
    for page in range(1, MAX_PAGES + 1):
        payload = get(base + "&page=" + str(page))
        if type(payload) is not dict:
            raise ValueError("GitHub page must be an object")
        total = payload.get("total_count")
        items = payload.get(field)
        if (type(total) is not int or total < 0 or total > MAX_RECORDS
                or type(items) is not list or len(items) > 100
                or any(type(item) is not dict for item in items)):
            raise ValueError("invalid or over-limit GitHub page")
        if expected is None:
            expected = total
        elif expected != total:
            raise ValueError("GitHub page count drift; no complete census")
        found.extend(items)
        if len(found) > expected:
            raise ValueError("overfull API population")
        if len(found) == expected:
            return found
        if len(items) != 100:
            raise ValueError("truncated API page")
    raise ValueError("GitHub page ceiling exceeded; cannot claim full census")


def read_runs(get, start, end):
    base = ROOT + f"/workflows/{WORKFLOW_ID}/runs?" + urlencode(
        {"created": start + ".." + end, "per_page": 100}
    )
    runs = fetch_pages(get, base, "workflow_runs")
    ids = set()
    for run in runs:
        rid = run.get("id")
        if type(rid) is not int or rid <= 0 or rid in ids:
            raise ValueError("invalid or duplicate research run ID")
        ids.add(rid)
        if (run.get("name") != WORKFLOW_NAME
                or ("workflow_id" in run and
                    (type(run["workflow_id"]) is not int or
                     run["workflow_id"] != WORKFLOW_ID))
                or ("repository" in run and
                    (type(run["repository"]) is not dict or
                     run["repository"].get("full_name") != REPO))
                or run.get("path") != WORKFLOW_PATH
                or run.get("head_branch") != "main"
                or run.get("event") not in ("schedule", "workflow_dispatch")
                or run.get("status") != "completed"
                or run.get("conclusion") not in
                    ("success", "failure", "cancelled", "timed_out", "neutral", "skipped")
                or type(run.get("run_attempt", 1)) is not int
                or run.get("run_attempt", 1) < 1
                or type(run.get("head_sha")) is not str
                or not HEX_SHA.fullmatch(run["head_sha"])):
            raise ValueError(f"unexpected research source/status on run {rid}")
        when = utc(run.get("created_at"))
        if not utc(start) <= when <= utc(end):
            raise ValueError("run outside the requested UTC creation window")
    return runs


def read_one_job(get, run):
    rid = run["id"]
    base = ROOT + f"/runs/{rid}/jobs?" + urlencode(
        {"filter": "latest", "per_page": 100}
    )
    jobs = fetch_pages(get, base, "jobs")
    if len(jobs) != 1:
        raise ValueError(f"run {rid} has {len(jobs)} latest jobs; review required")
    job = jobs[0]
    if (type(job.get("id")) is not int or job["id"] <= 0
            or type(job.get("run_id")) is not int
            or job["run_id"] != rid
            or job.get("name") != JOB_NAME
            or job.get("runner_name") != RUNNER_NAME
            or job.get("status") != "completed"
            or job.get("conclusion") != run["conclusion"]):
        raise ValueError(f"run {rid} missing a source-consistent completed HP job")
    created = utc(run["created_at"])
    begun = utc(job.get("started_at"))
    ended = utc(job.get("completed_at"))
    if not created <= begun <= ended:
        raise ValueError(f"run {rid} has invalid or reversed job/queue timing")
    return {
        "run_id": rid, "job_id": job["id"], "head_sha": run["head_sha"],
        "event": run["event"], "conclusion": run["conclusion"],
        "run_attempt": run.get("run_attempt", 1),
        "created_utc": created.isoformat().replace("+00:00", "Z"),
        "started_utc": begun.isoformat().replace("+00:00", "Z"),
        "completed_utc": ended.isoformat().replace("+00:00", "Z"),
        "queue_seconds": (begun - created).total_seconds(),
        "job_interval_seconds": (ended - begun).total_seconds(),
    }


def percentile90(samples):
    if not samples:
        return None
    s = sorted(samples)
    return s[(9 * len(s) + 9) // 10 - 1]


def measure(get, start, end, workers=4):
    window = checked_window(start, end)
    if type(workers) is not int or not 1 <= workers <= 6:
        raise ValueError("workers must be 1..6")
    runs = read_runs(get, start, end)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda run: read_one_job(get, run), runs))
    # A run can be retried or reclassified while its jobs are being read.
    # Pagination total_count checks alone cannot catch an unchanged count
    # with a changed attempt or head. Fail closed on source identity drift.
    after = read_runs(get, start, end)
    def identity(rows):
        return sorted((
            r["id"], r.get("run_attempt", 1), r["head_sha"], r["event"],
            r["conclusion"], r["created_at"], r["head_branch"],
        ) for r in rows)
    if identity(after) != identity(runs):
        raise ValueError("research source/run census changed during job reads")
    jobids = [x["job_id"] for x in rows]
    if len(jobids) != len(set(jobids)):
        raise ValueError("duplicate job ID across distinct workflow runs")
    rows.sort(key=lambda r: (r["created_utc"], r["run_id"]))
    queues = [r["queue_seconds"] for r in rows]
    jobtimes = [r["job_interval_seconds"] for r in rows]
    gaps = []
    for previous, current in zip(rows, rows[1:]):
        gaps.append((utc(current["created_utc"]) -
                     utc(previous["created_utc"])).total_seconds())
    by_event = Counter(r["event"] for r in rows)
    by_outcome = Counter(r["conclusion"] for r in rows)
    by_event_minutes = {
        event: round(sum(r["job_interval_seconds"] for r in rows
                         if r["event"] == event) / 60, 5)
        for event in sorted(by_event)
    }
    per_day = Counter(utc(r["created_utc"]).strftime("%Y-%m-%d") for r in rows)
    return {
        "schema": "ur-hp-research-delivery-census/1",
        "repository": REPO, "workflow_id": WORKFLOW_ID,
        "workflow": WORKFLOW_NAME, "runner": RUNNER_NAME,
        "created_window": {"start": start, "end": end},
        "workflow_runs_complete": True, "latest_job_census_complete": True,
        "job_attempt_policy": "latest",
        "source_notes": (
            "All rows are from one trusted-main research workflow. "
            "workflow_dispatch does not identify its calling client."
        ),
        "counts": {"runs": len(rows), "by_event": dict(by_event),
                   "by_outcome": dict(by_outcome),
                   "rerun_workflow_ids": sum(r["run_attempt"] > 1 for r in rows),
                   "by_created_utc_date": dict(sorted(per_day.items()))},
        "timing": {
            "window_minutes": round(window / 60, 5),
            "job_interval_minutes_by_event": by_event_minutes,
            "observed_job_interval_minutes": round(sum(jobtimes) / 60, 5),
            "observed_research_occupancy_fraction":
                round(sum(jobtimes) / window, 6),
            "total_queue_minutes": round(sum(queues) / 60, 5),
            "max_queue_minutes": round(max(queues) / 60, 5) if queues else None,
            "queue_minutes_excluding_max":
                round((sum(queues) - max(queues)) / 60, 5) if queues else None,
            "median_queue_minutes":
                round(statistics.median(queues) / 60, 5) if queues else None,
            "p90_queue_minutes":
                round(percentile90(queues) / 60, 5) if queues else None,
            "median_job_interval_minutes":
                round(statistics.median(jobtimes) / 60, 5) if jobtimes else None,
            "p90_job_interval_minutes":
                round(percentile90(jobtimes) / 60, 5) if jobtimes else None,
            "median_creation_spacing_minutes":
                round(statistics.median(gaps) / 60, 5) if gaps else None,
            "p90_creation_spacing_minutes":
                round(percentile90(gaps) / 60, 5) if gaps else None,
        },
        "queue_over_30m": [
            {"run_id": r["run_id"], "queue_minutes":
             round(r["queue_seconds"] / 60, 5),
             "classification": "cause unknown; correlate with HP availability"}
            for r in rows if r["queue_seconds"] > 1800
        ],
        "runs": rows,
        "limitations": (
            "Started/completed GitHub job intervals are not measured CPU, "
            "billing, wasted minutes, device uptime or release qualification. "
            "Long queues are not proof of CPU saturation or fallback causation."
        ),
    }


def render_markdown(report):
    count = report["counts"]
    t = report["timing"]
    lines = [
        "# HP research workflow delivery: manual GitHub census", "",
        f"Repository: {report['repository']}; runner: {report['runner']}",
        "Created UTC: " + report["created_window"]["start"] + " .. " +
        report["created_window"]["end"],
        "Source: complete workflow and latest-job API inventories; "
        "source-bound main only.", "",
        f"- Runs: **{count['runs']}**, schedule {count['by_event'].get('schedule', 0)}, "
        f"workflow_dispatch {count['by_event'].get('workflow_dispatch', 0)}.",
        f"- Outcomes: {json.dumps(count['by_outcome'], sort_keys=True)}.",
        f"- Valid job interval minutes: **{t['observed_job_interval_minutes']:.2f}**.",
        f"- Job interval share of the requested calendar window: "
        f"{100*t['observed_research_occupancy_fraction']:.2f}% "
        "(research workflow only).",
        f"- Queue minutes: **{t['total_queue_minutes']:.2f}**; "
        f"median {t['median_queue_minutes']} and p90 {t['p90_queue_minutes']}.",
        f"- Maximum queue: {t['max_queue_minutes']} minutes; "
        f"all other queues together: {t['queue_minutes_excluding_max']} minutes.",
        f"- >30-minute queues needing external host correlation: "
        f"{len(report['queue_over_30m'])}.", "",
        "## UTC creation-day distribution", "",
        "| UTC day | Run count |", "| --- | ---: |",
    ]
    lines += [f"| {day} | {num} |"
              for day, num in count["by_created_utc_date"].items()]
    lines += ["", "## Extended queue evidence (no automatic causation)", ""]
    lines += [f"- Run {r['run_id']}: {r['queue_minutes']:.2f} minutes; "
              f"{r['classification']}"
              for r in report["queue_over_30m"]]
    lines += ["", report["limitations"], "",
              "No source or runner changes, automatic dispatch, cost "
              "estimate, acceptance gate or secret is produced."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    args = p.parse_args(argv)
    report = measure(api_get, args.start, args.end, workers=args.workers)
    rendered = render_markdown(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, sort_keys=True, indent=2) +
                                 "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
