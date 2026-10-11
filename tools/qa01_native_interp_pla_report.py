#!/usr/bin/env python3
"""Original/native-provenanced native *interpreter* PLA scope, no course credit."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import qa01_original_fresh_switcher_01dd_report as original
import qa01_native_stack_read_report as reads

SCHEMA = "UR-QA01-SWITCHER-NATIVE-INTERPRETER-PLA-SCOPE/1"
LIMIT = 64
ROW = re.compile(
    r"^QANATIVEINTPLA f=(\d+) k=([0-9A-F]{2}) pcnext=([0-9A-F]{4})"
    r" sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4})"
    r" a0=([0-9A-F]{4}) a1=([0-9A-F]{4})"
    r" m0=([01]) e0=([01]) armed=([01])$"
)


def summarize(log: str) -> dict:
    if len(log) > 20000 or len(log.splitlines()) > LIMIT:
        raise ValueError("unbounded original/native Switcher interpreter PLA scope")
    result = []
    previous_frame = 5778
    previously_armed = False
    for line in log.splitlines():
        m = ROW.fullmatch(line)
        if not m:
            raise ValueError("malformed native interpreter PLA or overflow record")
        f, k, pc, sp0, sp1, a0, a1, m0, e0, armed = m.groups()
        f, sp0n, sp1n = int(f), int(sp0, 16), int(sp1, 16)
        width = 1 if m0 == "1" else 2
        observed_arm = armed == "1"
        if (not 5778 <= f <= 5782 or f < previous_frame
                or not 0x01DB <= sp0n <= 0x01DD
                or sp1n != sp0n + width
                or (e0 == "1" and m0 == "0")
                or (width == 1 and (int(a0, 16) & 0xFF00) !=
                    (int(a1, 16) & 0xFF00))
                or (f < 5781 and observed_arm)
                or (f > 5781 and not observed_arm)
                or (previously_armed and not observed_arm)):
            raise ValueError("native interpreter PLA stack, frame, or writer chronology invalid")
        previous_frame = f
        previously_armed = observed_arm
        first_byte, last_byte = sp0n + 1, sp1n
        touched = [
            f"7E:{address:04X}"
            for address in (0x01DD, 0x01DE)
            if first_byte <= address <= last_byte
        ]
        result.append({
            "native_snes_frame_counter": f,
            "interpreter_program_bank": k,
            "interpreter_post_opcode_fetch_pc": pc,
            "interpreter_pre_pull_stack_pointer": sp0,
            "interpreter_post_pull_stack_pointer": sp1,
            "interpreter_accumulator_before": a0,
            "interpreter_accumulator_after": a1,
            "interpreter_accumulator_width_bytes": width,
            "interpreter_emulation_mode_before": e0 == "1",
            "real_native_4004_writer_callback_precedes_interpreter_pla": observed_arm,
            "physically_touched_stack_bytes": touched,
            "guest_pla_opcode_executed": True,
            "interpreter_pc_is_post_fetch_not_exact_instruction_pc": True,
        })
    saved_word = [
        row for row in result
        if row["native_snes_frame_counter"] == 5781
        and row["interpreter_pre_pull_stack_pointer"] == "01DC"
        and row["interpreter_post_pull_stack_pointer"] == "01DE"
        and row["interpreter_accumulator_after"] == "4004"
        and row["interpreter_accumulator_width_bytes"] == 2
        and row["interpreter_emulation_mode_before"] is False
        and row["real_native_4004_writer_callback_precedes_interpreter_pla"] is True
    ]
    return {
        "schema": SCHEMA,
        "native_interpreter_pla_records": result,
        "native_interpreter_pla_observation_count": len(result),
        "native_interpreter_saved_4004_pla_candidate_count": len(saved_word),
        "native_interpreter_pla_candidate_not_original_native_phase_or_gameplay_causality": True,
        "no_interpreter_pla_observed_does_not_rule_out_aot_or_other_reads": True,
        "interpreter_stack_sp_and_m_are_internal_registers_not_host_cpu_state": True,
        "source_original_and_native_cpu_frame_alignment_proven": False,
        "release_complete_event_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--interp-log", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--native-read-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    paired_bytes = args.paired_report.read_bytes()
    prov = original.verify_original_native_pair(json.loads(paired_bytes.decode("utf-8")))
    read_report = json.loads(args.native_read_report.read_text(encoding="utf-8"))
    digest = hashlib.sha256(paired_bytes).hexdigest()
    if (not isinstance(read_report, dict) or read_report.get("schema") != reads.SCHEMA
            or read_report.get("paired_report_bytes_sha256") != digest
            or read_report.get("independently_authenticated_original_native_pair") != prov
            or read_report.get("native_read_observer_armed_by_real_nmi_4004_writer") is not True
            or read_report.get("release_complete_event_credit") != 0):
        raise ValueError("native interpreter opcode scope not tied to actual saved-4004 writer")
    result = summarize(args.interp_log.read_text(encoding="utf-8"))
    result["independently_authenticated_original_native_pair"] = prov
    result["paired_report_bytes_sha256"] = digest
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "native_executed_interpreter_plas_in_target_stack_window":
            result["native_interpreter_pla_observation_count"],
        "native_saved_4004_interpreter_pla_candidates":
            result["native_interpreter_saved_4004_pla_candidate_count"],
        "original_native_phase_proven": False,
        "release_course_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
