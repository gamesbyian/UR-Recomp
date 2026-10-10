#!/usr/bin/env python3
"""Authentic P1 slot97 source OBJ alpha from existing 4x native 1P guest run.

The native PPU exports a single OAM slot BEFORE BG/window final priority,
with RemoveFromGame OFF. Compare its true alpha plane against independently
executed same-frame 1x source and 4x Original logical colour, never treat an
opaque OBJ source pixel as automatically final-visible or safe to erase.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_density_parity import (
        capture_files, LOGICAL_WIDTH, LOGICAL_HEIGHT,
    )
    from tools.baldosa_ws24_presentation_report import restore_logical_nearest
    from tools.check_baldosa_wide_single_slot_source import (
        assess as assess_source, read_source, HEADER,
    )
except ModuleNotFoundError:
    from check_baldosa_wide_density_parity import (
        capture_files, LOGICAL_WIDTH, LOGICAL_HEIGHT,
    )
    from baldosa_ws24_presentation_report import restore_logical_nearest
    from check_baldosa_wide_single_slot_source import (
        assess as assess_source, read_source, HEADER,
    )


def alpha_vs_final(original: bytes, isolated: bytes) -> dict:
    expected = LOGICAL_WIDTH * LOGICAL_HEIGHT * 4
    if len(original) != expected or len(isolated) != expected:
        raise ValueError("real PPU isolated source/final-raster dimensions differ")
    opaque = same_rgb = different_rgb = transparent = 0
    for i in range(0, expected, 4):
        if isolated[i + 3] == 0:
            transparent += 1
            continue
        opaque += 1
        if isolated[i:i+3] == original[i:i+3]:
            same_rgb += 1
        else:
            different_rgb += 1
    return {
        "source_opaque_pixels": opaque,
        "source_opaque_rgb_matches_final_raster": same_rgb,
        "source_opaque_rgb_differs_from_final_raster": different_rgb,
        "source_alpha_empty_pixels": transparent,
        "final_owner_or_priority_proven": False,
    }


def assess(stock_crc: Path, four_crc: Path, original_dir: Path,
           density4_dir: Path, isolated_pam: Path, log_file: Path,
           guest_frame: int = 2208, slot: int = 97) -> dict:
    if guest_frame != 2208 or slot != 97:
        raise ValueError("only the authenticated real 1P 0895 source frame/slot is in scope")
    original, dense = stock_crc.read_bytes().splitlines(), four_crc.read_bytes().splitlines()
    if len(original) != 5447 or original != dense:
        raise ValueError("native 1P 4x route is not source-identical across all guest CRCs")
    one = capture_files(original_dir, 1)
    four = capture_files(density4_dir, 4)
    if set(one) != set(four) or len(one) != 7 or guest_frame not in one:
        raise ValueError("one-to-one seven real source/dense guest image frames not present")
    recovered = {}
    for frame, physical in four.items():
        pixels, exact_nearest = restore_logical_nearest(
            physical, LOGICAL_WIDTH, LOGICAL_HEIGHT, 4)
        if not exact_nearest:
            raise ValueError(f"native 4x Original contains non-nearest source pixels at {frame}")
        recovered[frame] = pixels
    source = read_source(isolated_pam, slot)
    if source["guest_frame"] != guest_frame:
        raise ValueError("isolated source OAM raster belongs to wrong guest frame")
    text = log_file.read_text(encoding="utf-8", errors="replace")
    proof = assess_source(one, recovered, source, text, min_shared_frames=7)
    if proof["status"] != "passed" or proof["identical_complete_original_342_rasters"] != 7:
        raise ValueError("single-slot native source provenance does not preserve all Original pixels")
    raw = isolated_pam.read_bytes()
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + LOGICAL_WIDTH * LOGICAL_HEIGHT * 4:
        raise ValueError("source OBJ source file lost native PPU provenance")
    pixels = raw[len(HEADER):]
    mapping = alpha_vs_final(one[guest_frame], pixels)
    if mapping["source_opaque_pixels"] != (
        source["top_opaque_source_pixels"] + source["bottom_opaque_source_pixels"]
    ):
        raise ValueError("source PPU slot opaque count differs from raw isolated source raster")
    return {
        "schema_version": 1,
        "status": "native-1p-source-obj-slot97-frame2208-verified",
        "native_guest_crcs_identical": len(original),
        "guest_frame": guest_frame,
        "source_semantic_frame_id": "0895",
        "isolated_original_ppu_obj_slot": slot,
        "no_remove_from_game": True,
        "independent_one_x_four_x_source_image_pairs": 7,
        "original_logical_raster": [LOGICAL_WIDTH, LOGICAL_HEIGHT],
        "native_density4_raster": [LOGICAL_WIDTH * 4, LOGICAL_HEIGHT * 4],
        "source_obj_alpha": source,
        "isolated_source_rgba_sha256": hashlib.sha256(pixels).hexdigest(),
        "stock_original_at_frame_sha256": hashlib.sha256(one[guest_frame]).hexdigest(),
        "alpha_vs_final_observations": mapping,
        "authored_hd_asset_approved": False,
        "actual_bg_window_final_winner_proven": False,
        "widescreen_hd_replacement_admitted": False,
        "limits": (
            "Actual single-OAM-slot P1 source emission before original BG/window "
            "composition, not proof of unoccluded final PPU ownership, complete "
            "art family, 4x authored reconstruction, 2P source priority or beta."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--candidate-crc", required=True, type=Path)
    p.add_argument("--one-x", required=True, type=Path)
    p.add_argument("--four-x", required=True, type=Path)
    p.add_argument("--source-file", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    r = assess(a.baseline_crc, a.candidate_crc, a.one_x, a.four_x,
               a.source_file, a.log)
    a.out.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_1P_SOURCE_0895 "
          f"status={r['status']} "
          f"opaque={r['source_obj_alpha']['top_opaque_source_pixels'] + r['source_obj_alpha']['bottom_opaque_source_pixels']} "
          "final_bg_priority_proven=0 wide_hd_admitted=0")


if __name__ == "__main__":
    main()
