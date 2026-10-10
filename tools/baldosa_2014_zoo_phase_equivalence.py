#!/usr/bin/env python3
"""QA-01: compare independent Zoo guest memory dumps at adjacent fixed frames.

A source WRAM/VRAM/CGRAM match across frames is an observed scheduling phase,
NOT a license to shift controllers, patch game rules or admit a course.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MEMORY = {"wram.bin": 0x20000, "vram.bin": 0x10000, "cgram.bin": 0x200}
WINDOW = tuple(range(5154, 5164))


def read_memory(folder: Path, frame: int, suffix: str) -> bytes:
    path = folder / f"boundary-{frame:05d}.{suffix}"
    raw = path.read_bytes()
    if len(raw) != MEMORY[suffix]:
        raise ValueError(f"{path}: expected {MEMORY[suffix]} bytes, got {len(raw)}")
    return raw


def compare_memory(original: Path, native: Path, original_frame: int,
                   native_frame: int) -> dict:
    groups = {}
    for suffix, count in MEMORY.items():
        a = read_memory(original, original_frame, suffix)
        b = read_memory(native, native_frame, suffix)
        differing = sum(x != y for x, y in zip(a, b))
        groups[suffix.removesuffix(".bin")] = {
            "bytes_compared": count,
            "differing_bytes": differing,
            "exact": differing == 0,
            "original_sha256": hashlib.sha256(a).hexdigest(),
            "native_sha256": hashlib.sha256(b).hexdigest(),
        }
    return {
        "original_frame": original_frame,
        "native_frame": native_frame,
        "all_guest_memory_exact": all(g["exact"] for g in groups.values()),
        "groups": groups,
    }


def analyze(original: Path, native: Path, boundary: dict,
            frames: tuple[int, ...] = WINDOW) -> dict:
    if boundary.get("schema") != "UR-QA01-ORIGINAL-BALDOSA-ZOO-FIXED-BOUNDARY/1":
        raise ValueError("requires the independent fixed-boundary guest report")
    if boundary.get("complete_event_qa_credit") != 0:
        raise ValueError("diagnostic must not consume or confer event admission")
    onset = boundary.get("first_fixed_frame_result_menu")
    if onset != {"original": 5163, "native": 5162}:
        raise ValueError(f"unexpected pinned Zoo result onset: {onset}")
    if not frames or len(set(frames)) != len(frames) or sorted(frames) != list(frames):
        raise ValueError("frame window must be ordered and distinct")
    rows = {}
    for frame in frames:
        rows[str(frame)] = {
            "same_fixed_frame": compare_memory(original, native, frame, frame),
            "reference_next_frame": compare_memory(original, native, frame + 1, frame),
        }
    return {
        "schema": "UR-QA01-ZOO-ADJACENT-GUEST-MEMORY/1",
        "source": "pinned source-original 2014 movie / separate original Snes9x and native Baldosa fixed-frame dump artifacts",
        "relative_frames": list(frames),
        "original_native_result_onset": onset,
        "first_exact_next_reference_frame": next(
            (f for f in frames if rows[str(f)]["reference_next_frame"]["all_guest_memory_exact"]),
            None),
        "exact_source_wram_at_5155": (
            rows.get("5155", {}).get("same_fixed_frame", {}).get("groups", {})
            .get("wram", {}).get("exact", False)),
        "exact_full_guest_memory_native_5156_original_5157": (
            rows.get("5156", {}).get("reference_next_frame", {})
            .get("all_guest_memory_exact", False)),
        "comparisons": rows,
        "limitations": ("Full 128-KiB WRAM + 64-KiB VRAM + 512-byte CGRAM equality "
                        "does not prove CPU register/PC, PPU internal scanline, audio, "
                        "host scheduling or game-rule equivalence. Adjacent-frame "
                        "matches are evidence about phase, not a fix or acceptance."),
        "complete_event_qa_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--boundary-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.original, args.native,
                     json.loads(args.boundary_report.read_text(encoding="utf-8")))
    if not result["exact_source_wram_at_5155"]:
        raise ValueError("pinned original/native no longer share full WRAM at +5155")
    if not result["exact_full_guest_memory_native_5156_original_5157"]:
        raise ValueError("pinned +5156 native / +5157 original full guest memory witness changed")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "first_exact_next_reference_frame", "exact_source_wram_at_5155",
        "exact_full_guest_memory_native_5156_original_5157",
        "complete_event_qa_credit")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
