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
PRERACE_REFERENCE_SHIFT_XY = [0, 113]  # observed before GO, not a post-GO rule
MIN_UNCHANGED_STOCK_FRAMES = 7


def occupied_rgba(data: bytes) -> dict[tuple[int, int], bytes]:
    if len(data) != WIDTH * HEIGHT * 4:
        raise ValueError("authentic complete 342x224 PPU source plane required")
    pixels = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            at = 4 * (y * WIDTH + x)
            if data[at + 3]:
                pixels[(x, y)] = data[at:at + 4]
    return pixels


def compare(upper: bytes, lower: bytes) -> dict:
    """Infer *candidate* full-source translation from independent alpha bboxes.

    Exact translation implies identical source alpha geometry including
    the translated bbox, so its minX/minY delta is necessary and unique.
    Then verify every occupied source RGBA and all support coordinates;
    do not assume the earlier countdown (0,+113) offset persists after GO.
    """
    top = occupied_rgba(upper)
    bottom = occupied_rgba(lower)
    top_wrong_band = sum(y >= HEIGHT // 2 for _, y in top)
    bottom_wrong_band = sum(y < HEIGHT // 2 for _, y in bottom)
    delta = None
    differences = []
    different_alpha = different_rgba = 0
    if top and bottom:
        dx = min(x for x, _ in bottom) - min(x for x, _ in top)
        dy = min(y for _, y in bottom) - min(y for _, y in top)
        delta = [dx, dy]
        shifted = {(x + dx, y + dy): rgba for (x, y), rgba in top.items()}
        missing_up = shifted.keys() - bottom.keys()
        missing_bottom = bottom.keys() - shifted.keys()
        different_alpha = len(missing_up) + len(missing_bottom)
        shared = shifted.keys() & bottom.keys()
        different_rgba = sum(shifted[xy] != bottom[xy] for xy in shared)
        for x, y in sorted(missing_up | missing_bottom | {
                xy for xy in shared if shifted[xy] != bottom[xy]}):
            if len(differences) >= 12:
                break
            differences.append({
                "upper_xy": [x - dx, y - dy],
                "lower_xy": [x, y],
                "upper_rgba": list(shifted.get((x, y), bytes(4))),
                "lower_rgba": list(bottom.get((x, y), bytes(4))),
            })
    else:
        # One-sided emission is a measurable failure of pair equivalence,
        # not a missing file or automatically approved substitute rider.
        different_alpha = len(top) + len(bottom)
        for (x, y), rgba in list(sorted(top.items()))[:6]:
            differences.append({"upper_xy": [x, y], "lower_xy": None,
                                "upper_rgba": list(rgba),
                                "lower_rgba": [0, 0, 0, 0]})
        for (x, y), rgba in list(sorted(bottom.items()))[:6]:
            differences.append({"upper_xy": None, "lower_xy": [x, y],
                                "upper_rgba": [0, 0, 0, 0],
                                "lower_rgba": list(rgba)})
    alias = (bool(top) and bool(bottom) and
             different_alpha == 0 and different_rgba == 0 and
             top_wrong_band == 0 and bottom_wrong_band == 0)
    return {
        "status": ("source-positive-exact-translated-rgba-alias" if alias
                   else "source-empty" if not (top or bottom)
                   else "source-visible-split-divergence"),
        "upper_source_opaque_pixels": len(top),
        "lower_source_opaque_pixels": len(bottom),
        "bbox_inferred_upper_to_lower_translation_xy": delta,
        "different_alpha_after_registration": different_alpha,
        "different_rgba_after_registration": different_rgba,
        "upper_source_in_lower_analytic_half": top_wrong_band,
        "lower_source_in_upper_analytic_half": bottom_wrong_band,
        "exact_rgba_split_alias_observed": alias,
        "bounded_differences": differences,
        "source_bbox_alone_is_not_sufficient_for_alpha_or_rgba_match": True,
        "hardware_obj_bg_window_owner_proven": False,
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
        "original_prerace_source_translation_xy_not_assumed": PRERACE_REFERENCE_SHIFT_XY,
        "postgo_translation_same_across_both_player_pairs": (
            pairs["98->97"]["exact_rgba_split_alias_observed"] and
            pairs["99->96"]["exact_rgba_split_alias_observed"] and
            pairs["98->97"]["bbox_inferred_upper_to_lower_translation_xy"] ==
            pairs["99->96"]["bbox_inferred_upper_to_lower_translation_xy"]
        ),
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
              f"top={record['upper_source_opaque_pixels']} " +
              f"bottom={record['lower_source_opaque_pixels']} " +
              f"shift={record['bbox_inferred_upper_to_lower_translation_xy']} " +
              f"alpha_diff={record['different_alpha_after_registration']} " +
              f"rgba_diff={record['different_rgba_after_registration']} " +
              "source_only=1 remastered_admitted=0")


if __name__ == "__main__":
    main()
