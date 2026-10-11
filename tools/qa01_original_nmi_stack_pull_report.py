#!/usr/bin/env python3
"""Fail-closed classification of source Snes9x Switcher stack-pull candidates.

Read-only observations from a disposable, original Snes9x CPU. A matching
architectural pull is a candidate reader; this does not prove a result-critical
consumer or native/original instruction and beam parity. Zero pulls is a
bounded negative, not proof no instruction read the addresses.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import qa01_original_nmi_pha_accumulator_report as nmi
import qa01_original_fresh_switcher_01dd_report as original

SCHEMA = "UR-QA01-ORIGINAL-SWITCHER-NMI-STACK-PULL-SCOPES/1"
PULL = re.compile(
    r"^QANMIPULL f=(\d+) v=(\d+) pc=([0-9A-F]{6}) op=([0-9A-F]{2}) "
    r"sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4}) width=(\d+) "
    r"pl0=([0-9A-F]{2}) pl1=([0-9A-F]{2}) "
    r"a0=([0-9A-F]{4}) a1=([0-9A-F]{4}) "
    r"dd=([0-9A-F]{2}) de=([0-9A-F]{2}) "
    r"touches_dd=([01]) touches_de=([01]) f1=(\d+)$",
    re.MULTILINE,
)
RTI = re.compile(
    r"^QANMIRTI f=(\d+) v0=(\d+) v1=(\d+) pc=([0-9A-F]{6}) nextpc=([0-9A-F]{6}) "
    r"pb0=([0-9A-F]{2}) pb1=([0-9A-F]{2}) "
    r"sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4}) "
    r"a0=([0-9A-F]{4}) a1=([0-9A-F]{4}) "
    r"pl0=([0-9A-F]{2}) pl1=([0-9A-F]{2}) "
    r"cyc0=(-?\d+) cyc1=(-?\d+) f1=(\d+)$",
    re.MULTILINE,
)
MAX_RTIS = 16
MAX_PULLS = 64
STACK_LOW, STACK_HIGH = 0x0100, 0x01FF
TARGET_DD, TARGET_DE = 0x01DD, 0x01DE


def expected_pull_width(opcode: int, p: int) -> int:
    if opcode == 0x68:  # PLA
        return 1 if p & 0x20 else 2
    if opcode in (0xFA, 0x7A):  # PLX / PLY
        return 1 if p & 0x10 else 2
    if opcode == 0x2B:  # PLD
        return 2
    if opcode in (0xAB, 0x28):  # PLB / PLP
        return 1
    raise ValueError(f"not an approved stack pull opcode: {opcode:02X}")


def summarize(log: str, *, first: int = 5778, last: int = 5782) -> dict:
    if not (type(first) is int and type(last) is int and 0 <= first <= last):
        raise ValueError("invalid original CPU-frame bounds")
    # This crosschecks actual independent original NMI entries and 01DD writer,
    # rather than admitting a synthetic stand-alone QANMIPULL line.
    original_context = nmi.summarize(log, first=first, last=last)
    matches = list(PULL.finditer(log))
    # Do not silently drop truncated or modified instrumentation lines.
    if sum(line.startswith("QANMIPULL") for line in log.splitlines()) != len(matches):
        raise ValueError("malformed original QANMIPULL trace row")
    if len(matches) > MAX_PULLS:
        raise ValueError("unbounded original stack pull trace")
    rows = []
    for match in matches:
        (frame_s, v_s, pc, op_s, sp0_s, sp1_s, width_s,
         pl0_s, pl1_s, a0, a1, dd, de, tdd_s, tde_s, f1_s) = match.groups()
        frame, frame_after = int(frame_s), int(f1_s)
        v, opcode, sp0, sp1 = int(v_s), int(op_s, 16), int(sp0_s, 16), int(sp1_s, 16)
        width, p0, p1 = int(width_s), int(pl0_s, 16), int(pl1_s, 16)
        tdd, tde = tdd_s == "1", tde_s == "1"
        exp_width = expected_pull_width(opcode, p0)
        exp_dd = sp0 < TARGET_DD <= sp0 + width
        exp_de = sp0 < TARGET_DE <= sp0 + width
        if (not first <= frame <= last
                or frame_after < frame or frame_after > last + 1
                or not 0 <= v < 263
                or not STACK_LOW <= sp0 <= STACK_HIGH
                or not STACK_LOW <= sp1 <= STACK_HIGH
                or width != exp_width or sp1 != sp0 + width
                or (tdd, tde) != (exp_dd, exp_de)
                or not (tdd or tde)
                or not re.fullmatch(r"[0-9A-F]{6}", pc)):
            raise ValueError("malformed original stack pull source scope")
        # A real PLA must load any target byte that its architectural pull
        # covers. This is stronger than merely observing the stack S delta.
        # In 8-bit M mode, the accumulator's B/high byte is preserved.
        verified_pla_bytes = 0
        if opcode == 0x68:
            after_a, before_a = int(a1, 16), int(a0, 16)
            if width == 1 and (after_a & 0xFF00) != (before_a & 0xFF00):
                raise ValueError("8-bit PLA unexpectedly changed preserved accumulator B")
            for address, raw in ((TARGET_DD, dd), (TARGET_DE, de)):
                displacement = address - (sp0 + 1)
                if 0 <= displacement < width:
                    if ((after_a >> (8 * displacement)) & 0xFF) != int(raw, 16):
                        raise ValueError("observed original PLA does not restore target stack byte")
                    verified_pla_bytes += 1
        # The preceding predicate separately validates numeric/architectural
        # fields. Changes in P or A are legal for PLP/PLA; do not equate them.
        rows.append({
            "original_cpu_frame_before": frame,
            "original_cpu_frame_after": frame_after,
            "ppu_vcounter_before": v,
            "opcode_pc": f"{pc[:2]}:{pc[2:]}",
            "opcode": f"{opcode:02X}",
            "stack_pointer_before": f"{sp0:04X}",
            "stack_pointer_after": f"{sp1:04X}",
            "architectural_stack_pull_bytes": width,
            "processor_status_low_before": f"{p0:02X}",
            "processor_status_low_after": f"{p1:02X}",
            "accumulator_before": a0,
            "accumulator_after": a1,
            "observed_01dd_byte_before": dd,
            "observed_01de_byte_before": de,
            "architecturally_touches_01dd": tdd,
            "architecturally_touches_01de": tde,
            "pla_loaded_target_bytes_verified": verified_pla_bytes,
        })
    # RTI records the interrupted CPU's architectural return, but a bare
    # opcode cannot prove whether this was NMI, IRQ or BRK.
    rti_matches = list(RTI.finditer(log))
    if sum(line.startswith("QANMIRTI") for line in log.splitlines()) != len(rti_matches):
        raise ValueError("malformed original QANMIRTI trace row")
    if len(rti_matches) > MAX_RTIS:
        raise ValueError("unbounded original RTI scope observation")
    pha_by_frame = {
        event["original_cpu_frame_before"]: event["accumulator_before"]
        for event in original_context["all_bounded_original_I_NMI_pha_register_scopes"]
    }
    rti_rows = []
    for match in rti_matches:
        (f0s, v0s, v1s, pc, nextpc, pb0, pb1, sp0s, sp1s,
         a0, a1, pl0, pl1, cyc0s, cyc1s, f1s) = match.groups()
        f0, f1 = int(f0s), int(f1s)
        v0, v1, sp0, sp1 = int(v0s), int(v1s), int(sp0s, 16), int(sp1s, 16)
        cyc0, cyc1 = int(cyc0s), int(cyc1s)
        if (not first <= f0 <= last or not f0 <= f1 <= last + 1
                or not 0 <= v0 < 263 or not 0 <= v1 < 263
                or not STACK_LOW <= sp0 <= STACK_HIGH
                or not STACK_LOW <= sp1 <= STACK_HIGH
                or sp1 - sp0 not in (3, 4)
                or int(nextpc[:2], 16) != int(pb1, 16)
                or a0 != a1 or not -1000000 <= cyc0 <= 1000000
                or not -1000000 <= cyc1 <= 1000000):
            raise ValueError("impossible original RTI register or stack restoration")
        rti_rows.append({
            "original_cpu_frame_before": f0,
            "original_cpu_frame_after": f1,
            "ppu_vcounter_before": v0,
            "ppu_vcounter_after": v1,
            "opcode_pc": f"{pc[:2]}:{pc[2:]}",
            "resumed_guest_pc": f"{nextpc[:2]}:{nextpc[2:]}",
            "program_bank_before": pb0,
            "program_bank_after": pb1,
            "stack_pointer_before": f"{sp0:04X}",
            "stack_pointer_after": f"{sp1:04X}",
            "architectural_return_frame_bytes": sp1-sp0,
            "accumulator_before": a0,
            "accumulator_after": a1,
            "processor_status_low_before": pl0,
            "processor_status_low_after": pl1,
            "cpu_cycles_before": cyc0,
            "cpu_cycles_after": cyc1,
            "same_cpu_frame_as_original_nmi_pha": f0 in pha_by_frame,
            "same_frame_pha_accumulator_equals_rti_A": (
                pha_by_frame[f0] == a0 if f0 in pha_by_frame else None
            ),
        })
    if any(a["original_cpu_frame_before"] > b["original_cpu_frame_before"]
           for a, b in zip(rti_rows, rti_rows[1:])):
        raise ValueError("original RTI candidates out of CPU-frame order")
    if any(a["original_cpu_frame_before"] > b["original_cpu_frame_before"]
           for a, b in zip(rows, rows[1:])):
        raise ValueError("original NMI stack pull observations out of order")
    # This witness certifies source eligibility, never relative game timing.
    return {
        "schema": SCHEMA,
        "original_cpu_frame_window": [first, last],
        "independent_original_nmi_pha_context_schema": original_context["schema"],
        "original_nmi_hardware_entries": len(original_context["original_nmi_hardware_entry_events"]),
        "original_01dd_pha_writer_confirmed": True,
        "observed_candidate_stack_pull_count": len(rows),
        "candidate_stack_pull_scopes": rows,
        "candidate_rti_scope_count": len(rti_rows),
        "candidate_rti_scopes": rti_rows,
        "rti_instruction_source_cannot_prove_interrupt_vector": True,
        "zero_count_is_bounded_negative_only": len(rows) == 0,
        "stack_reads_outside_named_pulls_not_excluded": True,
        "native_same_logical_cpu_beam_phase_not_proven": True,
        "original_native_result_guest_relative_parity": False,
        "release_complete_event_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--original-log", type=Path, required=True)
    parser.add_argument("--paired-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paired = json.loads(args.paired_report.read_text(encoding="utf-8"))
    authenticated = original.verify_original_native_pair(paired)
    result = summarize(args.original_log.read_text(encoding="utf-8"))
    result["independently_authenticated_original_native_pair"] = authenticated
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "original_nmi_entries": result["original_nmi_hardware_entries"],
        "candidate_stack_pulls": result["observed_candidate_stack_pull_count"],
        "candidate_rti_scopes": result["candidate_rti_scope_count"],
        "original_native_guest_relative_result_parity": False,
        "release_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
