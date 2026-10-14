#!/usr/bin/env python3
"""Read-only ROM-free decoder for a FUTURE retained CI-created MIKE 1P .urrun.

The existing green Win32 three-game run 38503716264 archived only the producer
SHA-256 and game logs, not the saved run bytes. No actual run file has been
independently rehashed; do not apply this decoder to substitute dummy bytes
for the missing evidence or turn hosted results into release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from check_baldosa_native_ci_pair_bytes_qa import (
    BALDOSA_COMPAT, MAX_RUN_BYTES, RUN_KEYS, USA_ROM_SHA256,
    canonical_lines, read_bounded,
)
from check_baldosa_win32_first_racer_earned_records_qa import (
    RESULT, audit_hosted_first_racer_earned_1p,
)

SCALAR_N = len(RUN_KEYS)
DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")
HEX_MASK = re.compile(r"(?:0|[1-9A-F][0-9A-F]*)\Z")
SPLIT_ID = re.compile(r"[A-Za-z0-9_.:-]{1,160}\Z")
RUN_NAME = re.compile(r"run-[0-9]{16}-[0-9]{4}\.urrun\Z")
MAX_LOG = 2 * 1024 * 1024


def inspect_earned_mike_1p_run_bytes(
    raw_report: bytes, raw_created: bytes, raw_played: bytes,
    raw_fresh: bytes, *, run_name: str, raw_run: bytes,
) -> dict[str, object]:
    """Return bounded BYTE and codec consistency only, never release credit."""
    logs = audit_hosted_first_racer_earned_1p(
        raw_report, raw_created, raw_played, raw_fresh,
    )
    reported_sha = logs["hosted_one_canonical_urrun_sha256_producer_reported"]
    if (
        type(run_name) is not str
        or RUN_NAME.fullmatch(run_name) is None
        or run_name != logs["hosted_played_1p_capture_basename"]
        or type(raw_run) is not bytes
        or not 0 < len(raw_run) <= MAX_RUN_BYTES
        or hashlib.sha256(raw_run).hexdigest() != reported_sha
    ):
        raise ValueError("CI first-racer raw .urrun differs from source name or producer SHA-256")
    rows, internal_fingerprint = canonical_lines(raw_run, MAX_RUN_BYTES)
    if (
        len(rows) < 12 or rows[0] != "URRUN 1" or rows[-2] != "END"
    ):
        raise ValueError("CI first-racer run has invalid v1 header/framing")
    scalars: dict[str, str] = {}
    for name, row in zip(RUN_KEYS, rows[1:1 + SCALAR_N]):
        prefix = name + " "
        if not row.startswith(prefix) or row.count(" ") != 1:
            raise ValueError("CI first-racer run has invalid scalar order or layout")
        scalars[name] = row[len(prefix):]
    expected = {
        "game": "uniracers-usa",
        "rom_sha256": USA_ROM_SHA256,
        "build_compat": BALDOSA_COMPAT,
        "course": "course:01",
        "mode": "race-1p",
        "elapsed_ticks60": str(logs["hosted_played_1p_finish_ticks60"]),
        "frame_count": str(logs["hosted_played_1p_input_frames"]),
        "terminal_digest": "-",
    }
    if scalars != expected:
        raise ValueError("CI first-racer run provenance/timing is inconsistent with native source")
    matches = list(RESULT.finditer(raw_played.decode("utf-8")))
    if len(matches) != 1:
        raise ValueError("CI first-racer source result ambiguous")
    expected_input_runs = int(matches[0].group(5))
    if not 1 <= expected_input_runs <= 100_000:
        raise ValueError("CI first-racer source input-run count is invalid")
    split_clock = 0
    prior_input_end = 0
    prior_mask: tuple[int, int] | None = None
    seen_p1 = False
    inputs = 0
    splits = 0
    finish_ids: list[str] = []
    input_seen = False
    frames = logs["hosted_played_1p_input_frames"]
    ticks = logs["hosted_played_1p_finish_ticks60"]
    for row in rows[1 + SCALAR_N:-2]:
        fields = row.split(" ")
        if len(fields) == 3 and fields[0] == "split":
            if input_seen or not SPLIT_ID.fullmatch(fields[1]) or not DECIMAL.fullmatch(fields[2]):
                raise ValueError("CI first-racer run contains malformed/out-of-order split")
            split_time = int(fields[2])
            if split_time < split_clock or split_time > ticks:
                raise ValueError("CI first-racer run has impossible split time")
            split_clock = split_time
            finish_ids.append(fields[1])
            splits += 1
        elif len(fields) == 5 and fields[0] == "input":
            input_seen = True
            if (
                not DECIMAL.fullmatch(fields[1])
                or not DECIMAL.fullmatch(fields[2])
                or not HEX_MASK.fullmatch(fields[3])
                or not HEX_MASK.fullmatch(fields[4])
            ):
                raise ValueError("CI first-racer run has noncanonical input span or mask")
            start, duration = int(fields[1]), int(fields[2])
            p1, p2 = int(fields[3], 16), int(fields[4], 16)
            if (
                not 0 < duration <= frames
                or start < prior_input_end or start + duration > frames
                or not 0 < p1 <= 0x0fff or p2 != 0
                or (start == prior_input_end and prior_mask == (p1, p2))
            ):
                raise ValueError("CI first-racer run violates source 1P input lane/compaction")
            prior_input_end = start + duration
            prior_mask = (p1, p2)
            seen_p1 = True
            inputs += 1
        else:
            raise ValueError("CI first-racer run has unexpected v1 row")
    # Source assemble_baldosa_native_run_record.cpp inserts exactly ONE
    # finish split for TimedOnePlayerRace. A splitless or extra/mismatched
    # split run could have a valid FNV and producer SHA yet never have been
    # emitted by the actual native 1P assembler.
    if not seen_p1 or inputs != expected_input_runs:
        raise ValueError("CI first-racer run lacks the exact native source P1 input-run count")
    if splits != 1 or split_clock != ticks or finish_ids != ["finish"]:
        raise ValueError("CI first-racer run lacks the exact native source finish split")

    return {
        "scope": "synthetic-ci-first-created-mike-native-1p-urrun-byte-and-codec-consistency",
        "saved_run_basename": run_name,
        "saved_run_sha256_independently_recomputed": reported_sha,
        "saved_run_internal_fnv1a64_independently_recomputed": internal_fingerprint,
        "saved_run_v1_codec_decoded": True,
        "native_source_frame_count_matched": frames,
        "native_source_result_ticks60_matched": ticks,
        "native_source_resolved_input_runs_matched": inputs,
        "run_split_count_parsed_not_original_verified": splits,
        "original_emulator_event_parity_accepted": False,
        "physical_controller_audio_display_verified": False,
        "approved_merged_main_release_candidate": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "created-log", "played-log", "fresh-log", "run"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = inspect_earned_mike_1p_run_bytes(
        read_bounded(args.report, 64 * 1024),
        read_bounded(args.created_log, MAX_LOG),
        read_bounded(args.played_log, MAX_LOG),
        read_bounded(args.fresh_log, MAX_LOG),
        run_name=args.run.name,
        raw_run=read_bounded(args.run, MAX_RUN_BYTES),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
