#!/usr/bin/env python3
"""Summarize GitHub Actions run, job, and step wall-clock timing."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
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


def step_bucket(name: str) -> str:
    lowered = name.lower()
    if (
        "apt" in lowered
        or "package dependenc" in lowered
        or ("install" in lowered and "dependenc" in lowered)
    ):
        return "dependency"
    if any(token in lowered for token in (
        "build", "compile", "configure", "scaffold", "cmake", "generate"
    )):
        return "build"
    if any(token in lowered for token in (
        "acceptance", "route", "smoke", "capture", "boot", "prove", "compare",
        "regression", "evidence shard", "replay"
    )):
        return "execution"
    return "other"


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



def job_parallelism_profile(jobs: list[dict[str, Any]]) -> dict[str, float] | None:
    """Observed runner occupancy from actual started/completed job intervals.

    Ending a job at the same instant another starts does not constitute
    concurrent work. Skipped, unstarted and malformed intervals contribute
    no runner seconds. This is an *observed span*, not the dependency-DAG
    critical path or GitHub queue time.
    """
    intervals: list[tuple[datetime, datetime]] = []
    for job in jobs:
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
        "cancelled_runs": 0,
        "failed_runs": 0,
        "jobs": 0,
        "runs_with_job_timing": 0,
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
    })
    step_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "count": 0,
        "total_seconds": 0.0,
        "max_seconds": 0.0,
        "bucket": "other",
    })
    included = 0

    for run in payload.get("workflow_runs", []):
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
        included += 1

        if run.get("status") == "completed":
            row["completed_runs"] += 1
        if run.get("conclusion") == "cancelled":
            row["cancelled_runs"] += 1
        if run.get("conclusion") == "failure":
            row["failed_runs"] += 1

        started_value = run.get("run_started_at") or run.get("created_at")
        wall_seconds = elapsed_seconds(started_value, run.get("updated_at"))
        # A queued or running workflow's updated_at is not an end time.
        # Including it silently understates the baseline and contaminates
        # averages used to decide which gate needs optimization.
        if run.get("status") == "completed":
            row["total_wall_seconds"] += wall_seconds
            row["max_wall_seconds"] = max(row["max_wall_seconds"], wall_seconds)
        row["run_queue_seconds"] += elapsed_seconds(
            run.get("created_at"), run.get("run_started_at")
        )
        if run.get("conclusion") == "cancelled":
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
        row["avg_wall_seconds"] = (
            row["total_wall_seconds"] / row["completed_runs"] if row["completed_runs"] else 0.0
        )
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
        "schema_version": 2,
        "included_runs": included,
        "since_hours": since_hours,
        "workflows": workflows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CI runtime report",
        "",
        f"Included runs: {report['included_runs']}",
        "",
        "| Workflow | Runs | Total min | Avg min | Max min | Run queue avg | Job queue avg | Dependencies | Build | Execution | Cancelled min | Failed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["workflows"]:
        lines.append(
            f"| {row['workflow']} | {row['runs']} | {row['total_wall_seconds']/60:.1f} | "
            f"{row['avg_wall_seconds']/60:.1f} | {row['max_wall_seconds']/60:.1f} | "
            f"{row['avg_run_queue_seconds']/60:.1f} | {row['avg_job_queue_seconds']/60:.1f} | "
            f"{row['dependency_seconds']/60:.1f} | {row['build_seconds']/60:.1f} | "
            f"{row['execution_seconds']/60:.1f} | {row['cancelled_wall_seconds']/60:.1f} | "
            f"{row['failed_runs']} |"
        )

    lines.extend([
        "",
        "## Observed parallel runner occupancy",
        "",
        "These are measured started/completed job spans, not dependency-DAG critical paths. "
        "Missing job intervals are excluded; queue time is reported separately.",
        "",
        "| Workflow | Timed runs | Runner min | Observed span min | Mean active jobs | Peak active jobs |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["workflows"]:
        lines.append(
            f"| {row['workflow']} | {row['runs_with_job_timing']} | "
            f"{row['runner_seconds']/60:.1f} | "
            f"{row['observed_job_span_seconds']/60:.1f} | "
            f"{row['mean_active_jobs']:.2f} | {row['peak_active_jobs']} |"
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
