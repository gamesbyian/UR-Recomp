#!/usr/bin/env python3
"""Rebase unchanged original movie controller runs to two *observed* guest
scene-entry frame numbers. Reuses the project's historical SMV parser.

A 340-command `press` conversion added 340 unwanted release frames. These
absolute-frame input files reproduce every source-held and idle frame instead.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

import baldosa_2014_zoo_scene_route as scene
import extract_historical_smv_scene_window as movie


def guest_scene_entry(log: str) -> int:
    frames = re.findall(r"(?m)^script f=(\d+) dump scene-entered\b", log)
    if len(frames) != 1:
        raise ValueError(f"expected one genuine scene-entry dump, found {len(frames)}")
    return int(frames[0])


def native_input_origin(entry: int, phase: int) -> int:
    """Bounded host-latch discriminator: shift original movie masks, not guest rules."""
    if type(entry) is not int or type(phase) is not int or phase not in (-1, 0, 1):
        raise ValueError("only explicit native -1, 0 or +1 guest input frame phases")
    if entry + phase < 0:
        raise ValueError("negative guest input origin")
    return entry + phase


def generate(meta: Path, original_log: Path, native_log: Path,
             original_out: Path, native_out: Path, report_path: Path,
             source_report: Path, *, native_phase: int = 0) -> dict:
    original_entry = guest_scene_entry(original_log.read_text(encoding="utf-8"))
    native_entry = guest_scene_entry(native_log.read_text(encoding="utf-8"))
    native_origin = native_input_origin(native_entry, native_phase)
    provenance = json.loads(source_report.read_text(encoding="utf-8"))
    window = scene.verified_window(meta)
    if (provenance["raw_original_input_sha256"] != window["raw_controller_window_sha256"]
            or not provenance["requires_direct_frame_inputs"]):
        raise ValueError("source movie fingerprint or direct-input policy changed")
    for path, entry in ((original_out, original_entry),
                        (native_out, native_origin)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(movie.shifted_input_file(window, entry), encoding="utf-8")
    result = {
        "schema_version": 1,
        "original_guest_scene_entry_frame": original_entry,
        "baldosa_guest_scene_entry_frame": native_entry,
        "baldosa_guest_input_origin": native_origin,
        "native_controller_latch_phase_intervention": native_phase,
        "native_phase_is_experiment_not_admission": native_phase != 0,
        "original_minus_baldosa_entry_frames": original_entry - native_entry,
        "original_frame_input_sha256": hashlib.sha256(original_out.read_bytes()).hexdigest(),
        "baldosa_frame_input_sha256": hashlib.sha256(native_out.read_bytes()).hexdigest(),
        "source_movie_window_sha256": window["raw_controller_window_sha256"],
        "source_input_segment_count": len(window["relative_input_segments"]),
        "controller_frames": window["frames"],
        "unaltered_joypad_bits": True,
        "press_inserted_release_frames": 0,
        "original_native_terminal_result_qa_credit": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", type=Path, default=movie.METADATA)
    ap.add_argument("--source-report", type=Path, required=True)
    ap.add_argument("--original-log", type=Path, required=True)
    ap.add_argument("--native-log", type=Path, required=True)
    ap.add_argument("--out-original", type=Path, required=True)
    ap.add_argument("--out-native", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--native-phase", type=int, choices=(-1, 0, 1), default=0)
    args = ap.parse_args()
    print(json.dumps(generate(args.meta, args.original_log, args.native_log,
                              args.out_original, args.out_native, args.report,
                              args.source_report, native_phase=args.native_phase)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
