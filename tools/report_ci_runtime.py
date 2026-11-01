#!/usr/bin/env python3
"""Summarize GitHub Actions run, job, and step wall-clock timing."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from statistics import median
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def elapsed_seconds(start_value: str | None, end_value: str | None) -> float:
    start = parse_time(start_value)
    end = parse_time(end_value)
    if not start or not end or end < start:
        return 0.0
    return (end - start).total_seconds()


def observed_completed_wall_seconds(start_value, end_value) -> float | None:
    """None means timing unavailable, not an observed zero-second run."""
    try:
        start = parse_time(start_value)
        end = parse_time(end_value)
    except (ValueError, TypeError, OverflowError):
        return None
    if (start is None or end is None or start.tzinfo is None
            or end.tzinfo is None or end < start):
        return None
    return (end - start).total_seconds()


def p90_nearest_rank(samples: list[float]) -> float | None:
    """90th percentile by nearest rank, with no invented zero for empty data."""
    if not samples:
        return None
    return sorted(samples)[(9 * len(samples) + 9) // 10 - 1]


def elapsed_minutes_or_unknown(value) -> str:
    return "unknown" if value is None else f"{value / 60:.1f}"


def step_bucket(name: str) -> str:
    lowered = name.lower()
    if (
        re.search(r"\bapt(?:-get)?\b", lowered) is not None
        or "package dependenc" in lowered
        or ("install" in lowered and "dependenc" in lowered)
        # The Windows static SDL3 install is dependency setup, even though
        # the step name says 'cache'. Likewise restore/save transport time.
        # Previous reports wrongly charged ~110s of Windows setup to 'other'.
        or "source-pinned static sdl3 cache" in lowered
        or "hosted windows verified sdl3 candidate" in lowered
        # Source-owned main-push seed steps added after the original cache
        # reporter correction; these are dependency work, not "other".
        or lowered in (
            "restore hosted main-branch sdl3 seed",
            "validate isolated hosted main sdl3 seed",
            "save verified hosted main-branch sdl3 seed",
        )
    ):
        return "dependency"
    if any(token in lowered for token in (
        "build", "compile", "configure", "scaffold", "cmake", "generate"
    )):
        return "build"
    if any(token in lowered for token in (
        "acceptance", "route", "smoke", "capture", "boot", "prove", "compare",
        "regression", "evidence shard", "replay",
        # The dominant actual Win32 QA checks are named by their gate IDs
        # rather than the word "acceptance". Keep their elapsed runner time
        # in execution instead of leaving them invisible in "other".
        "qa-05 packaged", "qa-09 packaged"
    )):
        return "execution"
    return "other"



def needs_job_detail(run: dict[str, Any]) -> bool:
    """A completed, wholly skipped workflow has no executed jobs to time.

    Keep its run-level event and wall metadata in the sample. Do not waste
    another Actions API request fetching job records that are all skipped.
    Fail open for missing/ambiguous status so real execution is never hidden.
    """
    return not (run.get("status") == "completed"
                and run.get("conclusion") == "skipped")


def jobs_by_run(payload: dict[str, Any] | None) -> dict[int, list[dict[str, Any]]]:
    if not payload:
        return {}
    result: dict[int, list[dict[str, Any]]] = {}
    for entry in payload.get("runs", []):
        run_id = entry.get("run_id")
        if run_id is None:
            continue
        result[int(run_id)] = list(entry.get("jobs", []))
    return result



MAX_POST_STEP_JOB_SECONDS = 600


def untrusted_job_completion_time(job: dict[str, Any]) -> bool:
    """Reject API job ends irreconcilable with source-observed final steps.

    A real HP run crossing 2026-11-01 DST had completed_at one hour AFTER
    its actual final job log and completed Actions step. Do not silently
    count that phantom hour as occupied CPU or try to repair the timestamp.
    Without completed step evidence, the job interval remains unverified
    by this additional guard (ordinary missing-time rules still apply).
    """
    try:
        end = parse_time(job.get("completed_at"))
        steps = job.get("steps") or []
        ended_steps = [
            parse_time(step.get("completed_at"))
            for step in steps if isinstance(step, dict) and step.get("completed_at")
        ]
    except (AttributeError, TypeError, ValueError, OverflowError):
        return True
    ended_steps = [value for value in ended_steps if value is not None]
    if not end or not ended_steps:
        return False
    if end.tzinfo is None or any(value.tzinfo is None for value in ended_steps):
        return True
    delta = (end - max(ended_steps)).total_seconds()
    return delta < -60 or delta > MAX_POST_STEP_JOB_SECONDS


def job_parallelism_profile(jobs: list[dict[str, Any]]) -> dict[str, float] | None:
    """Observed runner occupancy from actual started/completed job intervals.

    Ending a job at the same instant another starts does not constitute
    concurrent work. Skipped, unstarted and malformed intervals contribute
    no runner seconds. This is an *observed span*, not the dependency-DAG
    critical path or GitHub queue time.
    """
    intervals: list[tuple[datetime, datetime]] = []
    for job in jobs:
        # GitHub can populate synthetic timestamps for skipped matrix jobs,
        # even in reverse order. They never occupied a runner.
        if job.get("conclusion") == "skipped" or untrusted_job_completion_time(job):
            continue
        start = parse_time(job.get("started_at"))
        end = parse_time(job.get("completed_at"))
        if start and end and end > start:
            intervals.append((start, end))
    if not intervals:
        return None

    edges = []
    runner_seconds = 0.0
    for start, end in intervals:
        runner_seconds += (end - start).total_seconds()
        edges.extend(((start, 1), (end, -1)))
    edges.sort(key=lambda item: (item[0], item[1]))
    active = 0
    peak = 0
    for _time, delta in edges:
        active += delta
        peak = max(peak, active)
    observed_span_seconds = (
        max(end for _, end in intervals) - min(start for start, _ in intervals)
    ).total_seconds()
    return {
        "runner_seconds": runner_seconds,
        "observed_span_seconds": observed_span_seconds,
        "peak_active_jobs": float(peak),
    }



def same_source_cross_workflow_build_candidates(
    payload: dict[str, Any],
    jobs_payload: dict[str, Any] | None,
    since_hours: float | None,
    now: datetime,
) -> list[dict[str, Any]]:
    """Identify possible duplicate builds using *observed* job step timestamps.

    Same Actions head SHA does NOT establish equal checkout, toolchain, compiled
    EXE, private ZIP, or intended acceptance. This reports review candidates,
    not estimated avoidable runner cost or jobs that should be disabled.
    """
    import re

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    job_map = jobs_by_run(jobs_payload)
    for run in payload.get("workflow_runs", []):
        sha = run.get("head_sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            continue
        started = parse_time(run.get("run_started_at") or run.get("created_at"))
        if started is None or (since_hours is not None and
                               (now - started).total_seconds() > since_hours * 3600):
            continue
        if run.get("status") != "completed" or type(run.get("id")) is not int:
            continue
        build_seconds = 0.0
        observed_build_steps = 0
        for job in job_map.get(run["id"], []):
            for step in job.get("steps", []):
                if step_bucket(str(step.get("name") or "")) != "build":
                    continue
                seconds = elapsed_seconds(step.get("started_at"), step.get("completed_at"))
                if seconds > 0:
                    build_seconds += seconds
                    observed_build_steps += 1
        if build_seconds > 0:
            grouped[sha].append({
                "run_id": run["id"],
                "workflow": str(run.get("name") or "unknown")[:140],
                "event": str(run.get("event") or "unknown")[:40],
                "started": started,
                "build_seconds": round(build_seconds, 3),
                "timed_build_steps": observed_build_steps,
            })
    result = []
    for sha, rows in grouped.items():
        rows.sort(key=lambda row: (row["started"], row["run_id"]))
        # Only compare close-in-time executions: an old deliberate re-run
        # and a current regression are not an obvious consolidation case.
        for start in range(len(rows)):
            group = [rows[start]]
            for row in rows[start + 1:]:
                if (row["started"] - rows[start]["started"]).total_seconds() > 7200:
                    break
                group.append(row)
            names = {row["workflow"] for row in group}
            if len(names) < 2:
                continue
            result.append({
                "head_sha": sha,
                "run_ids": [row["run_id"] for row in group[:12]],
                "workflow_names": sorted(names)[:10],
                "runs_observed": len(group),
                "timed_build_steps": sum(row["timed_build_steps"] for row in group),
                "observed_build_step_seconds": round(
                    sum(row["build_seconds"] for row in group), 3),
                "start_span_seconds": round(
                    (group[-1]["started"] - group[0]["started"]).total_seconds(), 3),
                "status": "manual_review_only_identity_and_coverage_unverified",
            })
            break
    result.sort(key=lambda row: (-row["observed_build_step_seconds"], row["head_sha"]))
    return result[:10]

def summarize(
    payload: dict[str, Any],
    since_hours: float | None = None,
    now: datetime | None = None,
    jobs_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    job_map = jobs_by_run(jobs_payload)
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "runs": 0,
        "completed_runs": 0,
        "timed_completed_runs": 0,
        "completed_runs_missing_wall_timing": 0,
        "cancelled_runs": 0,
        "failed_runs": 0,
        "jobs": 0,
        "runs_with_job_timing": 0,
        "runs_missing_job_timing": 0,
        "untrusted_job_completion_timestamps": 0,
        "untrusted_run_completion_timestamps": 0,
        "runner_seconds": 0.0,
        "observed_job_span_seconds": 0.0,
        "peak_active_jobs": 0,
        "total_wall_seconds": 0.0,
        "max_wall_seconds": 0.0,
        "run_queue_seconds": 0.0,
        "job_queue_seconds": 0.0,
        "dependency_seconds": 0.0,
        "build_seconds": 0.0,
        "execution_seconds": 0.0,
        "other_step_seconds": 0.0,
        "cancelled_wall_seconds": 0.0,
        "cancelled_runner_seconds": 0.0,
        "failed_runner_seconds": 0.0,
        "events": {},
    })
    step_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "count": 0,
        "total_seconds": 0.0,
        "max_seconds": 0.0,
        "bucket": "other",
    })
    included = 0
    observed_wall_by_workflow: dict[str, list[float]] = defaultdict(list)
    source_runs = payload.get("workflow_runs", [])
    source_created = [parse_time(run.get("created_at")) for run in source_runs]
    source_created = [created for created in source_created if created is not None]
    oldest_available = min(source_created) if source_created else None
    newest_available = max(source_created) if source_created else None
    # Actions returns runs newest-first. Without an older-than-window row or a
    # complete repository census, the selected page count is only a sample.
    total_available = payload.get("total_count")
    threshold = now - timedelta(hours=since_hours) if since_hours is not None else None
    window_complete = (
        (oldest_available is not None and threshold is not None and oldest_available <= threshold)
        or (isinstance(total_available, int) and total_available <= len(source_runs))
    )

    for run in source_runs:
        created = parse_time(run.get("created_at"))
        if (
            since_hours is not None
            and created is not None
            and (now - created).total_seconds() > since_hours * 3600
        ):
            continue

        name = str(run.get("name") or run.get("workflow_id") or "unknown")
        row = groups[name]
        row["runs"] += 1
        event = str(run.get("event") or "unknown")
        row["events"][event] = row["events"].get(event, 0) + 1
        included += 1

        if run.get("status") == "completed":
            row["completed_runs"] += 1
        if run.get("conclusion") == "cancelled":
            row["cancelled_runs"] += 1
        if run.get("conclusion") == "failure":
            row["failed_runs"] += 1

        run_id = run.get("id")
        detailed_jobs = job_map.get(int(run_id), []) if run_id is not None else []
        bad_job_ends = sum(untrusted_job_completion_time(j) for j in detailed_jobs)
        row["untrusted_job_completion_timestamps"] += bad_job_ends
        started_value = run.get("run_started_at") or run.get("created_at")
        wall_seconds = observed_completed_wall_seconds(
            started_value, run.get("updated_at"))
        try:
            end = parse_time(run.get("updated_at"))
        except (AttributeError, TypeError, ValueError, OverflowError):
            end = None
        # GitHub may emit an impossible completed_at/updated_at on a Windows
        # self-hosted job across a local DST transition. Use the actual step
        # observations to flag the inconsistency, even when reported time
        # stops being "future" an hour later. Never fabricate a corrected end.
        untrusted_run_end = (
            bad_job_ends > 0 or
            (end is not None and end.tzinfo is not None
             and end > now + timedelta(minutes=5))
        )
        if run.get("status") == "completed" and untrusted_run_end:
            row["untrusted_run_completion_timestamps"] += 1
            wall_seconds = None
        # Missing/reversed/inconsistent timestamps must not bias averages
        # by becoming a fictitious zero or an extra hour of occupied time.
        if run.get("status") == "completed":
            if wall_seconds is None:
                row["completed_runs_missing_wall_timing"] += 1
            else:
                observed_wall_by_workflow[name].append(wall_seconds)
                row["timed_completed_runs"] += 1
                row["total_wall_seconds"] += wall_seconds
                row["max_wall_seconds"] = max(row["max_wall_seconds"], wall_seconds)
        row["run_queue_seconds"] += elapsed_seconds(
            run.get("created_at"), run.get("run_started_at")
        )
        if run.get("conclusion") == "cancelled" and wall_seconds is not None:
            row["cancelled_wall_seconds"] += wall_seconds

        run_id = run.get("id")
        if run_id is None:
            continue
        profile = job_parallelism_profile(job_map.get(int(run_id), []))
        if profile:
            row["runs_with_job_timing"] += 1
            row["runner_seconds"] += profile["runner_seconds"]
            row["observed_job_span_seconds"] += profile["observed_span_seconds"]
            row["peak_active_jobs"] = max(
                row["peak_active_jobs"], int(profile["peak_active_jobs"])
            )
            if run.get("conclusion") == "cancelled":
                row["cancelled_runner_seconds"] += profile["runner_seconds"]
            elif run.get("conclusion") == "failure":
                row["failed_runner_seconds"] += profile["runner_seconds"]
        else:
            row["runs_missing_job_timing"] += 1
        for job in job_map.get(int(run_id), []):
            row["jobs"] += 1
            row["job_queue_seconds"] += elapsed_seconds(
                job.get("created_at"), job.get("started_at")
            )
            for step in job.get("steps", []):
                seconds = elapsed_seconds(step.get("started_at"), step.get("completed_at"))
                if seconds <= 0:
                    continue
                step_name = str(step.get("name") or "unnamed")
                bucket = step_bucket(step_name)
                row[f"{bucket}_seconds" if bucket != "other" else "other_step_seconds"] += seconds

                stat = step_stats[(name, step_name)]
                stat["count"] += 1
                stat["total_seconds"] += seconds
                stat["max_seconds"] = max(stat["max_seconds"], seconds)
                stat["bucket"] = bucket

    workflows = []
    for name, row in groups.items():
        row["workflow"] = name
        measured = observed_wall_by_workflow[name]
        row["avg_wall_seconds"] = (
            row["total_wall_seconds"] / len(measured) if measured else None
        )
        row["p50_wall_seconds"] = median(measured) if measured else None
        row["p90_wall_seconds"] = p90_nearest_rank(measured)
        row["avg_run_queue_seconds"] = (
            row["run_queue_seconds"] / row["runs"] if row["runs"] else 0.0
        )
        row["avg_job_queue_seconds"] = (
            row["job_queue_seconds"] / row["jobs"] if row["jobs"] else 0.0
        )
        row["mean_active_jobs"] = (
            row["runner_seconds"] / row["observed_job_span_seconds"]
            if row["observed_job_span_seconds"] else 0.0
        )
        row["cancelled_fraction"] = (
            row["cancelled_runs"] / row["runs"] if row["runs"] else 0.0
        )
        top_steps = []
        for (workflow, step_name), stat in step_stats.items():
            if workflow != name:
                continue
            top_steps.append({
                "step": step_name,
                "bucket": stat["bucket"],
                "count": stat["count"],
                "total_seconds": stat["total_seconds"],
                "avg_seconds": stat["total_seconds"] / stat["count"],
                "max_seconds": stat["max_seconds"],
            })
        top_steps.sort(key=lambda item: (-item["total_seconds"], item["step"]))
        row["top_steps"] = top_steps[:10]
        workflows.append(row)

    workflows.sort(key=lambda row: (-row["total_wall_seconds"], row["workflow"]))
    return {
        "schema_version": 3,
        "included_runs": included,
        "since_hours": since_hours,
        "source_runs_fetched": len(source_runs),
        "source_total_available": total_available,
        "sample_oldest_created_at": oldest_available.isoformat() if oldest_available else None,
        "sample_newest_created_at": newest_available.isoformat() if newest_available else None,
        "window_census_complete": bool(window_complete),
        "possible_same_source_cross_workflow_builds":
            same_source_cross_workflow_build_candidates(payload, jobs_payload, since_hours, now),
        "workflows": workflows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CI runtime report",
        "",
        f"Included runs: {report['included_runs']}",
        f"Fetched runs: {report.get('source_runs_fetched', 'unknown')} of {report.get('source_total_available', 'unknown')} available",
        f"Sample created-at range: {report.get('sample_oldest_created_at') or 'unknown'} to {report.get('sample_newest_created_at') or 'unknown'}",
        f"Requested lookback fully covered: {'yes' if report.get('window_census_complete') else 'NO (sample only; do not infer 7-day totals)'}",
        "",
        "Completed runs with absent, reversed, future or step-inconsistent "
        "timestamps are excluded from observed wall-time averages and "
        "percentiles; p90 uses nearest rank. Inconsistent job intervals "
        "are excluded from runner occupancy, while valid step times remain available.",
        "| Workflow | Runs | Timed completed | Missing timing | Total min | Avg min | p50 min | p90 min | Max min | Run queue avg | Job queue avg | Dependencies | Build | Execution | Cancelled min | Failed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["workflows"]:
        lines.append(
            f"| {row['workflow']} | {row['runs']} | "
            f"{row['timed_completed_runs']} | {row['completed_runs_missing_wall_timing']} | "
            f"{row['total_wall_seconds']/60:.1f} | "
            f"{elapsed_minutes_or_unknown(row['avg_wall_seconds'])} | "
            f"{elapsed_minutes_or_unknown(row['p50_wall_seconds'])} | "
            f"{elapsed_minutes_or_unknown(row['p90_wall_seconds'])} | "
            f"{row['max_wall_seconds']/60:.1f} | "
            f"{row['avg_run_queue_seconds']/60:.1f} | {row['avg_job_queue_seconds']/60:.1f} | "
            f"{row['dependency_seconds']/60:.1f} | {row['build_seconds']/60:.1f} | "
            f"{row['execution_seconds']/60:.1f} | {row['cancelled_wall_seconds']/60:.1f} | "
            f"{row['failed_runs']} |"
        )

    bad_jobs = sum(row.get("untrusted_job_completion_timestamps", 0)
                   for row in report["workflows"])
    bad_runs = sum(row.get("untrusted_run_completion_timestamps", 0)
                   for row in report["workflows"])
    if bad_jobs or bad_runs:
        lines += ["", f"Timestamp anomalies excluded: {bad_jobs} job interval(s), "
                  f"{bad_runs} completed-run wall interval(s). "
                  "Inspect the raw Actions job steps before comparing runtime."]
    lines.extend([
        "",
        "## Observed parallel runner occupancy",
        "",
        "These are measured started/completed job spans, not dependency-DAG critical paths. "
        "Missing job intervals are excluded; queue time is reported separately.",
        "",
        "Missing or unstarted job intervals are excluded. Runner minutes are observed lower bounds, not billing totals.",
        "",
        "| Workflow | Timed runs | Missing timing | Runner min | Cancelled runner min | Failed runner min | Observed span min | Mean active jobs | Peak active jobs |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in report["workflows"]:
        lines.append(
            f"| {row['workflow']} | {row['runs_with_job_timing']} | {row['runs_missing_job_timing']} | "
            f"{row['runner_seconds']/60:.1f} | "
            f"{row['cancelled_runner_seconds']/60:.1f} | "
            f"{row['failed_runner_seconds']/60:.1f} | "
            f"{row['observed_job_span_seconds']/60:.1f} | "
            f"{row['mean_active_jobs']:.2f} | {row['peak_active_jobs']} |"
        )

    lines.extend([
        "",
        "## Possible same-source duplicate build work (review only)",
        "",
        "Pairs use observed timed build-like steps within two hours on the same "
        "Actions head SHA and across different workflows. This is NOT proof "
        "of identical checkout/PE/ZIP, redundant required checks or avoidable "
        "runner charges. Missing step timing can hide candidates.",
    ])
    for group in report.get("possible_same_source_cross_workflow_builds", []):
        lines.append(
            "- " + group["head_sha"][:12] + ": "
            + ", ".join(group["workflow_names"])
            + "; run ids=" + ",".join(str(x) for x in group["run_ids"])
            + "; observed build-like step minutes="
            + str(round(group["observed_build_step_seconds"] / 60, 2))
            + "; **manual review only**"
        )

    for row in report["workflows"]:
        if not row["top_steps"]:
            continue
        lines.extend(["", f"## {row['workflow']} top measured steps", ""])
        lines.append("| Step | Class | Samples | Total min | Avg s | Max s |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for step in row["top_steps"]:
            lines.append(
                f"| {step['step']} | {step['bucket']} | {step['count']} | "
                f"{step['total_seconds']/60:.1f} | {step['avg_seconds']:.1f} | "
                f"{step['max_seconds']:.1f} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_json", type=Path)
    parser.add_argument("--jobs-json", type=Path)
    parser.add_argument("--since-hours", type=float, default=168)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()

    jobs_payload = (
        json.loads(args.jobs_json.read_text()) if args.jobs_json else None
    )
    report = summarize(
        json.loads(args.runs_json.read_text()),
        args.since_hours,
        jobs_payload=jobs_payload,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    rendered = markdown(report)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
