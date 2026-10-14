#!/usr/bin/env python3
"""Source-qualified, non-admitting Zoo original/native 0313 terminal writer crosswalk.

Use the ORIGINAL opcode pre/post WRAM observer and the NATIVE CPU-helper
logger on the same unchanged 2014 movie and independently measured guest
scene-entry clocks. A store scope is a candidate, not a proven root cause.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import baldosa_zoo_opcode_writer_report as source
import baldosa_zoo_native_write_chronology as guest

SCHEMA = "UR-QA01-ZOO-0313-TERMINAL-WRITER-CROSSWALK/1"
FRAMES = (5160, 5161, 5162, 5163)
# Independently measured from both original/native full-WRAM event probes,
# NOT derived from a one-frame normalized clock or a synthetic physics model.
EXPECTED = {
    "original": (1, 1, 0, 0x3D),
    "native": (1, 0, 0x3D, 0x3D),
}
EXPECTED_MENU = {
    "original": (0x16, 0x16, 0x16, 0xBC),
    "native": (0x16, 0x16, 0xBC, 0xBC),
}
# Original snesref emits a full framebuffer/PPU descriptor rather than the
# native host's 'ok'. Both formats certify the script tick; complete 128-KiB
# WRAM is verified separately for every selected boundary.
LOG = re.compile(
    r"^script f=(\d+) dump (scene-entered|boundary-(\d{5})) "
    r"(?:ok|fb=\d+x\d+ RGB565 sram=\d+ ppuw=\d+)$",
    re.MULTILINE,
)
ADDRESS = "7E:0313"


def logged_frames(log: str) -> tuple[int, dict[int, int]]:
    entries = [(int(host), tag, int(relative) if relative else None)
               for host, tag, relative in LOG.findall(log)]
    start = [host for host, tag, _ in entries if tag == "scene-entered"]
    if len(start) != 1 or start[0] <= 0:
        raise ValueError("missing or duplicated real Zoo scene-entry host receipt")
    entry = start[0]
    result = {}
    for relative in FRAMES:
        matches = [host for host, _, off in entries if off == relative]
        if len(matches) != 1 or matches[0] != entry + relative:
            raise ValueError(f"missing, duplicated or mistimed boundary-{relative:05d} guest receipt")
        result[relative] = matches[0]
    return entry, result


def samples(folder: Path, *, side: str) -> tuple[list[dict], dict[int, bytes]]:
    observed, images = [], {}
    for relative in FRAMES:
        p = folder / f"boundary-{relative:05d}.wram.bin"
        if p.is_symlink() or not p.is_file():
            raise ValueError(f"{side} missing genuine full-WRAM frame {relative}")
        raw = p.read_bytes()
        if len(raw) != 131072:
            raise ValueError(f"{side} incomplete genuine 128-KiB WRAM at {relative}")
        images[relative] = raw
        observed.append({
            "relative_host_frame": relative,
            "race_state_0313": raw[0x0313],
            "menu_009f": raw[0x009F],
            "course_00ce": raw[0x00CE],
            "full_wram_sha256": hashlib.sha256(raw).hexdigest(),
        })
    flags = tuple(row["race_state_0313"] for row in observed)
    menus = tuple(row["menu_009f"] for row in observed)
    if flags != EXPECTED[side] or menus != EXPECTED_MENU[side]:
        raise ValueError(f"{side} verified source Zoo terminal phase drifted: {flags}/{menus}")
    if any(row["course_00ce"] != 1 for row in observed):
        raise ValueError(f"{side} no longer on original Zoo circuit at result transition")
    return observed, images


def analyze(original_trace: str, native_trace: str,
            original_host_log: str, native_host_log: str,
            original_dir: Path, native_dir: Path) -> dict:
    src_entry, src_ticks = logged_frames(original_host_log)
    nat_entry, nat_ticks = logged_frames(native_host_log)
    src_samples, _ = samples(original_dir, side="original")
    nat_samples, _ = samples(native_dir, side="native")
    src_writes = [w for w in source.parse(original_trace)
                  if w["wram_address"] == ADDRESS and
                  src_entry + 5158 <= w["original_icpu_frame"] <= src_entry + 5165]
    native_writes, counts = guest.parse_writes(native_trace, entry_frame=nat_entry)
    nat_writes = [w for w in native_writes
                  if w["guest_address"] == ADDRESS and
                  nat_entry + 5158 <= w["native_host_pre_run_frame"] <= nat_entry + 5165]
    def original_boundary(prev: int, frame: int) -> list[dict]:
        expected_old, expected_new = EXPECTED["original"][FRAMES.index(prev)], EXPECTED["original"][FRAMES.index(frame)]
        return [w for w in src_writes
                if w["old"] == f"{expected_old:02X}" and w["new"] == f"{expected_new:02X}"]
    def native_boundary(prev: int, frame: int) -> list[dict]:
        expected_new = EXPECTED["native"][FRAMES.index(frame)]
        return [w for w in nat_writes if w["guest_value"] == f"{expected_new:02X}"]
    transitions = []
    for side, vals in EXPECTED.items():
        for before, after in zip(FRAMES, FRAMES[1:]):
            old, new = vals[FRAMES.index(before)], vals[FRAMES.index(after)]
            if old == new:
                continue
            candidates = (original_boundary(before, after) if side == "original"
                          else native_boundary(before, after))
            transitions.append({
                "engine": side,
                "original_or_native_guest_relative_hosts": [before, after],
                "observed_raw_0313": [old, new],
                "candidate_trace_scopes": candidates,
                "any_exact_value_candidate": bool(candidates),
                "cpu_instruction_phase_relative_to_host_dump_unproven": True,
            })
    return {
        "schema": SCHEMA,
        "original_host_scene_entry": src_entry,
        "native_host_scene_entry": nat_entry,
        "entry_host_offset_native_minus_original": nat_entry - src_entry,
        "original_verified_dump_host_ticks": src_ticks,
        "native_verified_dump_host_ticks": nat_ticks,
        "original_guest_samples": src_samples,
        "native_guest_samples": nat_samples,
        "original_cpu_0313_opcode_scope_rows": src_writes,
        "native_cpu_helper_0313_write_rows": nat_writes,
        "native_cpu_helper_log_counts": counts,
        "original_trace_sha256": hashlib.sha256(original_trace.encode()).hexdigest(),
        "native_trace_sha256": hashlib.sha256(native_trace.encode()).hexdigest(),
        "original_host_log_sha256": hashlib.sha256(original_host_log.encode()).hexdigest(),
        "native_host_log_sha256": hashlib.sha256(native_host_log.encode()).hexdigest(),
        "raw_state_transitions_and_trace_candidates": transitions,
        "original_cpu_icpu_frame_not_proven_equal_to_native_host_pre_run_frame": True,
        "cpu_opcode_scope_not_proven_direct_store": True,
        "missing_helper_writer_not_proof_of_absent_write": True,
        "strict_guest_relative_result_boundary_equal": False,
        "release_complete_event_credit": 0,
        "interpretation": (
            "The real original CPU opcode scopes and native CPU helper store scopes "
            "are separately stamped and compared with exactly sampled raw guest "
            "state. Candidate matching values alone do not establish executing "
            "PC equivalence, NMI/beam-phase equivalence, or a gameplay fix."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("original-trace", "native-trace", "original-host-log", "native-host-log",
                 "original-dir", "native-dir", "out"):
        ap.add_argument("--" + name, required=True, type=Path)
    args = ap.parse_args()
    result = analyze(
        args.original_trace.read_text(encoding="utf-8"),
        args.native_trace.read_text(encoding="utf-8"),
        args.original_host_log.read_text(encoding="utf-8"),
        args.native_host_log.read_text(encoding="utf-8"),
        args.original_dir, args.native_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "raw_state_transitions_and_trace_candidates":
            result["raw_state_transitions_and_trace_candidates"],
        "release_complete_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
