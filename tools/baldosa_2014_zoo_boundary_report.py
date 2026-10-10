#!/usr/bin/env python3
"""QA-only fixed-frame original/Baldosa Zoo result boundary discriminator.

Uses existing movie, guest dumps, decoded PPU text and semantic field oracle.
No menu polling, controller rebase interventions, guest writes or admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import baldosa_2014_zoo_scene_report as old
import baldosa_2014_zoo_scene_route as scene
from extract_menu_visual_language import Dump
from probe_tier_opponents import screen_texts


def logged_boundary_frames(log: str) -> dict:
    """Verify that both hosts actually sampled each requested scene offset."""
    def frames(label: str) -> list[int]:
        matches = []
        for line in log.splitlines():
            if f" dump {label} " in line:
                if "script f=" not in line:
                    raise ValueError(f"boundary dump {label} has no host frame")
                matches.append(int(line.split("script f=", 1)[1].split()[0]))
        return matches
    start = frames("scene-entered")
    if len(start) != 1:
        raise ValueError("independent guest scene entry must appear exactly once")
    entry = start[0]
    for frame in scene.BOUNDARY_FRAMES:
        label = f"boundary-{frame:05d}"
        actual = frames(label)
        if len(actual) != 1 or actual[0] != entry + frame:
            raise ValueError(f"wrong or absent {label}: {actual}; scene-entry {entry}")
    return {"guest_scene_entry": entry,
            "first_sampled_absolute": entry + scene.BOUNDARY_FRAMES[0],
            "last_sampled_absolute": entry + scene.BOUNDARY_FRAMES[-1]}


def analyze(original_dir: Path, native_dir: Path, original_log: str,
            native_log: str) -> dict:
    timing = {"original": logged_boundary_frames(original_log),
              "native": logged_boundary_frames(native_log)}
    observations = {}
    different = []
    phase_scratch_differences = []
    for frame in scene.BOUNDARY_FRAMES:
        label = f"boundary-{frame:05d}"
        files = (original_dir / f"{label}.wram.bin",
                 native_dir / f"{label}.wram.bin")
        rows = (old.snapshot(files[0]), old.snapshot(files[1]))
        if any(row["track_id"] != 1 for row in rows):
            raise ValueError(f"wrong active USA Zoom Zoo track at {label}")
        for key in rows[0]:
            if rows[0][key] != rows[1][key]:
                different.append({"relative_frame": frame, "field": key,
                                  "original": rows[0][key],
                                  "baldosa": rows[1][key]})
        original = files[0].read_bytes()
        native = files[1].read_bytes()
        # These are diagnostic transient DP bytes, NOT authoritative event
        # counters. Compare their phase WITHOUT hiding gameplay differences.
        scratch = {
            "original": {"dp_c6": original[0x00C6],
                         "dp_c8": original[0x00C8]},
            "native": {"dp_c6": native[0x00C6],
                       "dp_c8": native[0x00C8]},
        }
        if scratch["original"] != scratch["native"]:
            phase_scratch_differences.append({
                "relative_frame": frame, **scratch})
        p2_progression = {
            label: {"laps": int.from_bytes(w[0x0EF3:0x0EF5], "little"),
                    "checkpoint": int.from_bytes(w[0x119B:0x119D], "little"),
                    "finish_gate": int.from_bytes(w[0x119F:0x11A1], "little")}
            for label, w in (("original", original), ("native", native))
        }
        observations[str(frame)] = {
            "original": rows[0], "native": rows[1],
            "raw_phase_scratch": scratch,
            "p2_progression": p2_progression,
            "whole_wram_differing_bytes":
                sum(a != b for a, b in zip(original, native)),
            "original_wram_sha256": hashlib.sha256(original).hexdigest(),
            "native_wram_sha256": hashlib.sha256(native).hexdigest(),
        }
    def onset(side: str) -> int | None:
        return next((frame for frame in scene.BOUNDARY_FRAMES
                     if observations[str(frame)][side]["menu"] == 0xBC and
                     observations[str(frame)][side]["race_flag"] != 1), None)
    first_result = {"original": onset("original"), "native": onset("native")}
    labels = {}
    final = scene.BOUNDARY_FRAMES[-1]
    for side, directory in (("original", original_dir), ("native", native_dir)):
        labels[side] = screen_texts(Dump(directory, f"boundary-{final:05d}"))
    cleared = [
        frame for frame in scene.BOUNDARY_FRAMES
        if observations[str(frame)]["original"]["p1_stored_contact"] == 0
        and observations[str(frame)]["native"]["p1_stored_contact"] == 0
    ]
    return {
        "schema": "UR-QA01-ORIGINAL-BALDOSA-ZOO-FIXED-BOUNDARY/1",
        "source": "identical pinned original 2014 movie and independently measured active Zoo entry",
        "scene_relative_frame_range": [scene.BOUNDARY_FRAMES[0],
                                       scene.BOUNDARY_FRAMES[-1]],
        "host_frame_logs_validated": timing,
        "first_fixed_frame_result_menu": first_result,
        "same_fixed_frame_result_onset": (
            first_result["original"] is not None and
            first_result["original"] == first_result["native"]),
        "first_named_field_disagreement": different[0] if different else None,
        "first_transient_dp_phase_disagreement": (
            phase_scratch_differences[0] if phase_scratch_differences else None),
        "transient_dp_phase_disagreements": phase_scratch_differences,
        "all_named_field_differences": different,
        "p1_contact_cleared_in_both_at_frames": cleared,
        "final_result_ppu_text": labels,
        "final_ppu_equal": labels["original"] == labels["native"],
        "observations": observations,
        "complete_event_qa_credit": 0,
        "interpretation_guardrail": (
            "Matching fixed-frame result-menu onset would implicate host until "
            "polling semantics. Differing onset requires guest/update phase "
            "localization before calling it an execution defect. No automatic "
            "course admission or gameplay workarounds."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--original-log", type=Path, required=True)
    parser.add_argument("--native-log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.original, args.native,
                     args.original_log.read_text(),
                     args.native_log.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "first_fixed_frame_result_menu", "same_fixed_frame_result_onset",
        "first_named_field_disagreement",
        "first_transient_dp_phase_disagreement", "final_ppu_equal",
        "complete_event_qa_credit")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
