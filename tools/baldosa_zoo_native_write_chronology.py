#!/usr/bin/env python3
"""QA-01: align native Baldosa menu/track guest write scopes with its own script ticks.

Uses the pinned framework's pre-existing SNESRECOMP_WLOG_ADDR logger; there
are no guest writes, controller rephases, or CPU instruction substitutions.
Trace scopes are not necessarily exact PCs for AOT compiled instructions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

# FRAME on the native logger is snes_frame_counter BEFORE host RtlRunFrame.
# The host script's zero-frame "dump" markers sample the just-completed
# execution. Preserve this distinction rather than assuming equal counters.
WRITER = re.compile(
    r"^f\s*(\d+)\s+([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})="
    r"([0-9A-Fa-f]{2,4})\s+w([12])\s+(.+)$"
)
DUMP = re.compile(r"script f=(\d+) dump boundary-(\d{5}) ok")
TARGETS = (0x009F, 0x00CE)
MAX_OBSERVATIONS = 100000
FIRST = 5152
LAST = 5164


def guest_byte(raw: bytes, offset: int) -> int:
    if len(raw) != 0x20000:
        raise ValueError("only full 128KiB guest WRAM snapshots are admissible")
    return raw[offset]


def parse_writes(log: str, *, entry_frame: int) -> tuple[list[dict], dict]:
    if entry_frame <= 0:
        raise ValueError("native scene-entry must be a positive independent host frame")
    relevant = []
    parsed = 0
    near = 0
    for line in log.splitlines():
        m = WRITER.fullmatch(line.strip())
        if not m:
            continue
        parsed += 1
        if parsed > MAX_OBSERVATIONS:
            raise ValueError("native source write log reached observation limit; may be truncated")
        frame, bank, addr, val, width, scope = m.groups()
        frame = int(frame)
        bank = int(bank, 16)
        address = int(addr, 16)
        width = int(width)
        value = int(val, 16)
        if not FIRST - 1 <= frame - entry_frame <= LAST + 1:
            continue
        near += 1
        for target in TARGETS:
            # The logger may record a 16-bit write starting one byte before
            # our watched 8-bit field. Preserve that write, not just stores
            # with a matching start address.
            if not (address <= target < address + width):
                continue
            if bank not in (0x00, 0x7E, 0x80) and not (
                address < 0x2000 and (bank <= 0x3F or 0x80 <= bank <= 0xBF)
            ):
                continue
            shift = (target - address) * 8
            relevant.append({
                "native_host_pre_run_frame": frame,
                "relative_to_native_scene_entry": frame - entry_frame,
                "guest_address": f"7E:{target:04X}",
                "guest_value": f"{(value >> shift) & 0xff:02X}",
                "write_width": width,
                "actual_store_start": f"{bank:02X}:{address:04X}",
                "native_scope": scope,
            })
    return relevant, {
        "native_log_total_matched_wrapped_writes": parsed,
        "native_log_near_boundary_wrapped_writes": near,
        "native_log_target_guest_writes": len(relevant),
    }


def analyze(native_log: str, native_host_log: str, native: Path, original: Path,
            *, native_scene_entry_frame: int) -> dict:
    writes, counts = parse_writes(native_log, entry_frame=native_scene_entry_frame)
    dumps = {}
    for m in DUMP.finditer(native_host_log):
        frame = int(m.group(1))
        relative = int(m.group(2))
        if FIRST <= relative <= LAST:
            dumps[relative] = frame
    if set(range(5155, 5159)) - set(dumps):
        raise ValueError("missing native exact boundary dump markers +5155..+5158")
    if any(dumps[k] != native_scene_entry_frame + k for k in range(5155, 5159)):
        raise ValueError("native dump script frames disagree with measured scene entry")
    original_state = {}
    native_state = {}
    for f in range(5155, 5159):
        a = (original / f"boundary-{f:05d}.wram.bin").read_bytes()
        b = (native / f"boundary-{f:05d}.wram.bin").read_bytes()
        original_state[f] = [guest_byte(a, off) for off in TARGETS]
        native_state[f] = [guest_byte(b, off) for off in TARGETS]
    expectation = {
        5155: ([0x84, 0], [0x84, 0]),
        5156: ([0x84, 0], [0x84, 0]),
        5157: ([0x84, 0], [0x16, 1]),
        5158: ([0x16, 1], [0x16, 1]),
    }
    for frame, (ref, got) in expectation.items():
        if original_state[frame] != ref or native_state[frame] != got:
            raise ValueError(f"original/native menu transition snapshot changed at +{frame}")
    # Do not force writes to be trace-visible: a direct memcpy/DMA may bypass
    # the framework's CPU helper. That negative outcome is a diagnostic to
    # investigate, never permission to infer a guessed owning instruction.
    transition_candidates = [
        w for w in writes
        if (w["guest_address"], w["guest_value"]) in
        (("7E:009F", "16"), ("7E:00CE", "01"))
    ]
    return {
        "schema": "UR-QA01-ZOO-NATIVE-MENU-WRITE-CHRONOLOGY/1",
        "source": "pinned native Baldosa SNESRECOMP_WLOG_ADDR CPU writer helper; original pinned Snes9x independent fixed dumps",
        "native_scene_entry_host_frame": native_scene_entry_frame,
        "source_logger_range_hex": "008B:00CE",
        "logger_wrap_or_untracked_writes_possible": True,
        "frame_semantics": "Native logger f is pre-RtlRunFrame snes_frame_counter; script f dump is a zero-frame pre-run command that samples the preceding completed execution. CPU/NMI/VBlank internal scheduling is NOT measured.",
        "original_named_states_5155_to_5158": {str(k):v for k,v in original_state.items()},
        "native_named_states_5155_to_5158": {str(k):v for k,v in native_state.items()},
        "native_script_dump_host_frames": {str(k):v for k,v in dumps.items()},
        "native_log_sha256": hashlib.sha256(native_log.encode()).hexdigest(),
        "counts": counts,
        "native_menu_and_track_value_writes_near_boundary": transition_candidates,
        "native_boundary_cpu_store_trace_status": (
            "partial_candidate_writers" if transition_candidates else "no_target_cpu_helper_write_observed"
        ),
        "causality_claim": "none: no per-instruction native PC/NMI timeline, no claimed gameplay defect",
        "complete_event_qa_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--native-writes", type=Path, required=True)
    ap.add_argument("--native-host-log", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--native-scene-entry", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = analyze(args.native_writes.read_text(encoding="utf-8"),
                   args.native_host_log.read_text(encoding="utf-8"),
                   args.native, args.original,
                   native_scene_entry_frame=args.native_scene_entry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: data[k] for k in (
        "counts", "native_boundary_cpu_store_trace_status",
        "native_menu_and_track_value_writes_near_boundary",
        "complete_event_qa_credit")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
