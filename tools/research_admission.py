#!/usr/bin/env python3
"""Runner-aware admission control for the cumulative research coordinator.

Scheduling policy only. Nothing here is scientific evidence, changes a seed,
plan identity or fingerprint epoch, or grants release credit.

Facts this module is built around:

* The account has a 20-runner concurrency *ceiling* shared by every repository.
  GitHub offers no reservation and cannot preempt a running hosted job.
  Concurrency groups serialize one named group; they reserve nothing.
* ``GITHUB_TOKEN`` sees only this repository. Other repositories are invisible,
  so a fixed reserve is assumed for them rather than treating them as idle.
* Admission is a point-in-time check made *before* the ledger reserves a seed
  window. A deferred run therefore consumes no seeds and writes no ledger row.
  It cannot stop later jobs from contending: it only declines to start them.

Decisions: ``admit``, ``admit_downsized`` (only frontier shard *parallelism*,
never the case population), or ``defer``. ``force`` records the snapshot but
always admits the exact request (manual operator override).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path

SCHEMA = "ur-research-admission/1"
USAGE_SCHEMA = "ur-research-runner-usage/1"
CAMPAIGNS = ("native-2p", "windows", "fault-recovery",
             "graphics", "performance", "original-native", "frontier")

ACCOUNT_RUNNER_LIMIT = 20
# Other repositories on the account cannot be observed with GITHUB_TOKEN.
UNSEEN_REPOSITORY_RESERVE = 4
# Keep enough room for four agents' PR feedback bursts.
AGENT_HEADROOM = 6
# A job queued this long means hosted capacity is already exhausted.
QUEUE_SATURATION_SECONDS = 180
# "Large" campaigns run only when development CI is nearly idle.
LARGE_RUNNER_MINUTES = 240
QUIET_ACTIVE_JOBS = 4
MAX_RUNS_INSPECTED = 40

# Peak simultaneous runners per lane (max-parallel of its widest job) and a
# rough per-unit cost from measured runs. Frontier peak is its parallel knob.
PEAK_RUNNERS = {"native-2p": 2, "windows": 2, "fault-recovery": 3,
                "graphics": 1, "performance": 1, "original-native": 2}
# Measured: 100-case frontier ~40 experiment runner-minutes (runs 38438864232,
# 38446393623); 15-minute graphics ~16; candidate builds ~3-6.
FRONTIER_RUNNER_MINUTES_PER_CASE = 0.4

# Files whose change can plausibly alter a producer's behaviour. Used only to
# avoid automatically re-running a lane whose last receipt failed while nothing
# in its producer changed. A heuristic, never evidence identity.
PRODUCER_PATHS = {
    "native-2p": (".github/workflows/qa02-native-2p-seeded-endurance.yml",
                  ".github/workflows/modern-shared-native-acceptance.yml",
                  "tools/qa02_native_2p_seeded_endurance.py"),
    "windows": (".github/workflows/baldosa-windows-reliability-campaign.yml",
                ".github/workflows/baldosa-windows-native-bridge.yml",
                "tools/qa_baldosa_windows_reliability_batch.py"),
    "fault-recovery": (".github/workflows/qa02-real-fault-endurance.yml",
                       "tools/qa02_real_fault_endurance.py",
                       "tools/qa02_recovery_campaign.py"),
    "graphics": (".github/workflows/qa-cumulative-native-metrics.yml",
                 ".github/workflows/modern-shared-native-acceptance.yml",
                 "tools/qa_cumulative_native_metrics.py"),
    "performance": (".github/workflows/qa-cumulative-native-metrics.yml",
                    ".github/workflows/modern-shared-native-acceptance.yml",
                    "tools/qa_cumulative_native_metrics.py"),
    "original-native": (".github/workflows/qa01-event-campaign.yml",
                        "tools/qa01_event_campaign.py",
                        "tools/probe_original_event_complete.py",
                        "tools/baldosa_qa_dense_scene_input_patch.py"),
    "frontier": (".github/workflows/qa-adaptive-frontier.yml",
                 ".github/workflows/modern-shared-native-acceptance.yml",
                 "tools/qa_adaptive_frontier.py",
                 "tools/qa_frontier_handoff.py"),
}
FAILED = "incomplete_or_failed"


def _parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _os_class(labels: list) -> str:
    text = " ".join(str(label).lower() for label in labels or ())
    if "windows" in text:
        return "windows"
    if "macos" in text:
        return "macos"
    return "linux"


def _family(name: object) -> str:
    return str(name or "").split(" (", 1)[0]


def summarize_jobs(runs: list[dict], now: dt.datetime, *,
                   exclude_run_id: int | None = None,
                   truncated: bool = False) -> dict:
    """Reduce ``[{"run": run, "jobs": [job, ...]}, ...]`` to a snapshot.

    macOS has its own smaller account limit and is reported but excluded from
    the shared Linux/Windows ceiling arithmetic.
    """
    active = {"linux": 0, "windows": 0, "macos": 0}
    queued = {"linux": 0, "windows": 0, "macos": 0}
    throttled = {"linux": 0, "windows": 0, "macos": 0}
    oldest = 0
    research_active = 0
    inspected = 0
    for entry in runs:
        run = entry["run"]
        if exclude_run_id is not None and run.get("id") == exclude_run_id:
            continue
        inspected += 1
        is_research = "qa-cumulative-research" in str(run.get("path", ""))
        jobs = list(entry.get("jobs", ()))
        # A matrix sibling "queued" while another member of the same matrix
        # runs is normally held by that matrix's own max-parallel, not by a
        # runner shortage. Count it as pending work but not as saturation.
        running_families = {_family(j.get("name")) for j in jobs
                            if j.get("status") == "in_progress"}
        for job in jobs:
            status = job.get("status")
            kind = _os_class(job.get("labels"))
            if status == "in_progress":
                active[kind] += 1
                research_active += is_research
            elif status in ("queued", "waiting", "pending"):
                if _family(job.get("name")) in running_families:
                    throttled[kind] += 1
                    continue
                queued[kind] += 1
                created = job.get("created_at")
                if created:
                    age = int((now - _parse_time(created)).total_seconds())
                    oldest = max(oldest, age)
    return {
        "schema": SCHEMA, "observed_at": now.isoformat(),
        "runs_inspected": inspected, "truncated": bool(truncated),
        "active_jobs": active, "queued_jobs": queued,
        "matrix_throttled_jobs": throttled,
        "oldest_queued_seconds": oldest,
        "research_active_jobs": research_active,
        "unseen_repository_reserve": UNSEEN_REPOSITORY_RESERVE,
    }


def _shared(counts: dict) -> int:
    return counts["linux"] + counts["windows"]


def frontier_runner_minutes(cases: int) -> float:
    return cases * FRONTIER_RUNNER_MINUTES_PER_CASE


def expected_runner_minutes(request: dict) -> float:
    campaign = request["campaign"]
    if campaign == "frontier":
        return frontier_runner_minutes(int(request.get("frontier_cases", 100)))
    if campaign == "windows":
        # Four shards, roughly 2.5 minutes per Windows journey.
        return 4 * 2.5 * int(request.get("windows_trials", 3))
    return PEAK_RUNNERS[campaign] * int(request.get("minutes", 15))


def decide(snapshot: dict | None, request: dict) -> dict:
    """Pure admission decision. ``request`` keys: campaign, event, admission,
    frontier_parallel, frontier_cases, minutes, windows_trials."""
    campaign = request["campaign"]
    if campaign not in CAMPAIGNS:
        raise ValueError("unknown campaign")
    event = request.get("event", "workflow_dispatch")
    mode = request.get("admission", "auto")
    if mode not in ("auto", "force"):
        raise ValueError("admission must be auto or force")
    want_parallel = int(request.get("frontier_parallel", 2))
    if want_parallel not in (1, 2, 4):
        raise ValueError("frontier_parallel must be 1, 2 or 4")
    cost = expected_runner_minutes(request)
    base = {"schema": SCHEMA, "campaign": campaign, "event": event,
            "admission": mode, "requested_frontier_parallel": want_parallel,
            "expected_runner_minutes": round(cost, 1), "snapshot": snapshot,
            "scientific_identity_changed": False, "release_gate_credit": 0}

    def result(decision: str, parallel: int, reason: str) -> dict:
        return {**base, "decision": decision, "admitted": decision != "defer",
                "frontier_parallel": parallel, "reason": reason}

    if mode == "force":
        return result("admit", want_parallel, "operator force: exact request admitted")
    if snapshot is None:
        if event == "schedule":
            return result("defer", want_parallel,
                          "capacity unobservable; scheduled research defers")
        capped = min(want_parallel, 2)
        return result("admit" if capped == want_parallel else "admit_downsized", capped,
                      "capacity unobservable; manual dispatch admitted at <=2 frontier shards")
    busy = _shared(snapshot["active_jobs"]) + _shared(snapshot["queued_jobs"])
    free = ACCOUNT_RUNNER_LIMIT - UNSEEN_REPOSITORY_RESERVE - busy
    spare = free - AGENT_HEADROOM
    queued = _shared(snapshot["queued_jobs"])
    if queued and snapshot.get("oldest_queued_seconds", 0) >= QUEUE_SATURATION_SECONDS:
        return result("defer", want_parallel,
                      f"{queued} job(s) already queued >= {QUEUE_SATURATION_SECONDS}s: capacity saturated")
    if cost > LARGE_RUNNER_MINUTES and (
            _shared(snapshot["active_jobs"]) > QUIET_ACTIVE_JOBS or queued):
        return result("defer", want_parallel,
                      f"large campaign (~{cost:.0f} runner-min) requires <= {QUIET_ACTIVE_JOBS} "
                      "active jobs and an empty queue; run it in a quiet period or split it into batches")
    if event == "schedule":
        # Scheduled research never competes with an active development burst.
        spare -= 2
    need = 1 if campaign == "frontier" else PEAK_RUNNERS[campaign]
    if spare < need:
        return result("defer", want_parallel,
                      f"estimated spare runners {spare} < peak need {need} after "
                      f"{UNSEEN_REPOSITORY_RESERVE} unseen-repo and {AGENT_HEADROOM} agent reserve")
    if campaign != "frontier":
        return result("admit", want_parallel, f"spare runners {spare} >= peak need {need}")
    allowed = max(p for p in (1, 2, 4) if p <= max(1, min(want_parallel, spare)))
    if allowed == want_parallel:
        return result("admit", allowed, f"spare runners {spare} allow {allowed} frontier shards")
    return result("admit_downsized", allowed,
                  f"spare runners {spare}: frontier shard parallelism {want_parallel} -> {allowed} "
                  "(scheduling only; same cases, seeds and plan)")


def producer_digest(root: Path, campaign: str) -> str:
    h = hashlib.sha256()
    for rel in PRODUCER_PATHS[campaign]:
        path = root / rel
        data = path.read_bytes() if path.is_file() else b"<missing>"
        h.update(rel.encode() + b"\0" + hashlib.sha256(data).digest())
    return h.hexdigest()


def auto_lane(records: list[dict], digests: dict[str, str]) -> tuple[str, dict]:
    """Fair, failure-aware rotation for ``auto``.

    Least-recently-recorded lane first (never-run lanes before all others,
    ties in CAMPAIGNS order). A lane whose latest coordinator receipt failed is
    *ineligible* while its recorded producer digest still matches: re-running
    an unchanged failing producer adds cost, not information. Legacy failed
    receipts without a digest cannot prove "unchanged"; they stay eligible
    but rank after every healthy lane.
    """
    last_index: dict[str, int] = {}
    last_row: dict[str, dict] = {}
    for index, row in enumerate(records):
        if row.get("origin") == "coordinator" and row.get("campaign") in CAMPAIGNS:
            last_index[row["campaign"]] = index
            last_row[row["campaign"]] = row
    ranked = []
    excluded = {}
    for order, lane in enumerate(CAMPAIGNS):
        row = last_row.get(lane)
        failed = row is not None and row.get("disposition") == FAILED
        recorded = row.get("producer_digest") if row else None
        if failed and recorded is not None and recorded == digests.get(lane):
            excluded[lane] = "latest receipt failed and producer files are unchanged"
            continue
        legacy_failed = failed and recorded is None
        ranked.append((legacy_failed, last_index.get(lane, -1), order, lane))
    if not ranked:
        raise ValueError("every lane's latest receipt failed on an unchanged producer; "
                         "investigate before automatic research resumes")
    ranked.sort()
    return ranked[0][3], excluded


def _api(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def live_snapshot(repo: str, token: str, exclude_run_id: int | None,
                  api: str = "https://api.github.com") -> dict:
    runs = []
    for status in ("in_progress", "queued"):
        data = _api(f"{api}/repos/{repo}/actions/runs?status={status}&per_page=100", token)
        runs.extend(data.get("workflow_runs", ()))
    seen, unique = set(), []
    for run in runs:
        if run["id"] not in seen:
            seen.add(run["id"])
            unique.append(run)
    truncated = len(unique) > MAX_RUNS_INSPECTED
    entries = []
    for run in unique[:MAX_RUNS_INSPECTED]:
        if exclude_run_id is not None and run["id"] == exclude_run_id:
            continue
        jobs = _api(f"{api}/repos/{repo}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100",
                    token).get("jobs", ())
        entries.append({"run": run, "jobs": jobs})
    return summarize_jobs(entries, dt.datetime.now(dt.timezone.utc),
                          exclude_run_id=exclude_run_id, truncated=truncated)


def summarize_usage(jobs: list[dict], *, exclude_names: tuple[str, ...] = ()) -> dict:
    """Runner-minutes actually consumed by completed/started jobs of one run."""
    minutes = {"linux": 0.0, "windows": 0.0, "macos": 0.0}
    counted = 0
    for job in jobs:
        if job.get("name") in exclude_names or job.get("conclusion") == "skipped":
            continue
        start, end = job.get("started_at"), job.get("completed_at")
        if not start or not end:
            continue
        seconds = (_parse_time(end) - _parse_time(start)).total_seconds()
        if seconds < 0:
            continue
        minutes[_os_class(job.get("labels"))] += seconds / 60
        counted += 1
    return {"schema": USAGE_SCHEMA, "jobs_counted": counted,
            "runner_minutes": {k: round(v, 1) for k, v in minutes.items()},
            "total_runner_minutes": round(sum(minutes.values()), 1),
            "measured_by": "job started_at/completed_at; excludes the recording job itself"}


def validate_usage(usage: dict) -> None:
    rm = usage.get("runner_minutes") if type(usage) is dict else None
    if (type(usage) is not dict or usage.get("schema") != USAGE_SCHEMA
            or type(usage.get("jobs_counted")) is not int or usage["jobs_counted"] < 0
            or type(rm) is not dict or set(rm) != {"linux", "windows", "macos"}
            or any(type(v) not in (int, float) or v < 0 for v in rm.values())
            or type(usage.get("total_runner_minutes")) not in (int, float)
            or abs(sum(rm.values()) - usage["total_runner_minutes"]) > 0.5):
        raise ValueError("invalid runner usage receipt")


def _write_outputs(path: Path, values: dict) -> None:
    with path.open("a", encoding="utf8") as out:
        for key, value in values.items():
            out.write(f"{key}={value}\n")


def summary_markdown(decision: dict) -> str:
    snap = decision.get("snapshot")
    lines = [f"### Research admission: **{decision['decision']}** ({decision['campaign']})", "",
             decision["reason"], ""]
    if decision["decision"] == "defer":
        lines += ["No seed window was reserved and no ledger row will be written. "
                  "Re-dispatch later, or use `admission: force` for a deliberate override.", ""]
    if snap:
        lines.append(f"Observed this repo: active {snap['active_jobs']}, queued {snap['queued_jobs']}, "
                     f"oldest queued {snap['oldest_queued_seconds']}s; other repos assumed "
                     f"{snap['unseen_repository_reserve']} busy. Snapshot, not a reservation.")
    lines.append(f"Frontier shard parallelism: {decision['requested_frontier_parallel']} requested, "
                 f"{decision['frontier_parallel']} admitted. Expected ~{decision['expected_runner_minutes']} runner-min.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--repo", required=True)
    snap.add_argument("--exclude-run-id", type=int)
    snap.add_argument("--out", type=Path, required=True)
    dec = sub.add_parser("decide")
    dec.add_argument("--ledger", type=Path, required=True)
    dec.add_argument("--root", type=Path, default=Path("."))
    dec.add_argument("--snapshot", type=Path)
    dec.add_argument("--selected", choices=(*CAMPAIGNS, "auto"), required=True)
    dec.add_argument("--event", required=True)
    dec.add_argument("--admission", choices=("auto", "force"), default="auto")
    dec.add_argument("--frontier-parallel", type=int, default=2)
    dec.add_argument("--frontier-cases", type=int, default=100)
    dec.add_argument("--minutes", type=int, default=15)
    dec.add_argument("--windows-trials", type=int, default=3)
    dec.add_argument("--out", type=Path, required=True)
    dec.add_argument("--gha-output", type=Path)
    dec.add_argument("--summary", type=Path)
    use = sub.add_parser("usage")
    use.add_argument("--repo", required=True)
    use.add_argument("--run-id", type=int, required=True)
    use.add_argument("--exclude-job", action="append", default=[])
    use.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    token = os.environ.get("GH_TOKEN", "")
    if args.mode == "snapshot":
        data = live_snapshot(args.repo, token, args.exclude_run_id)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        print(json.dumps(data, sort_keys=True))
        return 0
    if args.mode == "usage":
        jobs, page = [], 1
        while True:
            data = _api(f"https://api.github.com/repos/{args.repo}/actions/runs/"
                        f"{args.run_id}/jobs?filter=latest&per_page=100&page={page}", token)
            jobs.extend(data.get("jobs", ()))
            if len(jobs) >= data.get("total_count", 0) or not data.get("jobs"):
                break
            page += 1
        usage = summarize_usage(jobs, exclude_names=tuple(args.exclude_job))
        validate_usage(usage)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(usage, indent=2, sort_keys=True) + "\n")
        print(json.dumps(usage, sort_keys=True))
        return 0
    ledger = json.loads(args.ledger.read_text())
    digests = {lane: producer_digest(args.root, lane) for lane in CAMPAIGNS}
    excluded = {}
    campaign = args.selected
    if campaign == "auto":
        campaign, excluded = auto_lane(ledger.get("records", []), digests)
    snapshot = None
    if args.snapshot is not None and args.snapshot.is_file():
        snapshot = json.loads(args.snapshot.read_text())
    decision = decide(snapshot, {
        "campaign": campaign, "event": args.event, "admission": args.admission,
        "frontier_parallel": args.frontier_parallel, "frontier_cases": args.frontier_cases,
        "minutes": args.minutes, "windows_trials": args.windows_trials})
    decision["selected"] = args.selected
    decision["auto_excluded_lanes"] = excluded
    decision["producer_digest"] = digests[campaign]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    if args.gha_output:
        _write_outputs(args.gha_output, {
            "admitted": str(decision["admitted"]).lower(), "campaign": campaign,
            "frontier_parallel": decision["frontier_parallel"],
            "producer_digest": decision["producer_digest"]})
    if args.summary:
        with args.summary.open("a", encoding="utf8") as out:
            out.write(summary_markdown(decision))
    print(f"ADMISSION {decision['decision']} {campaign}: {decision['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
