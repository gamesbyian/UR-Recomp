#!/usr/bin/env python3
"""Summarize GitHub Actions run duration from an exported Actions-runs payload."""

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

def summarize(payload: dict[str, Any], since_hours: float | None = None, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "runs":0,"completed_runs":0,"cancelled_runs":0,"failed_runs":0,
        "total_wall_seconds":0.0,"max_wall_seconds":0.0,
    })
    included = 0
    for run in payload.get("workflow_runs", []):
        created = parse_time(run.get("created_at"))
        if since_hours is not None and created is not None and (now - created).total_seconds() > since_hours * 3600:
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
        start = parse_time(run.get("run_started_at") or run.get("created_at"))
        end = parse_time(run.get("updated_at"))
        if start and end and end >= start:
            seconds = (end - start).total_seconds()
            row["total_wall_seconds"] += seconds
            row["max_wall_seconds"] = max(row["max_wall_seconds"], seconds)
    workflows = []
    for name, row in groups.items():
        row["workflow"] = name
        row["avg_wall_seconds"] = row["total_wall_seconds"] / row["runs"] if row["runs"] else 0.0
        row["cancelled_fraction"] = row["cancelled_runs"] / row["runs"] if row["runs"] else 0.0
        workflows.append(row)
    workflows.sort(key=lambda row: (-row["total_wall_seconds"], row["workflow"]))
    return {"schema_version":1,"included_runs":included,"since_hours":since_hours,"workflows":workflows}

def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CI runtime report","",f"Included runs: {report['included_runs']}","",
        "| Workflow | Runs | Total min | Avg min | Max min | Cancelled | Failed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["workflows"]:
        lines.append(
            f"| {row['workflow']} | {row['runs']} | {row['total_wall_seconds']/60:.1f} | "
            f"{row['avg_wall_seconds']/60:.1f} | {row['max_wall_seconds']/60:.1f} | "
            f"{row['cancelled_runs']} | {row['failed_runs']} |"
        )
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_json", type=Path)
    parser.add_argument("--since-hours", type=float, default=168)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    report = summarize(json.loads(args.runs_json.read_text()), args.since_hours)
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
