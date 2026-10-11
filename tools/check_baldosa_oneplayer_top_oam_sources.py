#!/usr/bin/env python3
"""Attribute real 1P frame 2208 PPU top OBJ source across slots98 and99.

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




def classify_top_source_pair(original: bytes, slot98: bytes, slot99: bytes) -> dict:
    """Bound ambiguity of two *emitted* OBJ planes versus finished Original.

    This is a read-only spatial census. Even exact RGB equality is not a
    PPU winner/priority proof; only a separately verified removal
    counterfactual could begin to establish that.
    """
    n = LOGICAL_WIDTH * LOGICAL_HEIGHT * 4
    if any(len(plane) != n for plane in (original, slot98, slot99)):
        raise ValueError("paired OBJ and original RGBA dimensions disagree")
    fields = (
        "slot98_only", "slot99_only", "shared", "neither",
        "exclusive98_rgb_differs_final", "exclusive99_rgb_differs_final",
        "shared_source_rgb_conflict", "shared_final_matches_98_only",
        "shared_final_matches_99_only", "shared_final_matches_both",
        "shared_final_matches_neither",
    )
    bands = {band: {field: 0 for field in fields}
             for band in ("top", "bottom")}
    examples = {"conflicting_shared": [], "shared_matches_neither": [],
                "exclusive_rgb_differs_final": []}
    for offset in range(0, n, 4):
        pixel = offset // 4
        y, x = divmod(pixel, LOGICAL_WIDTH)
        row = bands["top" if y < 112 else "bottom"]
        a = slot98[offset + 3] != 0
        b = slot99[offset + 3] != 0
        if not a and not b:
            row["neither"] += 1
            continue
        final_rgb = original[offset:offset + 3]
        if a and b:
            row["shared"] += 1
            rgb98 = slot98[offset:offset + 3]
            rgb99 = slot99[offset:offset + 3]
            if rgb98 != rgb99:
                row["shared_source_rgb_conflict"] += 1
                if len(examples["conflicting_shared"]) < 12:
                    examples["conflicting_shared"].append([x, y])
            matching98 = rgb98 == final_rgb
            matching99 = rgb99 == final_rgb
            name = ("shared_final_matches_both" if matching98 and matching99
                    else "shared_final_matches_98_only" if matching98
                    else "shared_final_matches_99_only" if matching99
                    else "shared_final_matches_neither")
            row[name] += 1
            if not matching98 and not matching99 and (
                len(examples["shared_matches_neither"]) < 12
            ):
                examples["shared_matches_neither"].append([x, y])
        else:
            key = "slot98_only" if a else "slot99_only"
            row[key] += 1
            source_rgb = (slot98 if a else slot99)[offset:offset + 3]
            if source_rgb != final_rgb:
                mismatch_key = ("exclusive98_rgb_differs_final" if a
                                else "exclusive99_rgb_differs_final")
                row[mismatch_key] += 1
                if len(examples["exclusive_rgb_differs_final"]) < 12:
                    examples["exclusive_rgb_differs_final"].append([x, y])

    totals = {key: sum(band[key] for band in bands.values())
              for key in fields}
    assert totals["slot98_only"] + totals["slot99_only"] + totals["shared"] + totals["neither"] == n // 4
    assert sum(totals[key] for key in (
        "shared_final_matches_98_only", "shared_final_matches_99_only",
        "shared_final_matches_both", "shared_final_matches_neither",
    )) == totals["shared"]
    return {
        "classification": "read-only-pre-BG-OBJ-overlap-and-final-RGB-census",
        "logical_width": LOGICAL_WIDTH,
        "logical_height": LOGICAL_HEIGHT,
        "viewport_split_y": 112,
        "band_counts": bands,
        "total_counts": totals,
        "emitted_slot98_pixels": totals["slot98_only"] + totals["shared"],
        "emitted_slot99_pixels": totals["slot99_only"] + totals["shared"],
        "distinct_emitted_coordinates": (
            totals["slot98_only"] + totals["slot99_only"] + totals["shared"]
        ),
        "bounded_coordinate_examples": examples,
        "final_pixel_ownership_or_HD_admission_proven": False,
        "caveat": ("Emitted OBJ alpha and RGB matching the final Original "
                   "frame cannot identify the winning PPU layer; RGB "
                   "mismatches are candidate overpaint/occlusion locations, "
                   "not attributed causes."),
    }


def assess(stock_crc: Path, original_1x_crc: Path, original_4x_crc: Path,
           source_1x_dir: Path, source_4x_dir: Path,
           source98: Path, source99: Path, log98: Path, log99: Path,
           probe98_dir: Path, probe99_dir: Path,
           probe98_crc: Path, probe99_crc: Path,
           frame: int = 2208) -> dict:
    if frame != 2208:
        raise ValueError("only guest2208 authentic 1P 0895 is in scope")
    base, one, four = (p.read_bytes().splitlines()
                       for p in (stock_crc, original_1x_crc, original_4x_crc))
    probes = (probe98_crc.read_bytes().splitlines(), probe99_crc.read_bytes().splitlines())
    if len(base) != 5447 or any(stream != base for stream in (one, four, *probes)):
        raise ValueError("independent five-way native P1 original guest CRC mismatch")
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
    pair_rgba = {}
    for slot, path, log, probe_dir in (
        (98, source98, log98, probe98_dir),
        (99, source99, log99, probe99_dir),
    ):
        meta = read_source(path, slot)
        if meta["guest_frame"] != frame:
            raise ValueError("source OBJ slot belongs to wrong native guest frame")
        native_log = log.read_text(encoding="utf-8", errors="replace")
        actual_probe = capture_files(probe_dir, 1)
        if set(actual_probe) != set(first) or len(actual_probe) != 7:
            raise ValueError("native top OAM probe is missing full Original scene frames")
        oracle = assess_source(first, actual_probe, meta, native_log, 7)
        if oracle["status"] != "passed" or oracle["identical_complete_original_342_rasters"] != 7:
            raise ValueError("native isolated source OBJ changed genuine final Original")
        data = path.read_bytes()
        if not data.startswith(HEADER) or (
            len(data) != len(HEADER) + LOGICAL_WIDTH * LOGICAL_HEIGHT * 4
        ):
            raise ValueError("native isolated source PPU plane corrupted")
        rgba = data[len(HEADER):]
        pair_rgba[slot] = rgba
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
    pair_overlap = classify_top_source_pair(
        first[frame], pair_rgba[98], pair_rgba[99])
    for rec in records:
        actual = pair_overlap["emitted_slot98_pixels" if rec["original_oam_slot"] == 98
                              else "emitted_slot99_pixels"]
        if actual != rec["rgb_vs_final_observation"]["isolated_source_opaque"]:
            raise ValueError("source pair census is inconsistent with isolated OBJ alpha")
    return {
        "top_pair_overlap_and_final_rgb_census": pair_overlap,
        "schema_version": 1,
        "status": "native-1p-paired-top-oam-source-truth",
        "native_guest_frame": frame,
        "source_p1_semantic": "0895",
        "native_original_guest_crc_identical": 5447,
        "independent_original_guest_processes": 5,
        "native_1x_and_4x_source_frames_identical": 7,
        "original_top_slot98_and_slot99_sources": records,
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
                "four-dir", "source98", "source99", "log98", "log99",
                "probe98-dir", "probe99-dir", "probe98-crc", "probe99-crc", "out"):
        p.add_argument("--" + opt, type=Path, required=True)
    a = p.parse_args()
    report = assess(a.stock_crc, a.one_crc, a.four_crc,
                    a.one_dir, a.four_dir, a.source98, a.source99,
                    a.log98, a.log99, a.probe98_dir, a.probe99_dir,
                    a.probe98_crc, a.probe99_crc)
    a.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("UR_BALDOSA_1P_TOP_SOURCE_98_99 "
          f"status={report['status']} "
          f"slot98={report['original_top_slot98_and_slot99_sources'][0]['rgb_vs_final_observation']['isolated_source_opaque']} "
          f"slot99={report['original_top_slot98_and_slot99_sources'][1]['rgb_vs_final_observation']['isolated_source_opaque']} "
          "BGpriority_proven=0 HDadmitted=0")


if __name__ == "__main__":
    main()
