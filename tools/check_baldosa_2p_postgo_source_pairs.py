#!/usr/bin/env python3
"""Characterize genuine 2P post-GO upper/lower original OAM source symmetry.

Reads four separate successful native PPU read-only source routes at guest2208,
their seven matching full Original 342-wide frame controls and source metadata.
Identical split source is observed, NOT assumed: alpha, full visible RGBA and
out-of-registered-band emissions are measured. No guest or renderer mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
    from tools.check_baldosa_wide_single_slot_source import read_source
except ModuleNotFoundError:
    from check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
    from check_baldosa_wide_single_slot_source import read_source

FRAME = 2208
SLOT_PAIRS = ((98, 97), (99, 96))
SPLIT_DELTA_Y = 113
MIN_UNCHANGED_STOCK_FRAMES = 7


def compare(upper: bytes, lower: bytes) -> dict:
    if len(upper) != WIDTH * HEIGHT * 4 or len(lower) != len(upper):
        raise ValueError("authentic complete 342x224 PPU source planes required")
    top_count = bottom_count = differing_alpha = differing_rgba = 0
    examples = []
    for y in range(HEIGHT - SPLIT_DELTA_Y):
        for x in range(WIDTH):
            a = 4 * (y * WIDTH + x)
            b = 4 * ((y + SPLIT_DELTA_Y) * WIDTH + x)
            ua, la = upper[a + 3] != 0, lower[b + 3] != 0
            top_count += ua
            bottom_count += la
            mismatch_alpha = ua != la
            mismatch_rgb = ua and la and upper[a:a + 4] != lower[b:b + 4]
            differing_alpha += mismatch_alpha
            differing_rgba += mismatch_alpha or mismatch_rgb
            if (mismatch_alpha or mismatch_rgb) and len(examples) < 12:
                examples.append({
                    "upper_xy": [x, y],
                    "lower_xy": [x, y + SPLIT_DELTA_Y],
                    "upper_rgba": list(upper[a:a + 4]) if ua else [0, 0, 0, 0],
                    "lower_rgba": list(lower[b:b + 4]) if la else [0, 0, 0, 0],
                })
    # y111 cannot be matched to a +113 target within 224 rows, and
    # lower y112 cannot come from the upper nonnegative source raster.
    upper_unpaired = sum(upper[4 * (111 * WIDTH + x) + 3] != 0
                         for x in range(WIDTH))
    lower_unpaired = sum(lower[4 * (112 * WIDTH + x) + 3] != 0
                         for x in range(WIDTH))
    upper_wrong_band = sum(upper[4 * (y * WIDTH + x) + 3] != 0
                           for y in range(112, HEIGHT)
                           for x in range(WIDTH))
    lower_wrong_band = sum(lower[4 * (y * WIDTH + x) + 3] != 0
                           for y in range(112)
                           for x in range(WIDTH))
    observed_alias = (
        top_count > 0 and top_count == bottom_count and
        differing_rgba == 0 and upper_unpaired == 0 and
        lower_unpaired == 0 and upper_wrong_band == 0 and
        lower_wrong_band == 0
    )
    return {
        "status": ("source-positive-exact-split-rgba-alias" if observed_alias
                   else "source-empty" if not (top_count or bottom_count or
                                              upper_unpaired or lower_unpaired or
                                              upper_wrong_band or lower_wrong_band)
                   else "source-visible-split-divergence"),
        "upper_in_registered_rows_0_to_110": top_count,
        "lower_in_registered_rows_113_to_223": bottom_count,
        "different_alpha_registered_coordinates": differing_alpha,
        "different_rgba_registered_coordinates": differing_rgba,
        "upper_unpaired_row111_alpha": upper_unpaired,
        "lower_unpaired_row112_alpha": lower_unpaired,
        "upper_source_in_lower_analytic_half": upper_wrong_band,
        "lower_source_in_upper_analytic_half": lower_wrong_band,
        "exact_rgba_split_alias_observed": observed_alias,
        "bounded_differences": examples,
        "all_original_PPU_BG_window_priority_proven": False,
        "HD_character_art_approved": False,
    }


def assess(root: Path) -> dict:
    original = read_pam(
        root / "baldosa-ws342-captures" / f"ur-baldosa-ws342-{FRAME:06d}.pam")
    original_sha = hashlib.sha256(original).hexdigest()
    sources, reports = {}, {}
    for slot in (96, 97, 98, 99):
        path = (root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam")
        report_path = (root / "baldosa-evidence" /
                       f"ws342_obj_slot_{slot}_frame{FRAME}.json")
        source = read_pam(path)
        metadata = read_source(path, slot)
        record = json.loads(report_path.read_text(encoding="utf-8"))
        ids = record.get("shared_full_frame_guest_ids", [])
        if (record.get("schema_version") != 1 or
            record.get("status") != "passed" or
            record.get("source_log_matches_pam") is not True or
            record.get("identical_complete_original_342_rasters", 0) <
                MIN_UNCHANGED_STOCK_FRAMES or
            record.get("minimum_shared_frames", 0) <
                MIN_UNCHANGED_STOCK_FRAMES or
            record.get("differing_original_rasters") != [] or
            len(ids) < MIN_UNCHANGED_STOCK_FRAMES or
            ids != sorted(set(ids)) or FRAME not in ids or
            record.get("source") != metadata or
            record.get("source_frame_main_raster_sha256") != original_sha or
            record.get("guest_crc_comparison") !=
                "Externally enforced byte-exact in native workflow" or
            metadata.get("guest_frame") != FRAME or
            metadata.get("slot") != slot):
            raise ValueError(f"native 2P post-GO source slot{slot}/frame{FRAME} unproven")
        sources[slot] = source
        reports[str(slot)] = metadata
    pairs = {}
    for upper_slot, lower_slot in SLOT_PAIRS:
        pairs[f"{upper_slot}->{lower_slot}"] = compare(
            sources[upper_slot], sources[lower_slot])
    return {
        "schema_version": 1,
        "status": "authenticated-original-2p-postgo-paired-source-characterization",
        "guest_frame": FRAME,
        "real_stock_original_sha256": original_sha,
        "source_metadata_by_slot": reports,
        "source_paired_upper_to_lower": pairs,
        "exact_original_split_translation_pixels": [0, SPLIT_DELTA_Y],
        "minimum_complete_unaltered_original_frame_controls_per_slot":
            MIN_UNCHANGED_STOCK_FRAMES,
        "source_report_native_guest_crc_parity_attested_not_replayed_here": True,
        "result_is_observational_not_required_exact_alias": True,
        "full_stock_vs_source_PPU_renderer_priority_inferred": False,
        "remastered_source_erasure_allowed": False,
        "artistic_likeness_approved": False,
        "limits": (
            "Only original native guest2208 after GO. Compared visible "
            "prepriority OBJ source alpha and RGBA, under sample-specific "
            "113-row registration. Genuine source aliases or divergences "
            "do not prove final hardware BG/window/OBJ winners, author "
            "3D art or allow destructive source capture."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-artifact-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    report = assess(a.native_artifact_root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    for name, record in report["source_paired_upper_to_lower"].items():
        print("UR_QA08_POSTGO_2P_SOURCE_PAIR " +
              f"guest={FRAME} slots={name} state={record['status']} " +
              f"top={record['upper_in_registered_rows_0_to_110']} " +
              f"bottom={record['lower_in_registered_rows_113_to_223']} " +
              f"different={record['different_rgba_registered_coordinates']} " +
              "source_only=1 remastered_admitted=0")


if __name__ == "__main__":
    main()
