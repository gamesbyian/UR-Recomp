#!/usr/bin/env python3
"""Bounded real-process seeded fault-recovery endurance; no game/release credit.

Reuses the existing production-store fault fixture and its five established
C09/C14/C15/C16/QA03 process/death/restart oracles. Each 10-case batch uses
a new deterministic jitter seed and separate real-process data roots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_recovery_campaign as original

SCHEMA = "ur-qa02-seeded-fault-endurance/1"
SUITES = original.SUITES
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MINUTES = (15, 60, 120)
CHUNK_SIZE = 10
MAX_CHUNKS = 20000


def digest_object(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def case_seed(base_seed: int, suite: str, index: int) -> int:
    if base_seed < 50000000:
        # Preserve the reproducibility of previously published noncumulative
        # 20261011-style historical experiments because their base is below
        # the reserved cumulative namespace.
        return base_seed + SUITES.index(suite) * 1000003 + index * 1009
    if not 0 <= index < MAX_CHUNKS:
        raise ValueError("fault jitter index exceeds reserved seed namespace")
    # Bijective integer seed over cumulative (base, source suite, chunk).
    # Python random.Random accepts arbitrarily large integer seeds, while
    # only the externally supplied base has the original 8-digit UI bound.
    return base_seed * (len(SUITES)*MAX_CHUNKS) + SUITES.index(suite)*MAX_CHUNKS + index


def validate_original(row: dict, suite: str, source_sha: str,
                      binary_sha: str, seed: int) -> None:
    """Treat the existing production fault oracle as immutable authority."""
    data = dict(row)
    digest = data.pop("receipt_sha256", None)
    if not isinstance(digest, str) or not SHA256.fullmatch(digest) or original.json_hash(data) != digest:
        raise ValueError("original fault producer emitted an altered receipt")
    expected = {
        "schema": original.SCHEMA, "source_sha": source_sha,
        "binary_sha256": binary_sha, "suite": suite, "seed": seed,
        "requested_iterations": CHUNK_SIZE, "attempted_iterations": CHUNK_SIZE,
        "passed_iterations": CHUNK_SIZE, "failed_iterations": 0,
        "disposition": "completed_positive", "release_gate_credit": 0,
        "physical_hardware_covered": False, "actual_guest_gameplay_covered": False,
        "retained_failure_root_count": 0,
    }
    if any(type(data.get(k)) is not type(v) or data.get(k) != v for k, v in expected.items()):
        raise ValueError("original production fault oracle rejected/incomplete trial population")
    if data.get("failures") != []:
        raise ValueError("original fault oracle has unexpected failure witnesses")
    if not isinstance(data.get("elapsed_ms"), int) or data["elapsed_ms"] < 0:
        raise ValueError("original producer has no real elapsed-time measurement")


def timing_histogram(seed: int) -> list[int]:
    """Exactly mirror established randint(0,8) millisecond fault jitter."""
    import random
    rng = random.Random(seed)
    out = [0] * 9
    for _ in range(CHUNK_SIZE):
        out[rng.randint(0, 8)] += 1
    return out


def run_shard(*, exe: Path, source_sha: str, binary_sha: str,
              suite: str, minutes: int, seed: int, work: Path,
              result_path: Path, max_chunks: int = MAX_CHUNKS) -> dict:
    if (not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha)
            or suite not in SUITES or minutes not in MINUTES
            or type(seed) is not int or seed < 0 or seed > 100000000
            or type(max_chunks) is not int or not 1 <= max_chunks <= MAX_CHUNKS):
        raise ValueError("invalid bounded suite/source/endurance budget")
    if not exe.is_file() or exe.is_symlink() or original.digest(exe) != binary_sha:
        raise ValueError("missing or mismatched original compiled production-store fixture")
    if work.exists():
        raise ValueError("refuse reused private real-process fault roots")
    work.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + minutes * 60
    rows: list[dict] = []
    failures: list[dict] = []
    histogram = [0] * 9

    def snapshot(disposition: str, stop_reason: str) -> dict:
        summary = {
            "schema": SCHEMA, "source_sha": source_sha, "binary_sha256": binary_sha,
            "suite": suite, "base_seed": seed, "minutes_budget": minutes,
            "max_chunks": max_chunks, "chunk_size": CHUNK_SIZE,
            "chunks": list(rows), "observed_complete_chunks": len(rows),
            "real_process_fault_journeys": len(rows) * CHUNK_SIZE,
            "failed_chunks": list(failures), "timing_jitter_ms_histogram": list(histogram),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stop_reason": stop_reason, "disposition": disposition,
            "release_gate_credit": 0,
            "actual_guest_gameplay_covered": False,
            "physical_hardware_covered": False,
            "power_loss_equivalence_claimed": False,
            "scope": "Real production fault/death/store fixture; no guest-run original/native event, hardware, power-cut device or Windows release",
        }
        summary["receipt_sha256"] = digest_object(summary)
        return summary

    for index in range(max_chunks):
        if index > 0 and time.monotonic() >= deadline:
            break
        actual_seed = case_seed(seed, suite, index)
        trial_dir = work / f"batch-{index:05d}"
        try:
            proof = original.run_suite(
                exe=exe, source_sha=source_sha, binary_sha256=binary_sha,
                suite=suite, iterations=CHUNK_SIZE, seed=actual_seed,
                work=trial_dir)
            validate_original(proof, suite, source_sha, binary_sha, actual_seed)
            per_seed_hist = timing_histogram(actual_seed)
            for n, count in enumerate(per_seed_hist):
                histogram[n] += count
            rows.append({
                "index": index, "seed": actual_seed,
                "source_receipt_sha256": proof["receipt_sha256"],
                "real_fault_journeys": CHUNK_SIZE, "elapsed_ms": proof["elapsed_ms"],
                "jitter_ms_histogram": per_seed_hist,
            })
            # No persisted ROM, personal storage or ephemeral fault roots.
            shutil.rmtree(trial_dir)
        except Exception as exc:
            failures.append({"index": index, "seed": actual_seed,
                             "kind": type(exc).__name__, "detail": str(exc)[-600:]})
            save(result_path, snapshot("invariant_violation", "producer_failure"))
            return snapshot("invariant_violation", "producer_failure")
        if index % 25 == 0:
            # Preserves partial progress evidence if runner hard-times-out:
            # the final cross-shard aggregate always refuses in_progress.
            save(result_path, snapshot("in_progress", "active_work"))
    reason = "case_cap" if len(rows) == max_chunks else "wall_budget"
    report = snapshot("completed_positive", reason)
    save(result_path, report)
    return report


def aggregate(results: Path, source_sha: str, binary_sha: str,
              minutes: int, seed: int, max_chunks: int = MAX_CHUNKS) -> dict:
    if (not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha)
            or minutes not in MINUTES or type(seed) is not int
            or seed < 0 or seed > 100000000
            or not 1 <= max_chunks <= MAX_CHUNKS):
        raise ValueError("invalid aggregate provenance or bounded budget")
    rows, issues = [], []
    for suite in SUITES:
        path = results / ("fault-endurance-" + suite) / "result.json"
        if not path.is_file():
            issues.append(f"{suite}: missing source-linked receipt")
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            hash_claim = row.pop("receipt_sha256")
            if not isinstance(hash_claim, str) or not SHA256.fullmatch(hash_claim) or hash_claim != digest_object(row):
                raise ValueError("tampered fault receipt")
            expected = {
                "schema": SCHEMA, "source_sha": source_sha,
                "binary_sha256": binary_sha, "suite": suite, "base_seed": seed,
                "minutes_budget": minutes, "max_chunks": max_chunks,
                "chunk_size": CHUNK_SIZE, "release_gate_credit": 0,
                "actual_guest_gameplay_covered": False,
                "physical_hardware_covered": False,
                "power_loss_equivalence_claimed": False,
                "disposition": "completed_positive",
            }
            if any(type(row.get(k)) is not type(v) or row.get(k) != v for k, v in expected.items()):
                raise ValueError("source, candidate, budget or release-credit identity mismatch")
            chunks = row["chunks"]
            if (type(chunks) is not list or not 1 <= len(chunks) <= max_chunks
                    or row["observed_complete_chunks"] != len(chunks)
                    or row["real_process_fault_journeys"] != len(chunks)*CHUNK_SIZE
                    or row["failed_chunks"] != []
                    or row["stop_reason"] not in ("wall_budget", "case_cap")
                    or not isinstance(row["elapsed_seconds"], (int, float))
                    or row["elapsed_seconds"] < 0):
                raise ValueError("incomplete or incorrectly counted process trials")
            observed_hist = [0]*9
            for index, chunk in enumerate(chunks):
                want_hist = timing_histogram(case_seed(seed, suite, index))
                expected_chunk = {
                    "index": index, "seed": case_seed(seed, suite, index),
                    "real_fault_journeys": CHUNK_SIZE, "jitter_ms_histogram": want_hist,
                }
                if (type(chunk) is not dict or
                        any(type(chunk.get(k)) is not type(v) or chunk.get(k) != v
                            for k,v in expected_chunk.items()) or
                        not SHA256.fullmatch(chunk.get("source_receipt_sha256","")) or
                        type(chunk.get("elapsed_ms")) is not int or
                        chunk["elapsed_ms"] < 0):
                    raise ValueError(f"non-original, repeated or altered fault batch {index}")
                for n, count in enumerate(want_hist):
                    observed_hist[n] += count
            if row["timing_jitter_ms_histogram"] != observed_hist:
                raise ValueError("missing timing-jitter population")
            row["receipt_sha256"] = hash_claim
            rows.append(row)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{suite}: invalid original fault evidence ({exc})")
    if results.is_dir():
        allowed = {"fault-endurance-" + name for name in SUITES}
        unexpected = [p.name for p in results.iterdir() if p.name not in allowed]
        if unexpected:
            issues.append("unexpected fault cohort artifacts: " + str(sorted(unexpected)[:6]))
    return {
        "schema": SCHEMA, "source_sha": source_sha, "binary_sha256": binary_sha,
        "minutes_budget_per_shard": minutes,
        "requested_suites": len(SUITES), "observed_suites": len(rows),
        "completed_unique_timing_batches": sum(x["observed_complete_chunks"] for x in rows),
        "completed_real_fault_process_journeys": sum(x["real_process_fault_journeys"] for x in rows),
        "elapsed_seconds_per_suite": {x["suite"]: x["elapsed_seconds"] for x in rows},
        "issues": issues, "disposition": "completed_positive" if not issues else "incomplete_or_failed",
        "release_gate_credit": 0, "actual_guest_gameplay_covered": False,
        "physical_hardware_covered": False, "power_loss_equivalence_claimed": False,
        "suites": rows,
    }


def summary(report: dict) -> str:
    lines = [
        "## QA-02 real-process fault endurance", "",
        f"**{report['disposition']}** | {report['completed_real_fault_process_journeys']} "
        f"genuine fault journeys | {report['completed_unique_timing_batches']} seeded timing batches",
        "", "| Production fault suite | Completed real-process journeys | Actual wall seconds |",
        "| --- | ---: | ---: |",
    ]
    for row in report["suites"]:
        lines.append(f"| {row['suite']} | {row['real_process_fault_journeys']} | {row['elapsed_seconds']} |")
    lines += [
        "", "Not guest-played match evidence, a physical/power-loss test, or release gate credit.", ""
    ]
    lines += ["- " + str(issue) for issue in report["issues"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    for name in ("exe","work","out"):
        run.add_argument("--"+name, type=Path, required=True)
    for name in ("source-sha","binary-sha","suite"):
        run.add_argument("--"+name, required=True)
    for name in ("minutes","seed","max-chunks"):
        run.add_argument("--"+name, type=int, required=True)
    agg = sub.add_parser("aggregate")
    for name in ("results","out","summary"):
        agg.add_argument("--"+name, type=Path, required=True)
    for name in ("source-sha","binary-sha"):
        agg.add_argument("--"+name, required=True)
    for name in ("minutes","seed","max-chunks"):
        agg.add_argument("--"+name, type=int, required=True)
    args = p.parse_args()
    if args.mode == "run":
        row = run_shard(
            exe=args.exe, source_sha=args.source_sha, binary_sha=args.binary_sha,
            suite=args.suite, minutes=args.minutes, seed=args.seed,
            work=args.work, result_path=args.out, max_chunks=args.max_chunks)
        print(f"{row['suite']}: {row['disposition']} {row['real_process_fault_journeys']} "
              f"real-process journeys; elapsed={row['elapsed_seconds']}s")
        return 0 if row["disposition"] == "completed_positive" else 1
    report = aggregate(args.results, args.source_sha, args.binary_sha,
                       args.minutes, args.seed, args.max_chunks)
    save(args.out, report)
    args.summary.write_text(summary(report), encoding="utf-8")
    return 0 if report["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
