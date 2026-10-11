#!/usr/bin/env python3
"""Fail-closed pinned native NMI word-write beam sampler.

The framework v/h clock is not automatically original Snes9x CPU phase.
Requires independent exact original/native Switcher result provenance and
one actual 16-bit native I_NMI_M1X1 writer of word 4004 at 7E:01DD.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import qa01_original_fresh_switcher_01dd_report as original
import qa01_native_switcher_stack_report as native

SCHEMA = "UR-QA01-NATIVE-SWITCHER-I_NMI-BEAM-WRITER/1"
BEAM = re.compile(
    r"(?:^| )QAbeam_v=(\\d+) QAbeam_h=(\\d+) "
    r"QAbeam_master=(\\d+) QAcpu_master=(\\d+)$"
)
MAX_LINES = 50000


def summarize(log: str) -> dict:
    if not log.strip():
        raise ValueError("missing actual bounded native WRAM write log")
    witness = []
    previous = 5778
    lines = log.splitlines()
    if len(lines) > MAX_LINES:
        raise ValueError("unbounded native writer trace")
    for line in lines:
        match = native.WRITE.fullmatch(line)
        if not match:
            raise ValueError("malformed pinned native WRAM logger row")
        frame, bank, addr, word, width, scope = match.groups()
        frame = int(frame)
        address, value = int(addr, 16), int(word, 16)
        width = int(width)
        if (frame < previous or not 5778 <= frame <= 5782
                or address != 0x01DD or width not in (1, 2)
                or bank.upper() not in ("00", "7E", "80")):
            raise ValueError("native NMI beam log escaped pinned writer bounds")
        previous = frame
        stamp = BEAM.search(scope)
        if stamp:
            if (width != 2 or not scope.startswith("I_NMI_M1X1 ")
                    or frame != 5781 or value != 0x4004
                    or " A=4004 " not in scope
                    or " S=01DD " not in scope
                    or " M=0 " not in scope):
                raise ValueError("native beam stamp not bound to witnessed I_NMI 4004 PHA")
            v, h, bm, cm = map(int, stamp.groups())
            if not (0 <= v < 263 and 0 <= h <= 1364 and
                    0 <= bm and 0 <= cm):
                raise ValueError("invalid native host-beam/CPU master clock")
            witness.append({
                "native_host_frame": frame,
                "generated_owner": "I_NMI_M1X1",
                "wram_write_destination": "7E:01DD",
                "stack_word_saved": "4004",
                "accumulator_at_write": "4004",
                "stack_pointer_at_write": "01DD",
                "framework_beam_vpos": v,
                "framework_beam_hpos": h,
                "framework_beam_master_timestamp": bm,
                "native_cpu_master_cycles": cm,
            })
        elif "QAbeam_" in scope:
            raise ValueError("partial or misplaced native beam stamp")
    if len(witness) != 1:
        raise ValueError("native exact NMI save did not yield one beam observation")
    return {
        "schema": SCHEMA,
        "native_observation_host_frame_window": [5778, 5782],
        "native_original_nmi_writer_beam": witness[0],
        "framework_beam_vs_original_cpu_phase_unaligned": True,
        "native_frame_counter_vs_original_icpu_frame_unaligned": True,
        "writer_attempt_not_guest_scoring_consumer": True,
        "accepted_usa_course_count_added": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wlog", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    paired = json.loads(args.paired_report.read_text(encoding="utf-8"))
    verified = original.verify_original_native_pair(paired)
    result = summarize(args.wlog.read_text(encoding="utf-8"))
    result["exact_original_native_switcher_pair_provenance"] = verified
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "native_nmi_beam": result["native_original_nmi_writer_beam"],
        "original_native_exact_cpu_beam_phase_proven": False,
        "release_course_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
