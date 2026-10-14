#!/usr/bin/env python3
"""Independent, ROM-free inspection of *retained* native Windows CI 2P files.

The existing Windows producer currently does NOT archive these two files.
This tool remains a prospective, fail-closed consumer until exact synthetic
CI-owned run+match bytes are furnished; it never certifies original parity,
consumer device tests, or a Windows release candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from check_baldosa_win32_native_2p_records_evidence import (
    audit_hosted_native_2p_records,
)
from verify_windows_tournament_acceptance_receipt import fnv_hex

USA_ROM_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
BALDOSA_COMPAT = (
    "baldosa-10b864b9d14a7b7416dd909eb7b054c88faef101"
    "-snes-075fbe4c8e0d97b0013be541795c39cb644a9709-v1"
)
RUN_KEYS = (
    "game", "rom_sha256", "build_compat", "course", "mode",
    "elapsed_ticks60", "frame_count", "terminal_digest",
)
MATCH_KEYS = (
    "run_checksum", "course", "outcome", "p1_result", "p2_result",
    "p1_profile", "p1_name", "p1_rider",
    "p2_profile", "p2_name", "p2_rider",
)
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
HEX64 = re.compile(r"[0-9a-f]{16}\Z")
MAX_RUN_BYTES = 4 * 1024 * 1024
MAX_MATCH_BYTES = 64 * 1024


def canonical_lines(raw: bytes, bound: int) -> tuple[list[str], str]:
    if (
        not isinstance(raw, bytes) or not 0 < len(raw) <= bound
        or not raw.endswith(b"\n") or b"\r" in raw or b"\0" in raw
    ):
        raise ValueError("native CI saved artifact absent, oversized or noncanonical")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("native CI saved artifact contains non-ASCII bytes") from exc
    if (
        len(lines) < 3 or any(not line for line in lines)
        or not lines[-1].startswith("checksum ")
        or not HEX64.fullmatch(lines[-1][9:])
    ):
        raise ValueError("native CI saved artifact missing canonical v1 trailer")
    body = ("\n".join(lines[:-1]) + "\n").encode("ascii")
    checksum = fnv_hex(body)
    if lines[-1] != "checksum " + checksum:
        raise ValueError("native CI saved artifact has invalid internal checksum")
    return lines, checksum


def audit_raw_native_ci_two_player_pair(
    raw_report: bytes, raw_played: bytes, raw_fresh: bytes,
    *, run_name: str, raw_run: bytes, raw_match: bytes,
) -> dict[str, object]:
    """Reconcile actual pair bytes with exact hosted source+Records logs.

    Caller MUST supply genuine saved CI files, not unit fixtures, for a real
    byte-inspection claim. This does not establish original-emulator truth.
    """
    log_evidence = audit_hosted_native_2p_records(
        raw_report, raw_played, raw_fresh,
    )
    report = json.loads(raw_report.decode("utf-8"))
    hashes = report["canonical_match_artifact_sha256"]
    if (
        type(run_name) is not str
        or run_name != log_evidence["hosted_native_2p_saved_run_capture_basename"]
        or set(hashes) != {run_name, run_name + ".urmatch"}
        or not isinstance(raw_run, bytes)
        or not isinstance(raw_match, bytes)
        or len(raw_run) > MAX_RUN_BYTES
        or len(raw_match) > MAX_MATCH_BYTES
        or hashlib.sha256(raw_run).hexdigest() != hashes[run_name]
        or hashlib.sha256(raw_match).hexdigest() != hashes[run_name + ".urmatch"]
    ):
        raise ValueError("native CI pair bytes do not match exact source capture and report hashes")
    run_rows, run_checksum = canonical_lines(raw_run, MAX_RUN_BYTES)
    side_rows, _ = canonical_lines(raw_match, MAX_MATCH_BYTES)
    if (
        len(run_rows) < 12 or run_rows[0] != "URRUN 1"
        or run_rows[-2] != "END" or len(side_rows) != 13
        or side_rows[0] != "UR-MULTIPLAYER-MATCH/1"
    ):
        raise ValueError("native CI run or paired match has invalid v1 framing")
    run_values: dict[str, str] = {}
    for name, row in zip(RUN_KEYS, run_rows[1:9]):
        prefix = name + " "
        if not row.startswith(prefix) or len(row) == len(prefix):
            raise ValueError("native CI .urrun scalar layout invalid")
        run_values[name] = row[len(prefix):]
    src = report["source_result"]
    expected = {
        "game": "uniracers-usa",
        "rom_sha256": USA_ROM_SHA256,
        "build_compat": BALDOSA_COMPAT,
        "course": "course:01",
        "mode": "race-2p",
        "elapsed_ticks60": str(
            (min(src["p1_hundredths"], src["p2_hundredths"]) * 60 + 50) // 100
        ),
        "frame_count": str(src["source_input_frames"]),
        "terminal_digest": "-",
    }
    if run_values != expected:
        raise ValueError("native CI .urrun provenance, time or frame count disagrees with source")
    expected_runs = int(re.search(
        r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p .+ input_runs=(\d+) published=1\r?$",
        raw_played.decode("utf-8"),
    ).group(1))
    rows = run_rows[9:-2]
    if len(rows) != expected_runs:
        raise ValueError("native CI run has wrong source input-run count")
    prior_end = 0
    seen_p1 = seen_p2 = False
    frames = int(run_values["frame_count"])
    for row in rows:
        fields = row.split(" ")
        if (
            len(fields) != 5 or fields[0] != "input"
            or not all(re.fullmatch(r"[0-9]+", x) for x in fields[1:3])
            or not all(re.fullmatch(r"[0-9a-fA-F]+", x) for x in fields[3:])
        ):
            raise ValueError("native CI run contains malformed resolved input")
        start, duration = int(fields[1]), int(fields[2])
        p1, p2 = int(fields[3], 16), int(fields[4], 16)
        if (
            duration < 1 or start < prior_end or start + duration > frames
            or p1 > 0xfff or p2 > 0xfff or not (p1 or p2)
        ):
            raise ValueError("native CI run contains overlapping/invalid input span")
        prior_end = start + duration
        seen_p1 |= p1 != 0
        seen_p2 |= p2 != 0
    if not (seen_p1 and seen_p2):
        raise ValueError("native CI source-confirmed 2P run lacks either input lane")

    values: dict[str, str] = {}
    for name, row in zip(MATCH_KEYS, side_rows[1:-1]):
        prefix = name + " "
        if not row.startswith(prefix) or len(row) == len(prefix):
            raise ValueError("native CI .urmatch field layout invalid")
        values[name] = row[len(prefix):]
    expected_match = {
        "run_checksum": run_checksum,
        "course": "course:01",
        "outcome": {0: "draw", 1: "p1", 2: "p2"}[src["winner"]],
        "p1_result": str(src["p1_hundredths"]),
        "p2_result": str(src["p2_hundredths"]),
        "p1_profile": "native-ci-rider".encode("ascii").hex(),
        "p1_name": "MIKE".encode("ascii").hex(),
        "p1_rider": "0",
        "p2_profile": "native-ci-second".encode("ascii").hex(),
        "p2_name": "MARTIN".encode("ascii").hex(),
        "p2_rider": "2",
    }
    if values != expected_match:
        raise ValueError("native CI .urmatch participant, result or run checksum differs from source")
    return {
        "scope": "synthetic-ci-native-2p-pair-byte-and-codec-consistency",
        "run_name": run_name,
        "run_sha256_independently_verified": hashes[run_name],
        "match_sha256_independently_verified": hashes[run_name + ".urmatch"],
        "run_artifact_fnv16_independently_verified": run_checksum,
        "source_input_frames": frames,
        "source_input_runs": len(rows),
        "saved_run_and_match_bytes_independently_decoded": True,
        "strict_original_emulator_event_parity_verified": False,
        "physical_windows_hardware_verified": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }


def read_bounded(path: Path, limit: int) -> bytes:
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= limit:
        raise ValueError("native CI evidence file missing, linked or oversized")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "played-log", "fresh-log", "run", "match"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = audit_raw_native_ci_two_player_pair(
        read_bounded(args.report, 64 * 1024),
        read_bounded(args.played_log, 2 * 1024 * 1024),
        read_bounded(args.fresh_log, 2 * 1024 * 1024),
        run_name=args.run.name,
        raw_run=read_bounded(args.run, MAX_RUN_BYTES),
        raw_match=read_bounded(args.match, MAX_MATCH_BYTES),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
