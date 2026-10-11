#!/usr/bin/env python3
"""QA-08 exact split OAM source reuse in authentic multi-frame 2P PPU.

Require source PPU slot96..99 RGBA from independent original guest processes
and their validated source-vs-Original reports at three distinct moving frames.
Observe that 98 and97, and 99 and96, are the same emitted original RGBA
translated by exactly 113 logical Y pixels. This is an independent source
visibility/reconstruction *invariant*, not authorization to erase sprites,
replace art or infer final BG/window compositing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_single_slot_source import (
        read_source, HEADER, WIDTH, HEIGHT,
    )
except ModuleNotFoundError:
    from check_baldosa_wide_single_slot_source import (
        read_source, HEADER, WIDTH, HEIGHT,
    )

FRAMES = (1856, 1872, 1888)
SLOTS = (96, 97, 98, 99)
PAIRS = ((98, 97), (99, 96))
SOURCE_FRAMES = (1808, 1824, 1840, 1856, 1872, 1888)
VERTICAL_DELTA = 113


def validated_source(root: Path, slot: int, frame: int) -> tuple[dict, bytes, dict]:
    report_name = (f"ws342_obj_slot_{slot}.json" if frame == FRAMES[0] else
                   f"ws342_obj_slot_{slot}_frame{frame}.json")
    path = root / "baldosa-ws342-obj-slots" / (
        f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
    report_path = root / "baldosa-evidence" / report_name
    raw = path.read_bytes()
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + WIDTH * HEIGHT * 4:
        raise ValueError(f"invalid full original PPU RGBA source {slot} at {frame}")
    read = read_source(path, slot)
    if read["guest_frame"] != frame or not read["source_nonempty"]:
        raise ValueError(f"missing authentic positive original source slot {slot}/{frame}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (report.get("schema_version") != 1 or
            report.get("status") != "passed" or
            report.get("source_log_matches_pam") is not True or
            report.get("identical_complete_original_342_rasters") != 6 or
            report.get("differing_original_rasters") != [] or
            report.get("shared_full_frame_guest_ids") != list(SOURCE_FRAMES) or
            report.get("minimum_shared_frames") != 4 or
            report.get("source") != read or
            report.get("guest_crc_comparison") !=
                "Externally enforced byte-exact in native workflow"):
        raise ValueError(f"slot {slot}/{frame}: original PPU/source/report validation failed")
    digest = report.get("source_frame_main_raster_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"slot {slot}/{frame}: no independent main Original digest")
    try:
        bytes.fromhex(digest)
    except ValueError as exc:
        raise ValueError("nonhex main Original digest") from exc
    return read, raw[len(HEADER):], report


def check_pair(top: bytes, bottom: bytes, top_slot: int, bottom_slot: int,
               frame: int, top_meta: dict, bottom_meta: dict) -> dict:
    if (top_slot, bottom_slot) not in PAIRS or frame not in FRAMES:
        raise ValueError("only authenticated split-slot pairs and observed frames")
    n = WIDTH * HEIGHT * 4
    if len(top) != n or len(bottom) != n:
        raise ValueError("source planes must be real 342x224 RGBA")
    top_emitted = bottom_emitted = identical = moved_conflicts = 0
    samples = []
    # Check both directions, including otherwise invisible source pixels.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 4
            rgba = top[idx:idx + 4]
            if rgba[3]:
                top_emitted += 1
                target_y = y + VERTICAL_DELTA
                if target_y >= HEIGHT:
                    moved_conflicts += 1
                else:
                    other = bottom[(target_y * WIDTH + x) * 4:
                                   (target_y * WIDTH + x) * 4 + 4]
                    if rgba != other:
                        moved_conflicts += 1
                        if len(samples) < 8:
                            samples.append([x, y, target_y])
                    else:
                        identical += 1
            other_rgba = bottom[idx:idx + 4]
            if other_rgba[3]:
                bottom_emitted += 1
                source_y = y - VERTICAL_DELTA
                if source_y < 0 or (
                    top[(source_y * WIDTH + x) * 4:
                        (source_y * WIDTH + x) * 4 + 4] != other_rgba
                ):
                    moved_conflicts += 1
                    if len(samples) < 8:
                        samples.append([x, source_y, y])
    expected_top = (top_meta["top_opaque_source_pixels"] +
                    top_meta["bottom_opaque_source_pixels"])
    expected_bottom = (bottom_meta["top_opaque_source_pixels"] +
                       bottom_meta["bottom_opaque_source_pixels"])
    if (top_emitted != expected_top or bottom_emitted != expected_bottom or
            expected_top == 0 or expected_bottom == 0):
        raise ValueError("PPU source alpha counts cannot be reconciled")
    if top_meta["bottom_opaque_source_pixels"] or bottom_meta["top_opaque_source_pixels"]:
        raise ValueError("original 2P split capture has unexpected raster-band source")
    if moved_conflicts or identical != top_emitted or top_emitted != bottom_emitted:
        raise ValueError(
            f"original PPU split pair {top_slot}/{bottom_slot} frame{frame} "
            f"is not exact RGBA under dy=113; conflicts={moved_conflicts}"
        )
    top_box = top_meta["bbox"]
    bottom_box = bottom_meta["bbox"]
    if ([top_box[0], top_box[1] + VERTICAL_DELTA,
         top_box[2], top_box[3] + VERTICAL_DELTA] != bottom_box):
        raise ValueError("original split pair RGBA passed but bounds do not translate")
    return {
        "top_slot": top_slot,
        "bottom_slot": bottom_slot,
        "source_opaque_rgba_pixels_in_each_view": identical,
        "source_bboxes_top_bottom": [top_box, bottom_box],
        "bottom_minus_top_y_logical_pixels": VERTICAL_DELTA,
        "differing_source_rgba_under_exact_translation": 0,
        "byte_exact_all_four_rgba_channels": True,
        "source_final_ppu_owner_proven": False,
    }


def assess(root: Path) -> dict:
    frames = {}
    source_sha = {}
    for frame in FRAMES:
        slots = {}
        planes = {}
        frame_digest = set()
        for slot in SLOTS:
            info, pixels, report = validated_source(root, slot, frame)
            slots[slot] = info
            planes[slot] = pixels
            frame_digest.add(report["source_frame_main_raster_sha256"])
            source_sha[f"{frame}:{slot}"] = info["source_sha256"]
        if len(frame_digest) != 1:
            raise ValueError(f"four independent slot probes disagree on frame{frame} Original")
        if len(planes) != 4:
            raise ValueError("incomplete original 2P slot capture")
        pairs = [check_pair(planes[top], planes[bottom], top, bottom,
                            frame, slots[top], slots[bottom])
                 for top, bottom in PAIRS]
        if pairs[0]["source_opaque_rgba_pixels_in_each_view"] == (
            pairs[1]["source_opaque_rgba_pixels_in_each_view"]
        ) and slots[98]["bbox"] == slots[99]["bbox"]:
            # Two players may share an animation; do not claim unequal
            # anatomy merely because this happened to be a different slot.
            pass
        frames[str(frame)] = {
            "source_main_original_ppu_sha256": next(iter(frame_digest)),
            "pairs": pairs,
            "exact_duplicate_rgba_pair_count": len(pairs),
            "distinct_original_source_export_count": 4,
        }
    return {
        "schema_version": 1,
        "status": "original-2p-six-exact-rgba-slot-aliases",
        "original_guest_frames": list(FRAMES),
        "validated_independent_original_source_exports": len(FRAMES) * len(SLOTS),
        "exact_split_duplicate_pairs": len(FRAMES) * len(PAIRS),
        "translation_x_pixels": 0,
        "translation_y_pixels": VERTICAL_DELTA,
        "original_ppu_source_sha256_by_frame_slot": source_sha,
        "frame_observations": frames,
        "guest_crc_parity": "native workflow originally enforced for each source run",
        "original_center_and_world_acceptance_unchanged": True,
        "release_or_remastered_admission": False,
        "limitations": (
            "Read-only original isolated per-slot PPU emission in three exact "
            "2P moving frames. Same RGBA at a translated source coordinate "
            "does not certify native final composite priority, real hardware "
            "outside these frames, guest event correctness, 4K, independent "
            "rider identity or safe host replacement."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-artifact-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = assess(args.native_artifact_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("UR_QA08_ORIGINAL_2P_SPLIT_RGBA exact_pairs=" +
          str(report["exact_split_duplicate_pairs"]) +
          " frames=" + str(report["original_guest_frames"]) +
          " translation_y=" + str(report["translation_y_pixels"]) +
          " HDadmitted=0")


if __name__ == "__main__":
    main()
