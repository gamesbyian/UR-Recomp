#!/usr/bin/env python3
"""Classify original Snes9x 7E:01DD opcode writes during a REAL Switcher replay.

Requires the independent real-original/native 5782 host-boundary report,
unchanged source movie + real rendered timed finish. Does not mistake the
archived movie host 17030 for the stock replay's host 5781 or award QA credit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import re
from pathlib import Path

import qa01_native_switcher_stack_report as native
import report_qa01_switcher_stack_trace as stack

SCHEMA = "UR-QA01-ORIGINAL-FRESH-SWITCHER-01DD-OPCODE-WITNESS/1"
FIRST = 5778
LAST = 5782
TARGET = 0x01DD
SOURCE_WINDOW_SHA256 = "6b4df10995e1383f4323d66e3d9af92a42833085041bd26944b9be570211d65d"
ROM_SHA256 = native.EXPECTED_ROM_SHA
MOVIE_SHA256 = native.EXPECTED_MOVIE_SHA
MAX_WRITES = 50000
SAMPLE_LIMIT = 12
NMI = re.compile(
    r"^QASTACKNMI f=(\d+) v=(\d+) pc=([0-9A-F]{6}) "
    r"sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4}) "
    r"addr=01DD old=([0-9A-F]{2}) new=([0-9A-F]{2})$",
    re.MULTILINE,
)



def verify_original_native_pair(paired: dict) -> dict:
    evidence = native.validate_paired_guest_report(paired)
    comp = paired["comparison"]
    source = paired["original_source_event"]
    if (source["original_entry_frame"] != 12327
            or source["original_result_frame"] != 17030
            or source["source_active_frames_to_result"] != 4703
            or paired["original_movie_window_sha256"] != SOURCE_WINDOW_SHA256
            or comp["fresh_guest_entry_equivalent"] is not True
            or comp["original_source_entry_equivalent"] is not True
            or comp["rendered_result_and_score_text_matched"] is not True
            or comp["timed_race_or_circuit_result_visible"] is not True
            or comp["both_reached_terminal_menu"] is not True
            or comp["result_outside_active_race_in_both_guests"] is not True
            or comp["terminal_result_frame_matched"] is not False):
        raise ValueError("not an independent original 2014 source + real paired Switcher result")
    return evidence


def summarize_original(log: str, *, first: int = FIRST, last: int = LAST) -> dict:
    """Frame-bounded changed-byte *opcode scopes*, not native write attempts."""
    if not 0 <= first < last <= 100000 or last-first > 8:
        raise ValueError("unbounded original opcode observation")
    gate = list(stack.BEGIN.finditer(log))
    if len(gate) != 1:
        raise ValueError("original opcode CPU gate must be observed exactly once")
    f, vcounter, pc, sp = gate[0].groups()
    start = int(f)
    if start < first or start > first + 1 or not 0 <= int(vcounter) < 263:
        raise ValueError("original CPU gate does not match fresh Switcher result window")
    counts_by_frame, counts_by_pc, counts_by_opcode = Counter(), Counter(), Counter()
    sp_aligned = 0
    samples = []
    total = 0
    last_frame = start
    for m in stack.WRITE.finditer(log):
        frame, v, pc, op, sp0, sp1, addr, old, new = m.groups()
        f = int(frame)
        if (f < start or f > last or f < last_frame or int(addr,16) != TARGET
                or not 0 <= int(v) < 263 or old == new):
            raise ValueError("original CPU opcode changed an unapproved byte or frame")
        last_frame = f
        total += 1
        if total > MAX_WRITES:
            raise ValueError("original opcode scope observation exceeded safe limit")
        pc = f"{pc[:2]}:{pc[2:]}"
        counts_by_frame[f] += 1
        counts_by_pc[pc] += 1
        counts_by_opcode[op] += 1
        aligned = stack.stack_push_compatible(
            int(op,16),int(sp0,16),int(sp1,16),TARGET)
        if aligned:
            sp_aligned += 1
        if len(samples) < SAMPLE_LIMIT:
            samples.append({
                "original_cpu_frame":f, "ppu_vcounter":int(v),
                "original_opcode_pc":pc,"opcode":op,
                "stack_pointer_before":sp0,"stack_pointer_after":sp1,
                "old_byte":old,"new_byte":new,
                "push_opcode_and_stack_address_compatible":aligned,
            })
    nmi_entries=[]
    for m in NMI.finditer(log):
        frame,v,pc,nsp0,nsp1,old,new=m.groups()
        frame=int(frame)
        v=int(v)
        if frame < first or frame > last or not 0 <= v < 263:
            raise ValueError("original CPU NMI stack event escaped observed fresh result window")
        pre,post=int(nsp0,16),int(nsp1,16)
        pushed_width=(pre-post)&0xFFFF
        covers=(
            pushed_width in (3,4)
            and TARGET in {((pre-d)&0xFFFF) for d in range(pushed_width)}
        )
        nmi_entries.append({
            "original_cpu_frame":frame,"ppu_vcounter":v,
            "pre_nmi_guest_pc":f"{pc[:2]}:{pc[2:]}",
            "stack_pointer_before":nsp0,"stack_pointer_after":nsp1,
            "stack_push_width_compatible":pushed_width in (3,4),
            "nmi_stack_push_range_covers_01dd":covers,
            "old_byte":old,"new_byte":new,
            "01dd_changed_during_nmi_entry":old!=new,
        })
    if not nmi_entries:
        raise ValueError("original NMI entry was not observed; normal opcode scopes alone are incomplete")
    if [e["original_cpu_frame"] for e in nmi_entries] != sorted(
            e["original_cpu_frame"] for e in nmi_entries):
        raise ValueError("original NMI entry events were not chronological")
    return {
        "original_nmi_entry_events":nmi_entries,
        "original_nmi_entry_event_count":len(nmi_entries),
        "original_nmi_stack_range_covered_01dd":any(
            e["nmi_stack_push_range_covers_01dd"] for e in nmi_entries),
        "original_nmi_entry_changed_01dd":any(
            e["01dd_changed_during_nmi_entry"] for e in nmi_entries),
        "original_nmi_changed_byte_events_are_distinct_from_opcode_scopes":True,
        "schema": SCHEMA,
        "read_only_original_snes9x_wram_target": "7E:01DD",
        "original_cpu_frame_observation_window": [first,last],
        "cpu_gate_first_observed_frame":start,
        "cpu_gate_pc":gate[0].group(3)[:2]+":"+gate[0].group(3)[2:],
        "cpu_gate_initial_stack_pointer":sp,
        "total_original_changed_byte_opcode_scopes":total,
        "original_push_opcode_sp_address_compatible_scope_count":sp_aligned,
        "original_changed_byte_scopes_by_cpu_frame":dict(sorted(counts_by_frame.items())),
        "original_changed_byte_scopes_by_pc":dict(sorted(counts_by_pc.items())),
        "original_changed_byte_scopes_by_opcode":dict(sorted(counts_by_opcode.items())),
        "first_bounded_original_opcode_scope_examples":samples,
        "zero_opcode_changes_is_bounded_negative_not_never_writes":total==0,
        "NMI_entry_is_separately_observed_even_if_opcode_scope_count_zero":True,
        "source_reference_guest_fresh_host_phase_not_exact_ppu_cpu_boundary":True,
        "complete_event_release_credit":0,
        "interpretation": (
            "Only original Snes9x changed-byte opcode scopes at 7E:01DD in "
            "fresh original-reference CPU frames 5778..5782; native separate "
            "writer observations are WRAM write ATTEMPTS and may include "
            "same-value stores. No original/native instruction/stack timing "
            "proof, causal result-reader liveness or complete event admission."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--original-log",type=Path,required=True)
    ap.add_argument("--paired-report",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    pairing=verify_original_native_pair(json.loads(args.paired_report.read_text(encoding="utf-8")))
    observed=summarize_original(args.original_log.read_text(encoding="utf-8"))
    observed["independently_authenticated_original_native_pair"]=pairing
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(observed,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA01_ORIGINAL_FRESH_01DD="+json.dumps({
        "gate_frame":observed["cpu_gate_first_observed_frame"],
        "total_changed_byte_scopes":observed["total_original_changed_byte_opcode_scopes"],
        "nmi_entry_events":observed["original_nmi_entry_events"],
        "nmi_01dd_pushed_range":observed["original_nmi_stack_range_covered_01dd"],
        "nmi_01dd_byte_changed":observed["original_nmi_entry_changed_01dd"],
        "by_original_pc":observed["original_changed_byte_scopes_by_pc"],
        "by_original_cpu_frame":observed["original_changed_byte_scopes_by_cpu_frame"],
        "by_opcode":observed["original_changed_byte_scopes_by_opcode"],
        "samples":observed["first_bounded_original_opcode_scope_examples"],
        "release_complete_event_credit":0,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
