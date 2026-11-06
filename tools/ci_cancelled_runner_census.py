#!/usr/bin/env python3
"""Read-only seven-day GitHub Actions cancellation timing census.

Observed job time is neither proof of avoidable waste nor billing cost.
No dispatches, schedule edits or runner writes are performed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import functools
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone

REPO = "gamesbyian/UR-Recomp"
ROOT = "/repos/" + REPO
WORKFLOWS = {
    "tooling": 369800124,
    "hygiene": 374916710,
    "visual_atlas": 393802512,
    "windows_candidate": 379623240,
    "windows_native": 374411662,
    "hp_research": 402410752,
}
MAX_PAGES = 10  # GitHub Actions run listing is capped at 1,000.
STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
API_STAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z"
)


def utc(value):
    """Parse a timezone-qualified GitHub timestamp, preserving UTC instants.

    The REST schema permits fractional seconds and ISO8601 offsets in job
    and step records; user-supplied search-window bounds remain strict Z.
    """
    if type(value) is not str or not API_STAMP.fullmatch(value):
        raise ValueError("expected a timezone-qualified GitHub timestamp")
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.utcoffset() is None:
        raise ValueError("missing GitHub timestamp offset")
    return instant.astimezone(timezone.utc)


def span(start, end):
    if (type(start) is not str or type(end) is not str
            or not STAMP.fullmatch(start) or not STAMP.fullmatch(end)):
        raise ValueError("window bounds require exact YYYY-MM-DDTHH:MM:SSZ")
    delta = utc(end) - utc(start)
    if not timedelta(0) < delta <= timedelta(days=7):
        raise ValueError("window must be greater than zero and <= seven days")
    return start + ".." + end


@functools.lru_cache(maxsize=1)
def auth_token():
    """Resolve read-only GitHub credentials once; never use anonymous fallback.

    An authenticated GitHub CLI on a Windows owner workstation does not
    automatically populate GH_TOKEN/GITHUB_TOKEN in the calling shell.
    Silent anonymous fallback would exhaust the 60-request/hour limit before
    this bounded multi-workflow census could complete.
    """
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(name)
        if token and token.strip():
            return token.strip()
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], check=True, capture_output=True,
            text=True, timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        raise RuntimeError(
            "GitHub authentication required: set GH_TOKEN/GITHUB_TOKEN "
            "or authenticate the GitHub CLI with gh auth login"
        ) from None
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("GitHub CLI returned no token; set GH_TOKEN or run gh auth login")
    return token


def api_get(path):
    if not path.startswith(ROOT + "/"):
        raise ValueError("GitHub API route outside repository")
    token = auth_token()
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "ur-ci-cancelled-runner-census/2",
               "Authorization": "Bearer " + token}
    request = urllib.request.Request("https://api.github.com" + path,
                                     headers=headers)
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)


def obj(value, what):
    if type(value) is not dict:
        raise ValueError("malformed " + what)
    return value


def count(value, what):
    if type(value) is not int or value < 0:
        raise ValueError("invalid count " + what)
    return value


def get_run_census(fetch, workflow, created):
    """Fetch all cancelled runs, refusing missing/changed/capped inventories."""
    base = ROOT + "/actions/workflows/" + str(workflow) + "/runs"
    def query(page, cancelled=False):
        fields = {"created": created, "per_page": 100, "page": page}
        if cancelled:
            fields["status"] = "cancelled"
        return base + "?" + urllib.parse.urlencode(fields)

    total = count(obj(fetch(query(1)), "run summary").get("total_count"), "all runs")
    rows = []
    expected = None
    for page in range(1, MAX_PAGES + 1):
        receipt = obj(fetch(query(page, True)), "cancelled page")
        n = count(receipt.get("total_count"), "cancelled runs")
        if expected is None:
            expected = n
            if n > 1000:
                raise ValueError("cancelled run census exceeds 1000")
        elif n != expected:
            raise ValueError("cancelled run population moved during pagination")
        batch = receipt.get("workflow_runs")
        if type(batch) is not list or len(batch) > 100 or any(type(x) is not dict for x in batch):
            raise ValueError("malformed cancelled page")
        rows.extend(batch)
        if len(rows) >= n:
            break
        if len(batch) != 100:
            raise ValueError("incomplete cancelled page")
    if expected is None or len(rows) != expected or expected > total:
        raise ValueError("incomplete cancelled run census")
    left, right = map(utc, created.split(".."))
    seen = set()
    for row in rows:
        rid = row.get("id")
        if type(rid) is not int or rid < 1 or rid in seen:
            raise ValueError("duplicate or invalid run ID")
        seen.add(rid)
        if row.get("conclusion") != "cancelled" or row.get("workflow_id") != workflow:
            raise ValueError("wrong workflow or run conclusion")
        if not left <= utc(row.get("created_at")) <= right:
            raise ValueError("run created outside selected window")
    return total, rows


def get_run_jobs(fetch, run_id, attempt_policy="latest"):
    """Read one cancelled run's latest or full rerun history, explicitly.

    GitHub's default is latest. Retain that as the historical P3 v1/v2
    baseline policy; use 'all' only for a separately labelled census.
    """
    if type(run_id) is not int or run_id < 1:
        raise ValueError("invalid source run ID")
    if attempt_policy not in ("latest", "all"):
        raise ValueError("invalid job attempt policy")
    base = ROOT + "/actions/runs/" + str(run_id) + "/jobs"
    jobs, expected = [], None
    for page in range(1, MAX_PAGES + 1):
        url = base + "?" + urllib.parse.urlencode({
            "filter": attempt_policy, "per_page": 100, "page": page
        })
        receipt = obj(fetch(url), "job page")
        n = count(receipt.get("total_count"), "jobs")
        if expected is None:
            expected = n
            if n > 1000:
                raise ValueError("job census exceeds 1000")
        elif n != expected:
            raise ValueError("job population moved during pagination")
        batch = receipt.get("jobs")
        if type(batch) is not list or len(batch) > 100 or any(type(x) is not dict for x in batch):
            raise ValueError("malformed job page")
        jobs.extend(batch)
        if len(jobs) >= n:
            break
        if len(batch) != 100:
            raise ValueError("incomplete job page")
    if expected is None or len(jobs) != expected:
        raise ValueError("incomplete jobs")
    seen = set()
    valid_seconds = cancelled_seconds = 0.
    step_seconds = prefirst_step_seconds = 0.
    valid = invalid = missing_end = 0
    timed_steps = invalid_steps = jobs_with_steps = jobs_without_step_evidence = 0
    for job in jobs:
        jid = job.get("id")
        if type(jid) is not int or jid < 1 or jid in seen:
            raise ValueError("duplicate or invalid job ID")
        seen.add(jid)
        if "run_id" in job and (type(job["run_id"]) is not int
                                or job["run_id"] != run_id):
            raise ValueError("job returned from another workflow run")
        start, end = job.get("started_at"), job.get("completed_at")
        if start is None:
            continue
        if end is None:
            missing_end += 1
            continue
        try:
            seconds = (utc(end) - utc(start)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            invalid += 1
            continue
        if seconds < 0:
            invalid += 1
            continue
        valid += 1
        valid_seconds += seconds
        if job.get("conclusion") == "cancelled":
            cancelled_seconds += seconds

        # A job can report a start minutes before any real step. Keep
        # GitHub's job intervals and observed step spans distinct.
        steps = job.get("steps")
        if type(steps) is not list:
            jobs_without_step_evidence += 1
            continue
        first_step = None
        observed = False
        for step in steps:
            if type(step) is not dict:
                raise ValueError("malformed job step")
            if step.get("conclusion") == "skipped":
                continue
            before, after = step.get("started_at"), step.get("completed_at")
            if before is None or after is None:
                continue
            try:
                st, en = utc(before), utc(after)
            except (ValueError, TypeError, OverflowError):
                invalid_steps += 1
                continue
            if en < st:
                invalid_steps += 1
                continue
            observed = True
            timed_steps += 1
            step_seconds += (en - st).total_seconds()
            if first_step is None or st < first_step:
                first_step = st
        if observed:
            jobs_with_steps += 1
            gap = (first_step - utc(start)).total_seconds()
            if gap < 0:
                invalid_steps += 1
            else:
                prefirst_step_seconds += gap
        else:
            jobs_without_step_evidence += 1
    return {"valid_started": valid, "invalid_intervals": invalid,
            "missing_completions": missing_end,
            "seconds_inside_cancelled_run": valid_seconds,
            "seconds_cancelled_jobs": cancelled_seconds,
            "timed_steps": timed_steps, "invalid_step_intervals": invalid_steps,
            "jobs_with_timed_steps": jobs_with_steps,
            "jobs_without_step_evidence": jobs_without_step_evidence,
            "seconds_in_timed_steps": step_seconds,
            "seconds_job_to_first_step": prefirst_step_seconds}


def measure(fetch, start, end, workflows=WORKFLOWS, workers=6,
            attempt_policy="latest"):
    created = span(start, end)
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("workers must be in range 1..8")
    if attempt_policy not in ("latest", "all"):
        raise ValueError("invalid job attempt policy")
    rows = []
    for name, workflow in workflows.items():
        if type(workflow) is not int or workflow < 1:
            raise ValueError("invalid workflow ID")
        total, cancelled = get_run_census(fetch, workflow, created)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            jobs = list(pool.map(
                lambda r: get_run_jobs(fetch, r["id"], attempt_policy),
                cancelled,
            ))
        sums = {key: sum(j[key] for j in jobs) for key in (
            "valid_started", "invalid_intervals", "missing_completions",
            "seconds_inside_cancelled_run", "seconds_cancelled_jobs",
            "timed_steps", "invalid_step_intervals", "jobs_with_timed_steps",
            "jobs_without_step_evidence", "seconds_in_timed_steps",
            "seconds_job_to_first_step")}
        rows.append({"name": name, "workflow_id": workflow, "all_runs": total,
                     "cancelled_runs": len(cancelled),
                     "cancelled_runs_with_reruns": sum(
                         type(r.get("run_attempt")) is int
                         and r["run_attempt"] > 1 for r in cancelled),
                     "cancelled_with_started_jobs": sum(j["valid_started"] > 0 for j in jobs),
                     **sums})
    return {"schema": "ur-ci-cancelled-runner-census/3", "repository": REPO,
            "created_after_utc": start, "created_before_utc": end,
            "job_attempt_policy": attempt_policy,
            "workflows": rows,
            "limitations": "GitHub job-interval and step-duration spans only; neither proves billed, active-CPU, wasted, avoidable or recovered minutes. Invalid/missing intervals and skipped steps excluded."}


def render_markdown(receipt):
    lines = ["# Cancelled-workflow GitHub timing census", "",
             "Source: " + receipt["repository"] + " created " +
             receipt["created_after_utc"] + " through " + receipt["created_before_utc"],
             "",
             "Job attempt policy: **" + receipt["job_attempt_policy"] +
             "** (latest is the original P3 v1/v2 baseline; all includes reruns)",
             "",
             "| Workflow | Runs | Cancelled | Valid job spans | Invalid job intervals | Job interval min | Cancelled job interval min | Step duration min | Pre-first-step gap min | Jobs with step evidence |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in receipt["workflows"]:
        lines.append(f'| {r["name"]} | {r["all_runs"]} | {r["cancelled_runs"]} | '
                     f'{r["valid_started"]} | {r["invalid_intervals"]} | '
                     f'{r["seconds_inside_cancelled_run"]/60:.2f} | '
                     f'{r["seconds_cancelled_jobs"]/60:.2f} | '
                     f'{r["seconds_in_timed_steps"]/60:.2f} | '
                     f'{r["seconds_job_to_first_step"]/60:.2f} | '
                     f'{r["jobs_with_timed_steps"]} |')
    lines.extend(["", "Evidence limit: " + receipt["limitations"], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--json-out", type=str)
    parser.add_argument("--markdown-out", type=str)
    parser.add_argument(
        "--attempts", choices=("latest", "all"), default="latest",
        help="latest (baseline-compatible) or all (includes rerun history)",
    )
    args = parser.parse_args()
    result = measure(api_get, args.start, args.end,
                     attempt_policy=args.attempts)
    rendered = render_markdown(result)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                       encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
