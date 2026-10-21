"""Bounded *actual job interval* sampler for cancelled GitHub Actions runs.

This is neither a daily census nor an estimate of billable minutes. Cancelled
runs without started jobs have zero observed occupancy in the sampled latest
attempt; incomplete/paginated job lists are UNKNOWN, not zero.
"""
from collections import defaultdict
import re

try:
    from .report_ci_runtime import job_parallelism_profile
except ImportError:
    from report_ci_runtime import job_parallelism_profile


def sample_cancelled_jobs(read, base, runs, *, limit=8):
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be 1..20")
    if type(runs) is not list:
        raise ValueError("runs must be an array")
    selected = [run for run in runs if isinstance(run, dict)
                and run.get("conclusion") == "cancelled"][:limit]
    totals = defaultdict(lambda: {"runs": 0, "runner_seconds": 0.0,
                                  "zero_started_jobs": 0})
    complete = 0
    unknown = []
    for run in selected:
        run_id = run.get("id")
        if type(run_id) is not int or run_id < 1:
            unknown.append({"run_id": None, "reason": "missing run ID"})
            continue
        try:
            data = read(base + f"/actions/runs/{run_id}/jobs?per_page=100&page=1")
            jobs = data["jobs"]
            count = data.get("total_count")
            if not isinstance(jobs, list) or any(not isinstance(j, dict) for j in jobs):
                raise ValueError("invalid job list")
            if len(jobs) >= 100 or (type(count) is int and count > len(jobs)):
                raise ValueError("job census not complete")
            profile = job_parallelism_profile(jobs)
            secs = profile["runner_seconds"] if profile else 0.0
            workflow = str(run.get("name") or "unnamed workflow")[:120]
            totals[workflow]["runs"] += 1
            totals[workflow]["runner_seconds"] += secs
            if profile is None:
                totals[workflow]["zero_started_jobs"] += 1
            complete += 1
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            unknown.append({"run_id": run_id, "reason": str(error)[:90]})
    total_seconds = sum(row["runner_seconds"] for row in totals.values())
    return {
        "scope": "latest_cancelled_up_to_8_from_latest_100_runs_last_attempt_jobs_only",
        "selected": len(selected),
        "verified_job_censuses": complete,
        "unknown_censuses": unknown,
        "unselected_cancelled_runs": max(
            0, sum(isinstance(r, dict) and r.get("conclusion") == "cancelled"
                   for r in runs) - len(selected)),
        "observed_runner_seconds": round(total_seconds, 3),
        "source": "actual_gitHub_job_started_at_and_completed_at",
        "not_billable_minutes": True,
        "not_evidence_of_waste": True,
        "workflows": [
            {"workflow": name, **row}
            for name, row in sorted(totals.items(),
                                    key=lambda kv: (-kv[1]["runner_seconds"], kv[0]))
        ],
    }
