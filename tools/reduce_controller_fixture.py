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
    return tuple(receipt[k] for k in FIELDS)


def reduce(runs, source_hash, protected_before_frame, oracle,
           max_calls=60, repeats=2, timeout=120):
    if not runs or protected_before_frame < 1 or not oracle:
        raise ValueError("need source runs, protected original prefix and oracle")
    if not (1 <= repeats <= 5 and repeats <= max_calls <= 10000 and 1 <= timeout <= 3600):
        raise ValueError("invalid execution budget")
    protected = [r for r in runs if r.start < protected_before_frame]
    mutable = [r for r in runs if r.start >= protected_before_frame]
    base_identity = None
    calls = tests = 0
    cache = {}
    with tempfile.TemporaryDirectory(prefix="ur-replay-reduce-") as tmp:
        candidate = Path(tmp) / "candidate.script"
        receipt_path = Path(tmp) / "receipt.json"

        def check(sequence):
            nonlocal base_identity, calls, tests
            raw = encode(sequence)
            hashed = digest(raw)
            if hashed in cache:
                return cache[hashed]
            if calls + repeats > max_calls:
                raise StopIteration
            tests += 1
            valid = True
            for _ in range(repeats):
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
                if base_identity is None:
                    base_identity = identity
                elif base_identity != identity:
                    raise ValueError("oracle provenance/semantic identity changed")
                if not (receipt["result"] == "reproduced" and
                        receipt["original_valid"] and receipt["native_valid"]):
                    valid = False
            cache[hashed] = valid
            return valid

        if not check(protected + mutable):
            raise ValueError("initial replay does not reproduce authentic paired discrepancy")
        partitions = 2
        exhausted = False
        while mutable:
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
        "protected_runs": len(protected),
        "original_runs": len(runs),
        "reduced_runs": len(final),
        "removed_runs": len(runs) - len(final),
        "oracle_calls": calls,
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
        args.protected_before_frame, argv, args.max_calls, args.repeats, args.timeout
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encode(result))
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
