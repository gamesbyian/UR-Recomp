#!/usr/bin/env python3
"""Attribute real 1P frame 2208 PPU bottom OBJ source across slots96 and97.

Use two ALREADY existing independently rendered native guest processes at
original density1 and density4, with each process observing exactly one
non-destructive PPU OBJ source slot. Pair both to the other process's exact
full Original logical source. Per-slot OBJ emissions are pre-BG priority
and must NEVER be presented as final source-screen pixel ownership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_density_parity import (
        capture_files, assess as parity, LOGICAL_WIDTH, LOGICAL_HEIGHT,
    )
    from tools.baldosa_ws24_presentation_report import restore_logical_nearest
    from tools.check_baldosa_wide_single_slot_source import (
        read_source, assess as assess_source, HEADER,
    )
except ModuleNotFoundError:
    from check_baldosa_wide_density_parity import (
        capture_files, assess as parity, LOGICAL_WIDTH, LOGICAL_HEIGHT,
    )
    from baldosa_ws24_presentation_report import restore_logical_nearest
    from check_baldosa_wide_single_slot_source import (
        read_source, assess as assess_source, HEADER,
    )


def observed_rgb(original: bytes, isolated: bytes) -> dict:
    n = LOGICAL_WIDTH * LOGICAL_HEIGHT * 4
    if len(original) != n or len(isolated) != n:
        raise ValueError("native full PPU/OBJ source dimensions disagree")
    alpha = same = different = 0
    for i in range(0, n, 4):
        if isolated[i+3] == 0:
            continue
        alpha += 1
        if original[i:i+3] == isolated[i:i+3]:
            same += 1
        else:
            different += 1
    return {
        "isolated_source_opaque": alpha,
        "source_rgb_equal_final_original": same,
        "source_rgb_different_final_original": different,
        "final_ppu_owner_proven": False,
    }


def assess(stock_crc: Path, original_1x_crc: Path, original_4x_crc: Path,
           source_1x_dir: Path, source_4x_dir: Path,
           source96: Path, source97: Path, log96: Path, log97: Path,
           frame: int = 2208) -> dict:
    if frame != 2208:
        raise ValueError("only guest2208 authentic 1P 0895 is in scope")
    base, one, four = (p.read_bytes().splitlines()
                       for p in (stock_crc, original_1x_crc, original_4x_crc))
    if len(base) != 5447 or base != one or base != four:
        raise ValueError("independent three-way native P1 original guest CRC mismatch")
    first = capture_files(source_1x_dir, 1)
    density = capture_files(source_4x_dir, 4)
    if set(first) != set(density) or len(first) != 7 or frame not in first:
        raise ValueError("real native Original 1x/4x source guest-frame identity incomplete")
    p = parity(first, density, 7)
    if p["status"] != "passed" or p["exact_image_pairs"] != 7:
        raise ValueError("whole native 1P logical source/density mismatch")
    recovered = {}
    for guest, image in density.items():
        logical, exact = restore_logical_nearest(
            image, LOGICAL_WIDTH, LOGICAL_HEIGHT, 4)
        if not exact or logical != first[guest]:
            raise ValueError("independent 4x source contains changed/padded original pixels")
        recovered[guest] = logical
    records = []
    for slot, path, log in (
        (96, source96, log96),
        (97, source97, log97),
    ):
        meta = read_source(path, slot)
        if meta["guest_frame"] != frame:
            raise ValueError("source OBJ slot belongs to wrong native guest frame")
        native_log = log.read_text(encoding="utf-8", errors="replace")
        oracle = assess_source(first, recovered, meta, native_log, 7)
        if oracle["status"] != "passed" or oracle["identical_complete_original_342_rasters"] != 7:
            raise ValueError("native isolated source OBJ changed genuine final Original")
        data = path.read_bytes()
        if not data.startswith(HEADER) or (
            len(data) != len(HEADER) + LOGICAL_WIDTH * LOGICAL_HEIGHT * 4
        ):
            raise ValueError("native isolated source PPU plane corrupted")
        rgba = data[len(HEADER):]
        colors = observed_rgb(first[frame], rgba)
        if colors["isolated_source_opaque"] != (
            meta["top_opaque_source_pixels"] + meta["bottom_opaque_source_pixels"]
        ):
            raise ValueError("native source alpha report differs from actual RGBA")
        records.append({
            "original_oam_slot": slot,
            "native_source": meta,
            "rgba_sha256": hashlib.sha256(rgba).hexdigest(),
            "rgb_vs_final_observation": colors,
            "original_1x_and_4x_remained_pixel_identical": True,
        })
    return {
        "schema_version": 1,
        "status": "native-1p-paired-bottom-oam-source-truth",
        "native_guest_frame": frame,
        "source_p1_semantic": "0895",
        "native_original_guest_crc_identical": 5447,
        "native_1x_and_4x_source_frames_identical": 7,
        "original_bottom_slot96_and_slot97_sources": records,
        "no_sprite_removal_or_guest_mutation": True,
        "source_slot_emission_accepted": True,
        "individual_final_bg_or_obj_priority_accepted": False,
        "authored_hd_or_wide_replacement_accepted": False,
        "windows_beta_accepted": False,
        "limits": (
            "Two read-only original PPU per-slot source planes from independent "
            "native Original executions; pre-final-BG/window, source-alpha "
            "alone cannot authorize original sprite removal, HD art or "
            "completed-gameplay/Windows release."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for opt in ("stock-crc", "one-crc", "four-crc", "one-dir",
                "four-dir", "source96", "source97", "log96", "log97", "out"):
        p.add_argument("--" + opt, type=Path, required=True)
    a = p.parse_args()
    report = assess(a.stock_crc, a.one_crc, a.four_crc,
                    a.one_dir, a.four_dir, a.source96, a.source97,
                    a.log96, a.log97)
    a.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("UR_BALDOSA_1P_BOTTOM_SOURCE_96_97 "
          f"status={report['status']} "
          f"slot96={report['original_bottom_slot96_and_slot97_sources'][0]['rgb_vs_final_observation']['isolated_source_opaque']} "
          f"slot97={report['original_bottom_slot96_and_slot97_sources'][1]['rgb_vs_final_observation']['isolated_source_opaque']} "
          "BGpriority_proven=0 HDadmitted=0")


if __name__ == "__main__":
    main()
