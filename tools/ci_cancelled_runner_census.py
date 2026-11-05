#!/usr/bin/env python3
"""Read-only seven-day GitHub Actions cancellation runner-time census.

Observed job time is neither proof of avoidable waste nor billing cost.
No dispatches, schedule edits or runner writes are performed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

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


def utc(value):
    from datetime import datetime
    if type(value) is not str or not STAMP.fullmatch(value):
        raise ValueError("expected exact UTC YYYY-MM-DDTHH:MM:SSZ")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def span(start, end):
    from datetime import timedelta
    delta = utc(end) - utc(start)
    if not timedelta(0) < delta <= timedelta(days=7):
        raise ValueError("window must be greater than zero and <= seven days")
    return start + ".." + end


def api_get(path):
    if not path.startswith(ROOT + "/"):
        raise ValueError("GitHub API route outside repository")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "ur-ci-cancelled-runner-census/1"}
    if token:
        headers["Authorization"] = "Bearer " + token
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


def get_run_jobs(fetch, run_id):
    base = ROOT + "/actions/runs/" + str(run_id) + "/jobs"
    jobs, expected = [], None
    for page in range(1, MAX_PAGES + 1):
        url = base + "?" + urllib.parse.urlencode({"per_page": 100, "page": page})
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
    valid = invalid = missing_end = 0
    for job in jobs:
        jid = job.get("id")
        if type(jid) is not int or jid < 1 or jid in seen:
            raise ValueError("duplicate or invalid job ID")
        seen.add(jid)
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
    return {"valid_started": valid, "invalid_intervals": invalid,
            "missing_completions": missing_end,
            "seconds_inside_cancelled_run": valid_seconds,
            "seconds_cancelled_jobs": cancelled_seconds}


def measure(fetch, start, end, workflows=WORKFLOWS, workers=6):
    created = span(start, end)
    if not 1 <= workers <= 8:
        raise ValueError("workers must be in range 1..8")
    rows = []
    for name, workflow in workflows.items():
        if type(workflow) is not int or workflow < 1:
            raise ValueError("invalid workflow ID")
        total, cancelled = get_run_census(fetch, workflow, created)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            jobs = list(pool.map(lambda r: get_run_jobs(fetch, r["id"]), cancelled))
        sums = {key: sum(j[key] for j in jobs) for key in (
            "valid_started", "invalid_intervals", "missing_completions",
            "seconds_inside_cancelled_run", "seconds_cancelled_jobs")}
        rows.append({"name": name, "workflow_id": workflow, "all_runs": total,
                     "cancelled_runs": len(cancelled),
                     "cancelled_with_started_jobs": sum(j["valid_started"] > 0 for j in jobs),
                     **sums})
    return {"schema": "ur-ci-cancelled-runner-census/1", "repository": REPO,
            "created_after_utc": start, "created_before_utc": end,
            "workflows": rows,
            "limitations": "Valid observed runner spans only; not billable, wasted, avoidable or recovered minutes. Invalid and missing intervals excluded."}


def render_markdown(receipt):
    lines = ["# Cancelled-workflow runner-time census", "",
             "Source: " + receipt["repository"] + " created " +
             receipt["created_after_utc"] + " through " + receipt["created_before_utc"],
             "",
             "| Workflow | Runs | Cancelled | Valid started job spans | Invalid intervals | Runner minutes | Cancelled job minutes |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in receipt["workflows"]:
        lines.append(f'| {r["name"]} | {r["all_runs"]} | {r["cancelled_runs"]} | '
                     f'{r["valid_started"]} | {r["invalid_intervals"]} | '
                     f'{r["seconds_inside_cancelled_run"]/60:.2f} | '
                     f'{r["seconds_cancelled_jobs"]/60:.2f} |')
    lines.extend(["", "Evidence limit: " + receipt["limitations"], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--json-out", type=str)
    parser.add_argument("--markdown-out", type=str)
    args = parser.parse_args()
    result = measure(api_get, args.start, args.end)
    rendered = render_markdown(result)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                       encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
