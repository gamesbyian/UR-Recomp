#!/usr/bin/env python3
"""Unattended owner-HP two-player source-bound gameplay exploration.

Reuses QA-02's actual four-execution treatment/replay/P1/P2 oracle and its
stock retail input fixtures. No model, network, global machine setting,
release/physical-pad credit, or copied ROM/game binary in its evidence.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from tools import qa02_native_2p_seeded_endurance as native

SCHEMA = "ur-hp-windows-seeded-2p-research/1"
WORKERS = 8  # Research-only trial; each worker owns four guest processes per case.
WALL_SECONDS = 360  # Scheduled/default manual horizon is unchanged.
MANUAL_WALL_SECONDS = 600  # Deliberate workflow_dispatch trial only.
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


def research_wall_seconds(env: dict[str, str]) -> int:
    """Allow the longer horizon only on a trusted manual HP research event."""
    raw = env.get("UR_HP_RESEARCH_WALL_SECONDS", str(WALL_SECONDS))
    if raw not in {str(WALL_SECONDS), str(MANUAL_WALL_SECONDS)}:
        raise ValueError("unsupported HP research wall horizon")
    if raw != str(WALL_SECONDS) and env.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise ValueError("extended research horizon requires a manual dispatch")
    return int(raw)


def authentic_candidate(proof: object, source: str) -> bool:
    """Check original ROM, source, stock script/input and exact PE hash identity."""
    keys = {"source_commit", "native_executable_sha256", "rom_sha256",
            "stock_input_sha256", "stock_script_sha256"}
    if not isinstance(proof, dict) or set(proof) != keys:
        return False
    if proof["source_commit"] != source or proof["rom_sha256"] != native.ROM_SHA:
        return False
    if any(not isinstance(proof[k], str) or not native.SHA256.fullmatch(proof[k])
           for k in keys - {"source_commit"}):
        return False
    stock_input, stock_script = native.base_source()
    return (proof["stock_input_sha256"] ==
            hashlib.sha256(stock_input.encode()).hexdigest()
            and proof["stock_script_sha256"] ==
            hashlib.sha256(stock_script.encode()).hexdigest())


def safe_failure_category(kind: str, detail: object) -> str:
    """Allowlisted native failure class; never publish private process logs."""
    if kind == "RuntimeError" and isinstance(detail, str):
        if re.fullmatch(r"real guest process timeout \([1-9][0-9]{0,2}s\)", detail):
            return "guest_timeout"
        exit_code = re.match(r"guest exited (-?[0-9]{1,10});", detail)
        if exit_code and int(exit_code.group(1)) != 0:
            return "guest_nonzero_exit"
    return "unclassified"


def source_owned_failure_notes(sealed: dict, source: str, worker: int,
                               run_id: int, wall_seconds: int = WALL_SECONDS) -> list[dict]:
    """Only authentic, bounded attempt records earn replay coordinates."""
    proof, failures = sealed.get("identity"), sealed.get("failures")
    shard = worker % 2
    expected_base = run_id % 10000000 + (worker // 2) * 25000000
    attempted, passed = sealed.get("attempted_cases"), sealed.get("passed_cases")
    if (sealed.get("schema") != native.SCHEMA
            or sealed.get("disposition") != "invariant_violation"
            or sealed.get("release_gate_credit") != 0
            or sealed.get("source_commit") is not None
            or not authentic_candidate(proof, source)
            or sealed.get("shard") != shard
            or sealed.get("base_seed") != expected_base
            or sealed.get("minutes_budget") != MINUTES
            or sealed.get("wall_seconds_budget") != wall_seconds
            or sealed.get("max_unique_cases") != MAX_CASES
            or sealed.get("stop_reason") != "invariant_failure"
            or not isinstance(failures, list) or not 1 <= len(failures) <= 2
            or sealed.get("failed_cases") != len(failures)
            or type(attempted) is not int or not 1 <= attempted <= MAX_CASES
            or type(passed) is not int or passed < 0
            or attempted != passed + len(failures)
            or sealed.get("total_real_native_processes") != 4 * passed):
        return []
    cases = sealed.get("case_results")
    if not isinstance(cases, list) or len(cases) != passed:
        return []
    origin = expected_base + shard * 1000003
    # A negative replay seed is credible only if preceding successful trials
    # used the actual source-owned treatment and route-script bytes.
    stock_input = script_digest = None
    if cases:
        stock_input, stock_script = native.base_source()
        script_digest = expected_script_digest(stock_script)
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            return []
        seed, digest = case.get("seed"), case.get("input_sha256")
        if (type(seed) is not int or not 0 <= seed - origin < attempted
                or not isinstance(digest, str) or not native.SHA256.fullmatch(digest)
                or digest != expected_treatment_digest(stock_input, seed)
                or case.get("script_sha256") != script_digest
                or case.get("real_native_processes") != 4
                or case.get("two_seats_observably_active") is not True
                or case.get("bit_exact_replay") is not True
                or seed - origin in seen):
            return []
        seen.add(seed - origin)
    notes = []
    for failure in failures:
        if not isinstance(failure, dict):
            return []
        seed, trial_index, kind = (failure.get("seed"),
                                   failure.get("trial_index"), failure.get("kind"))
        if (type(seed) is not int or type(trial_index) is not int
                or not 0 <= trial_index < attempted
                or seed != origin + trial_index or trial_index in seen
                or not isinstance(kind, str)
                or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", kind)):
            return []
        # New producer emits a typed category before truncating noisy guest
        # output. Historical sealed receipts still use the legacy parser.
        category = failure.get("failure_category")
        if kind == "GuestProcessError":
            if category not in {"guest_timeout", "guest_nonzero_exit"}:
                return []
            legacy = safe_failure_category("RuntimeError", failure.get("error"))
            if legacy != "unclassified" and legacy != category:
                return []
        else:
            if category not in (None, "unclassified"):
                return []
            category = safe_failure_category(kind, failure.get("error"))
        seen.add(trial_index)
        notes.append({"worker": worker, "reason": "source-owned trial invariant failure",
                      "seed": seed, "trial_index": trial_index, "kind": kind,
                      "failure_category": category})
    return notes if seen == set(range(attempted)) else []

def expected_treatment_digest(stock_input: str, seed: int) -> str:
    """Reproduce the producer's text-mode treatment file bytes on this host.

    Path.write_text uses host newline translation: CRLF on the owner HP,
    LF in Linux ROM-free tests.
    """
    rendered = native.render_input(stock_input, native.input_plan(seed)[0], None)
    return hashlib.sha256(rendered.replace("\n", os.linesep).encode("utf-8")).hexdigest()


def expected_script_digest(stock_script: str) -> str:
    """Hash the exact generated route-script bytes written by the producer."""
    rendered = native.render_script(stock_script)
    return hashlib.sha256(rendered.replace("\n", os.linesep).encode("utf-8")).hexdigest()


def collect(rows: list[dict], source: str, run_id: int, elapsed: float,
            *, wall_seconds: int = WALL_SECONDS) -> dict:
    if len(rows) != WORKERS:
        raise ValueError("missing worker result")
    identity = None
    seeds: set[int] = set()
    inputs: set[str] = set()
    issues: list[dict[str, str | int]] = []
    attempts = successes = native_processes = 0
    summaries = []
    pending_failures = []
    source_attested_partial_cases = 0
    source_attested_partial_native_processes = 0
    candidate_proofs = []
    stock_input = None
    script_digest = None
    for index, row in enumerate(rows):
        if row.get("worker") != index:
            raise ValueError("wrong worker order or index")
        report = row.get("report")
        if not isinstance(report, dict):
            kind = row.get("error_type")
            kind = kind if isinstance(kind, str) and re.fullmatch(
                r"[A-Za-z][A-Za-z0-9_]{0,63}", kind) else "Unknown"
            note = {"worker": index, "reason": "worker exception", "kind": kind}
            seed = row.get("base_seed")
            if type(seed) is int and 0 <= seed <= 100000000:
                note["base_seed"] = seed
            issues.append(note)
            continue
        sealed = dict(report)
        sig = sealed.pop("receipt_sha256", None)
        if not isinstance(sig, str) or native.hash_object(sealed) != sig:
            issues.append({"worker": index, "reason": "invalid source-owned research receipt"})
            continue
        if sealed.get("disposition") == "invariant_violation":
            notes = source_owned_failure_notes(sealed, source, index, run_id, wall_seconds)
            if notes:
                pending_failures.append((index, notes, sealed))
                candidate_proofs.append(sealed["identity"])
            else:
                issues.append({"worker": index, "reason": "unverifiable source-owned failure"})
            continue
        expected_base = run_id % 10000000 + (index // 2) * 25000000
        if (sealed.get("schema") != native.SCHEMA
                or sealed.get("disposition") != "completed_positive"
                or sealed.get("release_gate_credit") != 0
                or sealed.get("source_commit") is not None
                or sealed.get("failed_cases") != 0
                or sealed.get("shard") != index % 2
                or sealed.get("base_seed") != expected_base
                or type(sealed.get("attempted_cases")) is not int
                or not 1 <= sealed["attempted_cases"] <= MAX_CASES
                or sealed.get("stop_reason") != (
                    "case_cap" if sealed["attempted_cases"] == MAX_CASES else "wall_budget")
                or type(sealed.get("passed_cases")) is not int
                or sealed.get("failures") != []
                or any(sealed.get(k) is not False for k in (
                    "original_native_fidelity_accepted",
                    "complete_two_player_result_accepted",
                    "physical_gamepads_tested"))
                or type(sealed.get("elapsed_seconds")) is not float
                or not math.isfinite(sealed["elapsed_seconds"])
                or sealed["elapsed_seconds"] < 0
                or sealed.get("minutes_budget") != MINUTES
                or sealed.get("wall_seconds_budget") != wall_seconds
                or sealed.get("max_unique_cases") != MAX_CASES
                or sealed.get("attempted_cases") != sealed.get("passed_cases")
                or sealed.get("total_real_native_processes") != 4 * sealed.get("passed_cases", -1)):
            issues.append({"worker": index, "reason": "incomplete or nonpositive source-owned result"})
            continue
        proof = sealed.get("identity")
        if not authentic_candidate(proof, source):
            issues.append({"worker": index, "reason": "source or stock fixture mismatch"})
            continue
        candidate_proofs.append(proof)
        if stock_input is None:
            stock_input, stock_script = native.base_source()
            script_digest = expected_script_digest(stock_script)
        if identity is None:
            identity = proof
        elif proof != identity:
            issues.append({"worker": index, "reason": "executable, ROM or source fixture mismatch"})
            continue
        cases = sealed.get("case_results")
        if not isinstance(cases, list) or len(cases) != sealed["passed_cases"]:
            issues.append({"worker": index, "reason": "missing cases"})
            continue
        for trial_index, case in enumerate(cases):
            if not isinstance(case, dict):
                issues.append({"worker": index, "reason": "malformed controller case"})
                break
            seed, digest = case.get("seed"), case.get("input_sha256")
            expected_seed = expected_base + (index % 2) * 1000003 + trial_index
            if (type(seed) is not int or seed != expected_seed
                    or not isinstance(digest, str) or not native.SHA256.fullmatch(digest)
                    or digest != expected_treatment_digest(stock_input, seed)
                    or case.get("script_sha256") != script_digest
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
    if pending_failures:
        # A single checksum-vouched foreign PE cannot borrow the source
        # credentials of another worker. ALL source-owned producers must agree
        # before even one negative seed is published for replay.
        consistent = (not issues and len(candidate_proofs) == WORKERS
                      and all(proof == candidate_proofs[0]
                              for proof in candidate_proofs))
        if consistent:
            identity = candidate_proofs[0]
            # Keep source-sealed pre-failure research visible without turning
            # a failed multi-worker campaign into accepted cases or QA credit.
            source_attested_partial_cases = sum(
                sealed["passed_cases"] for _, _, sealed in pending_failures)
            source_attested_partial_native_processes = sum(
                sealed["total_real_native_processes"]
                for _, _, sealed in pending_failures)
        for index, notes, _ in pending_failures:
            issues.extend(notes if consistent else
                          [{"worker": index, "reason": "unverifiable source-owned failure"}])
    valid = not issues and identity is not None and attempts == successes and successes >= WORKERS
    result = {
        "schema": SCHEMA, "source_sha": source, "run_id": run_id,
        "status": "completed_positive" if valid else "research_failure",
        "workers": WORKERS, "wall_seconds_budget": wall_seconds,
        "elapsed_seconds": round(elapsed, 3),
        "attempted_cases": attempts, "accepted_cases": successes,
        "real_guest_processes": native_processes,
        "source_attested_pre_failure_cases": source_attested_partial_cases,
        "source_attested_pre_failure_native_processes": source_attested_partial_native_processes,
        "candidate_identity": identity,
        "per_worker": summaries, "issues": issues[:16],
        "original_native_event_credit": 0, "release_gate_credit": 0,
        "physical_gamepads_tested": False,
    }
    result["receipt_sha256"] = native.hash_object(result)
    return result


def run(exe: Path, rom: Path, env: dict[str, str], receipt: Path) -> dict:
    run_id, sha = authorize(env)
    wall_seconds = research_wall_seconds(env)
    if not exe.is_file() or not rom.is_file() or exe.is_symlink() or rom.is_symlink():
        raise ValueError("missing/redirected exact game executable or stock ROM")
    private = Path(env["RUNNER_TEMP"]) / f"hp-seeded-2p-{run_id}-{env['GITHUB_RUN_ATTEMPT']}"
    if private.exists():
        raise ValueError("research work root already exists; refusing stale evidence")
    private.mkdir(parents=True)
    # Every Actions run gets independent seed namespaces per paired shard.
    # Pair i owns one base namespace; shard 0/1 offset by 1,000,003.
    # With eight workers, the largest base remains <85M (source-owned bound 100M).
    base = run_id % 10_000_000
    seeds = tuple(base + (i // 2) * 25_000_000 for i in range(WORKERS))
    start = time.monotonic()

    def worker(i: int) -> dict:
        try:
            row = native.run_shard(
                exe=exe, rom=rom, source_sha=sha, shard=i % 2,
                base_seed=seeds[i], minutes=MINUTES, max_cases=MAX_CASES,
                timeout=PROCESS_TIMEOUT, wall_seconds=wall_seconds,
                work=private / f"worker-{i}")
            return {"worker": i, "report": row}
        except Exception as exc:
            # Keep the exact failure class in the negative receipt. A single
            # malformed test input or unexpected guest error must not erase
            # other concurrently completed independent workers' evidence.
            return {"worker": i, "error_type": type(exc).__name__,
                    "base_seed": seeds[i]}

    rows = [None] * WORKERS
    # Threads only coordinate; independent real Windows game processes own
    # separate per-worker controllers, dumps, user-data and directories.
    # This context always joins all workers, including on an early failure.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(worker, i): i for i in range(WORKERS)}
        for future in as_completed(futures):
            index = futures[future]
            rows[index] = future.result()
    result = collect(rows, sha, run_id, time.monotonic() - start,
                     wall_seconds=wall_seconds)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result



# Only print labels derived from accepted collector states. Research producers
# may include private guest stdout/stderr or local Windows paths in errors.
SUMMARY_ISSUE_LABELS = {
    "worker exception": "worker exception",
    "invalid source-owned research receipt": "invalid source-owned receipt",
    "unverifiable source-owned failure": "unverifiable source-owned failure",
    "incomplete or nonpositive source-owned result": "incomplete/nonpositive worker result",
    "source or stock fixture mismatch": "source/stock fixture mismatch",
    "executable, ROM or source fixture mismatch": "cross-worker identity mismatch",
    "missing cases": "missing case records",
    "malformed controller case": "malformed controller case",
    "repeated/unverified controller case": "duplicate/unverified controller case",
    "source-owned trial invariant failure": "source-owned trial invariant failure",
}
SUMMARY_FAILURE_CATEGORIES = frozenset(
    ("guest_timeout", "guest_nonzero_exit", "unclassified"))


def result_summary(result: dict) -> str:
    """Bounded, privacy-safe Actions summary; signed receipt stays authoritative."""
    positive = result["status"] == "completed_positive"
    workers = result["workers"]
    elapsed = result["elapsed_seconds"]
    lines = [
        "## Owner HP unattended two-player research",
        "",
        f"Source: `{result['source_sha']}`. Run: `{result['run_id']}`.",
        f"Research cohort wall horizon: **{result.get('wall_seconds_budget', WALL_SECONDS)}s**. "
        f"Disposition: **{result['status']}**. {workers} independent worker cohorts; "
        f"research wall time **{elapsed:.1f}s** (excludes build and QA).",
        "",
    ]
    if positive:
        cases = result["accepted_cases"]
        processes = result["real_guest_processes"]
        lines.append(
            f"**Accepted:** {cases} distinct source-bound seeded plans, "
            f"{processes} real Windows guest processes (four per plan).")
        if elapsed > 0:
            lines.append(
                f"Research-only throughput: **{60 * cases / elapsed:.2f} "
                f"accepted cases/min**, **{60 * processes / elapsed:.2f} "
                "guest processes/min**. No historical speedup inferred.")
        cohort = ([entry["case_count"] for entry in result["per_worker"]]
                  if len(result["per_worker"]) == workers else [])
        if cohort:
            lines.append(
                f"Per-worker accepted case range: **{min(cohort)}–{max(cohort)}**.")
    else:
        lines.append(
            "**No campaign accepted.** A source-attested pre-failure case "
            "cannot be counted as a completed positive campaign.")
        partial = result.get("source_attested_pre_failure_cases", 0)
        if partial:
            lines.append(
                f"Source-attested pre-failure cases: {partial} "
                "(diagnostic only; zero acceptance credit).")
        issues = result.get("issues", [])
        lines.append(
            f"First {len(issues)} classified receipt issue(s) "
            "(receipt is capped at 16; inspect artifact for full context):")
        if not issues:
            lines.append("- No classified worker issue in receipt.")
        for issue in issues[:8]:
            worker = issue.get("worker")
            worker_label = (f"worker {worker}" if type(worker) is int
                            and 0 <= worker < workers else "worker unknown")
            reason = SUMMARY_ISSUE_LABELS.get(
                issue.get("reason"), "unclassified collector issue")
            detail = ""
            if issue.get("reason") == "source-owned trial invariant failure":
                category = issue.get("failure_category")
                if category not in SUMMARY_FAILURE_CATEGORIES:
                    category = "unclassified"
                detail = f"; class={category}"
                seed = issue.get("seed")
                if type(seed) is int and 0 <= seed < 100_000_000:
                    detail += f"; replay seed={seed}"
            lines.append(f"- {worker_label}: {reason}{detail}")
        if len(issues) > 8:
            lines.append(f"- {len(issues) - 8} additional issue(s) in receipt.")
    lines += [
        "",
        "Result is native deterministic replay/seat-ablation research only. "
        "**Zero original/native event, physical-gamepad or release-gate credit.**",
        "",
    ]
    return "\n".join(lines)


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
          f" workers={result['workers']} elapsed_s={result['elapsed_seconds']}"
          f" seeds={result['accepted_cases']} windows_processes={result['real_guest_processes']}"
          f" issue_count={len(result['issues'])}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("\n" + result_summary(result))
    return 0 if result["status"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
