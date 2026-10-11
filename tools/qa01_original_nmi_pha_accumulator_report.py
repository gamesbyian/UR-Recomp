#!/usr/bin/env python3
"""Validate exact source Snes9x NMI+6 PHA A/M/SP against real original Switcher.

A 5-frame READ-ONLY original CPU opcode observation is NOT a same-instruction
original/native match, an accumulator parity assertion, or a USA course pass.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import qa01_original_fresh_switcher_01dd_report as original

SCHEMA = "UR-QA01-ORIGINAL-SWITCHER-NMI-PHA-A-M-S-CONTEXT/1"
PHA = re.compile(
    r"^QAPHAREG f=(\d+) v=(\d+) pc=([0-9A-F]{6}) op=([0-9A-F]{2}) "
    r"sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4}) a0=([0-9A-F]{4}) a1=([0-9A-F]{4}) "
    r"pl0=([0-9A-F]{2}) pl1=([0-9A-F]{2}) m0=([01]) m1=([01]) "
    r"dd0=([0-9A-F]{2}) dd1=([0-9A-F]{2}) de0=([0-9A-F]{2}) de1=([0-9A-F]{2}) f1=(\d+)$",
    re.MULTILINE,
)
MAX_EVENTS = 12


def summarize(log: str, *, first: int = 5778, last: int = 5782) -> dict:
    # Also require a *real independently captured NMI entry* and exact old
    # 01DD write scope; no synthetic log without a true original episode.
    baseline = original.summarize_original(log, first=first, last=last)
    if (baseline["total_original_changed_byte_opcode_scopes"] != 1
            or baseline["original_changed_byte_scopes_by_pc"] != {"00:858E": 1}
            or baseline["original_changed_byte_scopes_by_opcode"] != {"48": 1}
            or baseline["original_changed_byte_scopes_by_cpu_frame"] != {5780: 1}
            or baseline["original_nmi_entry_event_count"] != 5):
        raise ValueError("not the real bounded original fresh Switcher I_NMI+6 PHA witness")
    samples = baseline["first_bounded_original_opcode_scope_examples"]
    if (len(samples) != 1 or samples[0]["stack_pointer_before"] != "01DE"
            or samples[0]["stack_pointer_after"] != "01DC"
            or samples[0]["old_byte"] != "08"
            or samples[0]["new_byte"] != "42"):
        raise ValueError("original 01DD changed-byte opcode source witness diverged")

    matches = list(PHA.finditer(log))
    if not matches or len(matches) > MAX_EVENTS:
        raise ValueError("missing or unbounded original live I_NMI+6 PHA register observations")
    rows = []
    seen = []
    for m in matches:
        (frame, vcounter, pc, op, sp0, sp1, a0, a1, pl0, pl1,
         m0, m1, dd0, dd1, de0, de1, frame_after) = m.groups()
        frame, frame_after, vcounter = int(frame), int(frame_after), int(vcounter)
        if (not first <= frame <= last or frame_after < frame or frame_after > last+1
                or not 0 <= vcounter < 263 or pc not in {"00858E", "80858E"}
                or op != "48" or m0 != "0" or m1 != "0"
                or int(sp0,16) - int(sp1,16) != 2
                or a0 != a1 or pl0 != pl1):
            raise ValueError("original PHA at wrong original PC/M state/frame/SP or mutates A/P")
        # 16-bit PHA writes low A to SP0-1, high A to SP0.
        if int(sp0,16)-1 == 0x01DD:
            if (int(a0,16) & 0xFF) != int(dd1,16):
                raise ValueError("original NMI PHA low stack byte does not equal pre-PHA A")
        if int(sp0,16) == 0x01DE:
            if (int(a0,16)>>8) != int(de1,16):
                raise ValueError("original NMI PHA high stack byte does not equal pre-PHA A")
        if seen and frame < seen[-1]:
            raise ValueError("original I_NMI PHA source frames are not chronological")
        seen.append(frame)
        rows.append({
            "original_cpu_frame_before":frame,
            "original_cpu_frame_after":frame_after,
            "ppu_vcounter_before":vcounter,
            "original_instruction_pc":f"{pc[:2]}:{pc[2:]}",
            "opcode":op,
            "stack_pointer_before":sp0,"stack_pointer_after":sp1,
            "accumulator_before":a0,"accumulator_after":a1,
            "processor_status_low_before":pl0,"processor_status_low_after":pl1,
            "memory_width_flag_before":int(m0),"memory_width_flag_after":int(m1),
            "01dd_before":dd0,"01dd_after":dd1,
            "01de_before":de0,"01de_after":de1,
            "low_byte_matches_accumulator":int(dd1,16)==(int(a0,16)&0xFF)
                 if int(sp0,16)-1==0x01DD else None,
        })
    desired=[r for r in rows if r["original_cpu_frame_before"]==5780
             and r["stack_pointer_before"]=="01DE"
             and r["stack_pointer_after"]=="01DC"
             and r["01dd_before"]=="08" and r["01dd_after"]=="42"]
    if len(desired)!=1:
        raise ValueError("original live PHA A register not linked to observed 01DD 08->42")
    chosen=desired[0]
    if int(chosen["accumulator_before"],16)&0xFF != 0x42:
        raise ValueError("original PHA low A differs from executed 01DD byte 42")
    return {
        "schema":SCHEMA,
        "observed_source_original_cpu_window":[first,last],
        "all_bounded_original_I_NMI_pha_register_scopes":rows,
        "confirmed_original_01dd_pha_register_scope":chosen,
        "original_nmi_hardware_entry_events":baseline["original_nmi_entry_events"],
        "independent_original_01dd_opcode_scope_events":samples,
        "original_cpu_vs_native_writer_frame_clocks_unaligned":True,
        "native_comparator_accumulator_word":"4004",
        "native_comparator_frame":5781,
        "full_result_onset_guest_relative_original_native_mismatch":[4704,4702],
        "complete_event_release_credit":0,
        "qualification":"A/M/S at original original-CPU PHA instruction, not native same-cycle parity. Do not waive strict terminal comparator or change original inputs.",
    }


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--original-log",type=Path,required=True)
    ap.add_argument("--paired-report",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    pair=json.loads(args.paired_report.read_text(encoding="utf-8"))
    qual=original.verify_original_native_pair(pair)
    data=summarize(args.original_log.read_text(encoding="utf-8"))
    data["independently_authenticated_original_native_pair"]=qual
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    row=data["confirmed_original_01dd_pha_register_scope"]
    print("QA01_ORIGINAL_NMI_PHA_A="+json.dumps({
        "confirmed_writer":row,
        "original_nmi_pha_accumulator_observations":len(data["all_bounded_original_I_NMI_pha_register_scopes"]),
        "original_vs_native_guest_relative_result_parity":False,
        "release_event_credit":0,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
