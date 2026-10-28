#!/usr/bin/env python3
"""Bounded, fail-closed reducer for paired original/native SNES input fixtures.

The external oracle must execute both genuine engines. This tool cannot grant QA.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from controller_input import load_controller_runs

SCHEMA = "ur-controller-reducer-oracle/1"
FIELDS = ("source_sha", "original_rom_sha256", "native_binary_sha256",
          "reference_engine", "discrepancy_id", "semantic_phase")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(runs):
    lines = []
    for r in sorted(runs, key=lambda x: (x.start, x.end, x.p1_mask, x.p2_mask)):
        line = f"{r.start}:{r.duration}:{r.p1_mask:03X}"
        if r.p2_mask:
            line += f":{r.p2_mask:03X}"
        lines.append(line)
    return ("\n".join(lines) + ("\n" if lines else "")).encode("ascii")


def verify_receipt(receipt, candidate_hash):
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise ValueError("wrong or missing oracle schema")
    if receipt.get("candidate_sha256") != candidate_hash:
        raise ValueError("oracle has not attested exact candidate bytes")
    for field, width in (("source_sha", 40), ("original_rom_sha256", 64),
                         ("native_binary_sha256", 64)):
        value = receipt.get(field, "")
        if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{" + str(width) + "}", value):
            raise ValueError("invalid oracle " + field)
    for field in FIELDS[3:]:
        if not isinstance(receipt.get(field), str) or not receipt[field].strip():
            raise ValueError("missing oracle " + field)
    if type(receipt.get("original_valid")) is not bool or type(receipt.get("native_valid")) is not bool:
        raise ValueError("missing two-engine validity assertions")
    if receipt.get("result") not in ("reproduced", "not_reproduced", "invalid_route"):
        raise ValueError("invalid oracle result")
    if "native_executed" in receipt:
        if type(receipt["native_executed"]) is not bool:
            raise ValueError("invalid native execution evidence")
        if not receipt["native_executed"] and (
                receipt["native_valid"] or receipt["result"] != "invalid_route"
                or receipt.get("native_skip_reason") not in
                ("original_stage_invalid", "original_target_changed")):
            raise ValueError("unexecuted native cannot claim paired evidence")
        if receipt["native_executed"] and receipt.get("native_skip_reason") is not None:
            raise ValueError("executed native cannot claim skipped evidence")
    return tuple(receipt[k] for k in FIELDS)


def reduce(runs, source_hash, protected_before_frame, oracle,
           max_calls=60, repeats=2, timeout=120, observation_frame=None):
    if not runs or protected_before_frame < 1 or not oracle:
        raise ValueError("need source runs, protected original prefix and oracle")
    if not (1 <= repeats <= 5 and repeats <= max_calls <= 10000 and 1 <= timeout <= 3600):
        raise ValueError("invalid execution budget")
    if observation_frame is not None and (
            type(observation_frame) is not int
            or not protected_before_frame <= observation_frame < 200000):
        raise ValueError("observation frame must be an authenticated original guest clock")
    protected = [r for r in runs if r.start < protected_before_frame]
    mutable = [r for r in runs if r.start >= protected_before_frame]
    base_identity = None
    calls = tests = native_skips = 0
    negative_short_circuits = saved_negative_repeats = 0
    observed_results = {"reproduced": 0, "not_reproduced": 0, "invalid_route": 0}
    observed_skip_reasons = {"original_stage_invalid": 0, "original_target_changed": 0}
    cache = {}
    with tempfile.TemporaryDirectory(prefix="ur-replay-reduce-") as tmp:
        candidate = Path(tmp) / "candidate.script"
        receipt_path = Path(tmp) / "receipt.json"

        def check(sequence):
            nonlocal base_identity, calls, tests, native_skips
            nonlocal negative_short_circuits, saved_negative_repeats
            raw = encode(sequence)
            hashed = digest(raw)
            if hashed in cache:
                return cache[hashed]
            if calls + repeats > max_calls:
                raise StopIteration
            tests += 1
            valid = True
            for repetition in range(repeats):
                candidate.write_bytes(raw)
                receipt_path.unlink(missing_ok=True)
                try:
                    proc = subprocess.run(
                        [*oracle, "--candidate", str(candidate), "--receipt", str(receipt_path)],
                        capture_output=True, text=True, check=False, timeout=timeout,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("paired oracle timed out") from exc
                calls += 1
                if proc.returncode or not receipt_path.is_file():
                    raise RuntimeError("paired oracle failed: " + proc.stderr[-400:])
                try:
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                except (ValueError, UnicodeError) as exc:
                    raise ValueError("malformed oracle receipt") from exc
                identity = verify_receipt(receipt, hashed)
                # Keep compact decision counts instead of private candidate
                # inputs or guest stdout/stderr. Every count comes from the
                # actual validated per-run paired-oracle receipt.
                observed_results[receipt["result"]] += 1
                if receipt.get("native_executed") is False:
                    native_skips += 1
                    observed_skip_reasons[receipt["native_skip_reason"]] += 1
                if observation_frame is not None:
                    clocks = receipt.get("guest_clocks")
                    if (type(clocks) is not dict
                            or type(clocks.get("reference_observation_frame")) is not int
                            or clocks["reference_observation_frame"] != observation_frame):
                        raise ValueError("oracle original guest observation frame differs from horizon")
                if base_identity is None:
                    base_identity = identity
                elif base_identity != identity:
                    raise ValueError("oracle provenance/semantic identity changed")
                if not (receipt["result"] == "reproduced" and
                        receipt["original_valid"] and receipt["native_valid"]):
                    # A candidate is admissible ONLY when *every* repetition
                    # independently reproduces the source discrepancy. Once
                    # one execution rejects it, later positive repeats cannot
                    # reverse that decision. Stop spending expensive paired
                    # engine runs on an already disproved candidate; strict
                    # positive admission still requires all `repeats` runs.
                    valid = False
                    remaining = repeats - repetition - 1
                    if remaining:
                        negative_short_circuits += 1
                        saved_negative_repeats += remaining
                    break
            cache[hashed] = valid
            return valid

        if not check(protected + mutable):
            raise ValueError("initial replay does not reproduce authentic paired discrepancy")
        # A controller run beginning strictly after the source-authenticated
        # observation cannot causally affect a preceding checkpoint. Verify
        # removal with the SAME paired authentic oracle rather than inferring
        # semantic equivalence from a timeline alone. A spanning run remains.
        # This exact-horizon trial comes BEFORE ddmin to avoid spending the
        # small oracle budget testing implausibly large early-route deletions.
        post_observation_trial = False
        post_observation_removed_runs = 0
        partitions = 2
        exhausted = False
        if observation_frame is not None:
            prefix = [r for r in mutable if r.start <= observation_frame]
            if len(prefix) < len(mutable):
                post_observation_trial = True
                try:
                    if check(protected + prefix):
                        post_observation_removed_runs = len(mutable) - len(prefix)
                        mutable = prefix
                except StopIteration:
                    exhausted = True
        while mutable and not exhausted:
            count = len(mutable)
            span = math.ceil(count / partitions)
            changed = False
            for start in range(0, count, span):
                trial = mutable[:start] + mutable[start + span:]
                try:
                    reproduces = check(protected + trial)
                except StopIteration:
                    exhausted = True
                    break
                if reproduces:
                    mutable = trial
                    partitions = max(2, partitions - 1)
                    changed = True
                    break
            if exhausted:
                break
            if not changed:
                if partitions >= count:
                    break
                partitions = min(count, partitions * 2)
    final = protected + mutable
    report = {
        "schema": "ur-controller-reducer-report/1",
        "source_fixture_sha256": source_hash,
        "reduced_fixture_sha256": digest(encode(final)),
        "oracle_identity": dict(zip(FIELDS, base_identity)),
        "protected_before_frame": protected_before_frame,
        "observation_frame": observation_frame,
        "post_observation_trial": post_observation_trial,
        "post_observation_removed_runs": post_observation_removed_runs,
        "protected_runs": len(protected),
        "original_runs": len(runs),
        "reduced_runs": len(final),
        "removed_runs": len(runs) - len(final),
        "oracle_calls": calls,
        "negative_short_circuit_candidates": negative_short_circuits,
        "redundant_negative_oracle_calls_avoided": saved_negative_repeats,
        "native_skipped_oracle_calls": native_skips,
        "oracle_result_counts": observed_results,
        "native_skip_reason_counts": observed_skip_reasons,
        "candidates_tested": tests,
        "repeats_per_candidate": repeats,
        "budget_exhausted": exhausted,
        "release_gate_accepted": False,
    }
    return final, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--protected-before-frame", type=int, required=True)
    p.add_argument("--observation-frame", type=int,
                   help="authenticated original guest checkpoint; verify all strictly later input rows first")
    p.add_argument("--max-calls", type=int, default=60)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--oracle", nargs=argparse.REMAINDER, required=True)
    args = p.parse_args()
    argv = args.oracle[1:] if args.oracle and args.oracle[0] == "--" else args.oracle
    if not argv or len({args.input.resolve(), args.output.resolve(), args.report.resolve()}) != 3:
        p.error("need oracle executable and distinct input, output, report paths")
    result, report = reduce(
        load_controller_runs(args.input), digest(args.input.read_bytes()),
        args.protected_before_frame, argv, args.max_calls, args.repeats, args.timeout,
        args.observation_frame
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encode(result))
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
