#!/usr/bin/env python3
"""Unattended owner-HP two-player source-bound gameplay exploration.

Reuses QA-02's actual four-execution treatment/replay/P1/P2 oracle and its
stock retail input fixtures. No model, network, global machine setting,
release/physical-pad credit, or copied ROM/game binary in its evidence.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

from tools import qa02_native_2p_seeded_endurance as native

SCHEMA = "ur-hp-windows-seeded-2p-research/1"
WORKERS = 4
WALL_SECONDS = 360
MINUTES = 15
MAX_CASES = 12
PROCESS_TIMEOUT = 90
SHA1 = re.compile(r"[a-f0-9]{40}\Z")


def authorize(env: dict[str, str]) -> tuple[int, str]:
    """Separate this private scheduled research from untrusted PR execution."""
    if (env.get("GITHUB_REPOSITORY") != "gamesbyian/UR-Recomp"
            or env.get("GITHUB_REF") != "refs/heads/main"
            or env.get("RUNNER_NAME") != "hpmini-ur-recomp"
            or env.get("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}):
        raise ValueError("untrusted or nonowner HP research event")
    sha = env.get("GITHUB_SHA", "")
    if not SHA1.fullmatch(sha):
        raise ValueError("unbound source revision")
    run_id = env.get("GITHUB_RUN_ID", "")
    attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    if (not re.fullmatch(r"[1-9][0-9]{0,17}", run_id)
            or not re.fullmatch(r"[1-9][0-9]{0,3}", attempt)):
        raise ValueError("invalid workflow run identity")
    return int(run_id), sha


def collect(rows: list[dict], source: str, run_id: int, elapsed: float) -> dict:
    if len(rows) != WORKERS:
        raise ValueError("missing worker result")
    identity = None
    seeds: set[int] = set()
    inputs: set[str] = set()
    issues: list[dict[str, str | int]] = []
    attempts = successes = native_processes = 0
    summaries = []
    for index, row in enumerate(rows):
        if row.get("worker") != index:
            raise ValueError("wrong worker order or index")
        report = row.get("report")
        if not isinstance(report, dict):
            issues.append({"worker": index, "reason": str(row.get("error", "no report"))[:240]})
            continue
        sealed = dict(report)
        sig = sealed.pop("receipt_sha256", None)
        if not isinstance(sig, str) or native.hash_object(sealed) != sig:
            issues.append({"worker": index, "reason": "invalid source-owned research receipt"})
            continue
        if (sealed.get("schema") != native.SCHEMA
                or sealed.get("disposition") != "completed_positive"
                or sealed.get("release_gate_credit") != 0
                or sealed.get("source_commit") is not None
                or sealed.get("failed_cases") != 0
                or sealed.get("shard") != index % 2
                or sealed.get("minutes_budget") != MINUTES
                or sealed.get("wall_seconds_budget") != WALL_SECONDS
                or sealed.get("max_unique_cases") != MAX_CASES
                or sealed.get("attempted_cases") != sealed.get("passed_cases")
                or sealed.get("total_real_native_processes") != 4 * sealed.get("passed_cases", -1)):
            issues.append({"worker": index, "reason": "incomplete or nonpositive source-owned result"})
            continue
        proof = sealed.get("identity")
        if not isinstance(proof, dict) or proof.get("source_commit") != source:
            issues.append({"worker": index, "reason": "source mismatch"})
            continue
        if identity is None:
            identity = proof
        elif proof != identity:
            issues.append({"worker": index, "reason": "executable, ROM or source fixture mismatch"})
            continue
        cases = sealed.get("case_results")
        if not isinstance(cases, list) or len(cases) != sealed["passed_cases"]:
            issues.append({"worker": index, "reason": "missing cases"})
            continue
        for case in cases:
            seed, digest = case.get("seed"), case.get("input_sha256")
            if (not isinstance(seed, int) or not isinstance(digest, str)
                    or seed in seeds or digest in inputs
                    or case.get("real_native_processes") != 4
                    or case.get("two_seats_observably_active") is not True
                    or case.get("bit_exact_replay") is not True):
                issues.append({"worker": index, "reason": "repeated/unverified controller case"})
                break
            seeds.add(seed)
            inputs.add(digest)
        else:
            attempts += sealed["attempted_cases"]
            successes += sealed["passed_cases"]
            native_processes += sealed["total_real_native_processes"]
            summaries.append({"worker": index, "shard": index % 2,
                              "case_count": len(cases), "seed_first": cases[0]["seed"]
                              if cases else None, "elapsed_seconds": sealed.get("elapsed_seconds")})
    valid = not issues and identity is not None and attempts == successes and successes >= WORKERS
    result = {
        "schema": SCHEMA, "source_sha": source, "run_id": run_id,
        "status": "completed_positive" if valid else "research_failure",
        "workers": WORKERS, "elapsed_seconds": round(elapsed, 3),
        "attempted_cases": attempts, "accepted_cases": successes,
        "real_guest_processes": native_processes,
        "candidate_identity": identity,
        "per_worker": summaries, "issues": issues[:16],
        "original_native_event_credit": 0, "release_gate_credit": 0,
        "physical_gamepads_tested": False,
    }
    result["receipt_sha256"] = native.hash_object(result)
    return result


def run(exe: Path, rom: Path, env: dict[str, str], receipt: Path) -> dict:
    run_id, sha = authorize(env)
    if not exe.is_file() or not rom.is_file() or exe.is_symlink() or rom.is_symlink():
        raise ValueError("missing/redirected exact game executable or stock ROM")
    private = Path(env["RUNNER_TEMP"]) / f"hp-seeded-2p-{run_id}-{env['GITHUB_RUN_ATTEMPT']}"
    if private.exists():
        raise ValueError("research work root already exists; refusing stale evidence")
    private.mkdir(parents=True)
    # Every Actions run gets four distinct integer seed namespaces.
    base = run_id % 10_000_000
    seeds = (base, base, base + 25_000_000, base + 25_000_000)
    start = time.monotonic()

    def worker(i: int) -> dict:
        try:
            row = native.run_shard(
                exe=exe, rom=rom, source_sha=sha, shard=i % 2,
                base_seed=seeds[i], minutes=MINUTES, max_cases=MAX_CASES,
                timeout=PROCESS_TIMEOUT, wall_seconds=WALL_SECONDS,
                work=private / f"worker-{i}")
            return {"worker": i, "report": row}
        except Exception as exc:
            # Keep the exact failure class in the negative receipt. A single
            # malformed test input or unexpected guest error must not erase
            # other concurrently completed independent workers' evidence.
            return {"worker": i, "error": f"{type(exc).__name__}: {exc}"[:240]}

    rows = [None] * WORKERS
    # Threads only coordinate; independent real Windows game processes own
    # separate per-worker controllers, dumps, user-data and directories.
    # This context always joins all workers, including on an early failure.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(worker, i): i for i in range(WORKERS)}
        for future in as_completed(futures):
            index = futures[future]
            rows[index] = future.result()
    result = collect(rows, sha, run_id, time.monotonic() - start)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.exe, args.rom, dict(os.environ), args.receipt)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"HP_SEEDED_2P_RESEARCH=refused reason={type(exc).__name__} {exc}", file=sys.stderr)
        return 1
    print("HP_SEEDED_2P_RESEARCH=" + result["status"] +
          f" seeds={result['accepted_cases']} windows_processes={result['real_guest_processes']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("\n## Owner HP unattended two-player research\n\n")
            stream.write("Source: `" + result["source_sha"] + "`. "
                         "Disposition: **" + result["status"] + "**. "
                         f"{result['accepted_cases']} distinct seeded plans, "
                         f"{result['real_guest_processes']} actual Windows game processes.\n\n")
            stream.write("Pure native determinism/seat-ablation evidence only. "
                         "No original/native or release gate credit.\n")
    return 0 if result["status"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
