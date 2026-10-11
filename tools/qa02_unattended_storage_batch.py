#!/usr/bin/env python3
"""Aggregate ORIGINAL QA02 coordinator-race and fault-recovery receipts.

This is transport, never a third authority for Windows, original/native course
completion, gameplayed 2P, physical hardware or release ledger admission.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "ur-qa02-unattended-storage-supercampaign/1"
JOBS = ("success", "failure", "cancelled", "skipped")


def validated(path: Path, source: str, kind: str, trials: int) -> dict:
    if not path.is_file():
        raise ValueError("missing original " + kind + " machine result")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(kind + " original aggregate is not an object")
    if kind == "c12":
        expected = {
            "schema": "ur-qa02-c12-campaign-aggregate/1",
            "source_commit": source, "requested_trials": trials * 4,
            "observed_trials": trials * 4, "passed_trials": trials * 4,
            "failed_trials": 0, "missing_shards": [], "invalid_shards": [],
            "failing_shards": [], "disposition": "completed_positive",
            "release_gate_credit": 0,
        }
        hash_field = "binary_sha256"
    else:
        expected = {
            "schema": "ur-qa02-recovery-campaign/1",
            "source_sha": source, "requested_suite_count": 5,
            "completed_suite_count": 5,
            "requested_iterations": trials * 5,
            "observed_iterations": trials * 5,
            "passed_iterations": trials * 5,
            "failed_iterations": 0,
            "issues": [], "disposition": "completed_positive",
            "release_gate_credit": 0, "physical_hardware_covered": False,
            "actual_guest_gameplay_covered": False,
        }
        hash_field = "binary_sha256"
    for field, expected_value in expected.items():
        actual = value.get(field)
        if type(actual) is not type(expected_value) or actual != expected_value:
            raise ValueError(kind + " unaccepted population/condition: " + field)
    if not isinstance(value.get(hash_field), str) or not SHA256.fullmatch(value[hash_field]):
        raise ValueError(kind + " missing exact built fixture SHA-256")
    if kind == "recovery":
        shards = value.get("suites")
        if type(shards) is not list or len(shards) != 5 or len({
                row.get("suite") for row in shards if isinstance(row, dict)}) != 5:
            raise ValueError("recovery subcampaign did not contain five distinct case receipts")
    return value


def make_result(source_sha: str, run_id: str, trials: int,
                c12_job: str, recovery_job: str,
                c12_path: Path, recovery_path: Path) -> dict:
    if not SHA1.fullmatch(source_sha) or not run_id.isdecimal() or not run_id:
        raise ValueError("invalid source or actual GitHub run identity")
    if type(trials) is not int or trials not in (10, 100, 500):
        raise ValueError("unsupported deliberately bounded cohort")
    if c12_job not in JOBS or recovery_job not in JOBS:
        raise ValueError("invalid underlying workflow run job status")
    issues = []
    receipts = {}
    for kind, job, path in (("c12", c12_job, c12_path),
                            ("recovery", recovery_job, recovery_path)):
        if job != "success":
            issues.append(f"{kind}: reusable child workflow {job}")
        try:
            receipts[kind] = validated(path, source_sha, kind, trials)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            issues.append(f"{kind}: {exc}")
    return {
        "schema": SCHEMA, "source_commit": source_sha, "github_run_id": run_id,
        "requested_repetitions_per_scenario": trials,
        "total_expected_real_process_trials": 9 * trials,
        "verified_successful_real_process_trials": (
            9 * trials if not issues else 0
        ),
        "child_jobs": {"ownership_races": c12_job, "fault_recovery": recovery_job},
        "underlying_binary_sha256": {
            kind: report["binary_sha256"] for kind, report in receipts.items()
        },
        "component_receipts": {
            kind: {
                "disposition": report["disposition"],
                "requested_trials": report["requested_trials"]
                if kind == "c12" else report["requested_iterations"],
                "observed_trials": report["observed_trials"]
                if kind == "c12" else report["observed_iterations"],
            } for kind, report in receipts.items()
        },
        "issues": issues,
        "disposition": "completed_positive" if not issues else "incomplete_or_failed",
        "release_gate_credit": 0, "physical_hardware_witness": False,
        "authentic_guest_2p_match_played": False,
        "complete_original_native_event_equality": False,
        "scope": ("This is real OS-process QA02/03 production-store "
                  "contention, crash and recovery: not complete guest gameplay, "
                  "an integrated Windows build, independent original/native "
                  "event acceptance, or real physical hardware."),
    }


def present(report: dict) -> str:
    result = ["## QA-02 unattended storage stress", "",
              f"**{report['disposition']}**",
              f"0/{report['release_gate_credit']} is not a release metric.",
              f"Real OS-process trials requested: {report['total_expected_real_process_trials']}",
              f"Full-population verified trials: {report['verified_successful_real_process_trials']}",
              f"Source: \u0060{report['source_commit']}\u0060, Actions run: {report['github_run_id']}",
              "", "| Existing cohort | Job | Receipt | Population |",
              "| --- | --- | --- | --- |"]
    for kind, job in (("c12", report["child_jobs"]["ownership_races"]),
                       ("recovery", report["child_jobs"]["fault_recovery"])):
        receipt = report["component_receipts"].get(kind)
        result.append(f"| {kind} | {job} | "
                      f"{receipt['disposition'] if receipt else 'missing or invalid'} | "
                      f"{receipt['observed_trials'] if receipt else 0}/"
                      f"{receipt['requested_trials'] if receipt else '?'} |")
    result.extend(["", "**No release, guest-gameplay or physical device credit.**", ""])
    result.extend(f"- {problem}" for problem in report["issues"])
    return "\n".join(result) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--trials", type=int, required=True)
    p.add_argument("--c12-job", choices=JOBS, required=True)
    p.add_argument("--recovery-job", choices=JOBS, required=True)
    p.add_argument("--c12", type=Path, required=True)
    p.add_argument("--recovery", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    args = p.parse_args()
    result = make_result(args.source_sha, args.run_id, args.trials, args.c12_job,
                         args.recovery_job, args.c12, args.recovery)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    args.summary.write_text(present(result))
    return 0 if result["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
