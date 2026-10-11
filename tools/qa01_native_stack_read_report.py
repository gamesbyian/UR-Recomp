#!/usr/bin/env python3
"""Fail-closed count of native stack-byte *read attempts* after actual replay.

Reading a stack byte is not proof it was used for the result, that an
architectural pull consumed it, or that source Snes9x shares an NMI phase.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import qa01_original_fresh_switcher_01dd_report as pair

SCHEMA = "UR-QA01-NATIVE-SWITCHER-STACK-BUS-READ-CANDIDATES/1"
ROW = re.compile(
    r"^QANATIVEREAD f=(\d+) bank=([0-9A-F]{2}) addr=([0-9A-F]{4})"
    r" width=([12]) value=([0-9A-F]{4}) A=([0-9A-F]{4})"
    r" S=([0-9A-F]{4}) M=([01]) scope=([A-Za-z0-9_?]+)$"
)
LIMIT = 512
ARM = "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 A=4004 S=01DD scope=I_NMI_M1X1"


def summarize(log: str) -> dict:
    if len(log) > 131072:
        raise ValueError("native read journal exceeds small bounded window")
    lines = log.splitlines()
    if len(lines) > LIMIT + 1:
        raise ValueError("native read journal exceeded 512 rows and one arm")
    result = []
    last_frame = 5778
    arm_count = 0
    for raw in lines:
        if raw == ARM:
            if last_frame > 5781:
                raise ValueError("native 4004 writer arming row arrived after later-frame reads")
            last_frame = 5781
            arm_count += 1
            if arm_count > 1:
                raise ValueError("native read observer writer armed more than once")
            continue
        m = ROW.fullmatch(raw)
        if not m:
            raise ValueError("malformed native original-result WRAM read row")
        f, bank, addr, w, value, a, sp, mode, scope = m.groups()
        f, addr, w, word = int(f), int(addr, 16), int(w), int(value, 16)
        if (not 5778 <= f <= 5782 or f < last_frame
                or bank not in ("00", "7E", "80")
                or not (addr in (0x01DD, 0x01DE) if w == 1
                        else addr in (0x01DC, 0x01DD, 0x01DE))
                or (w == 1 and word > 0xFF)
                or len(scope) > 120):
            raise ValueError("native stack read escaped exact source window")
        last_frame = f
        touched = [f"7E:{addr + n:04X}"
                   for n in range(w) if addr + n in (0x01DD, 0x01DE)]
        result.append({
            "native_snes_frame_counter": f,
            "memory_bank_alias": bank,
            "word_start": f"{addr:04X}",
            "bus_read_width": w,
            "read_value": f"{word:04X}",
            "register_a_at_read": a,
            "stack_pointer_at_read": sp,
            "memory_width_flag_at_read": int(mode),
            "generated_or_interpreter_scope": scope,
            "target_stack_bytes_touched": touched,
            # ARM is emitted inside the independently recovered 4004
            # writer's WRAM callback, BEFORE the underlying store returns.
            # This is source order, not guest architectural liveness.
            "observed_after_4004_writer_callback_started": arm_count == 1,
            "register_s_does_not_prove_stack_instruction": True,
        })
    if arm_count != 1:
        raise ValueError("native read journal lacks unique actual 4004 NMI writer arming attestation")
    post_writer_same_frame_word_4004 = [
        x for x in result
        if x["observed_after_4004_writer_callback_started"]
        and x["native_snes_frame_counter"] == 5781
        and x["word_start"] == "01DD"
        and x["bus_read_width"] == 2
        and x["read_value"] == "4004"
    ]
    by_addr = {"7E:01DD": 0, "7E:01DE": 0}
    for row in result:
        for address in row["target_stack_bytes_touched"]:
            by_addr[address] += 1
    return {
        "schema": SCHEMA,
        "native_frame_bounds": [5778, 5782],
        "native_bus_read_attempt_count": len(result),
        "native_read_observer_armed_by_real_nmi_4004_writer": True,
        "native_bus_read_attempts_by_target": by_addr,
        "native_stack_read_attempts": result,
        "same_native_frame_post_writer_callback_read_4004_candidate_count":
            len(post_writer_same_frame_word_4004),
        "matched_word_read_is_stack_restore_candidate_not_proof": True,
        "zero_count_is_bounded_native_negative_not_no_reader_ever": len(result) == 0,
        "read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer": True,
        "native_cpu_frame_vs_source_snes9x_frame_unaligned": True,
        "no_guest_read_return_value_or_timing_changed": True,
        "release_complete_event_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--read-log", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    paired_bytes = args.paired_report.read_bytes()
    verified = pair.verify_original_native_pair(
        json.loads(paired_bytes.decode("utf-8")))
    observed = summarize(args.read_log.read_text(encoding="utf-8"))
    observed["independently_authenticated_original_native_pair"] = verified
    observed["paired_report_bytes_sha256"] = hashlib.sha256(paired_bytes).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(observed, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "native_stack_read_candidate_count": observed["native_bus_read_attempt_count"],
        "native_stack_read_counts": observed["native_bus_read_attempts_by_target"],
        "real_result_consumer_proven": False,
        "release_course_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
