#!/usr/bin/env python3
"""Byte-observed 2P upper racer OBJ front/rear actual PPU removal partition.

Read already independently validated native source98/source99 planes,
unaltered stock Original, actual slot98-only removed PPU output and source/
native final reports at guest1856 and1872. No new native run/guest harness.
Discriminate front-only pixels, rear-only, different-colour overlap and
same-colour overlap against the actual PPU results; no arbitrary HD mask.
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

FRAMES = (1856, 1872)
SLOTS = (98, 99)


def classify(stock: bytes, front: bytes, rear: bytes, no_front: bytes) -> dict:
    size = WIDTH * HEIGHT * 4
    if any(len(p) != size for p in (stock, front, rear, no_front)):
        raise ValueError("all planes must be genuine full Original 342x224 RGBA")
    counts = {
        "front_only": 0, "rear_only": 0,
        "overlap_different_rgb": 0, "overlap_equal_rgb": 0,
        "emitted_front": 0, "emitted_rear": 0,
        "stock_front_rgb_matches_when_emitted": 0,
        "stock_rear_rgb_matches_on_rear_only": 0,
        "removed_reveals_rear_rgb_on_different_overlap": 0,
        "front_only_removal_final_deltas": 0,
        "different_overlap_final_deltas": 0,
        "equal_overlap_no_final_delta": 0,
        "other_final_changed_pixels": 0,
        "unexpected_original_source_priority_pixels": 0,
    }
    errors = []
    for pos in range(WIDTH * HEIGHT):
        at = pos * 4
        fa, ra = (front[at + 3] != 0, rear[at + 3] != 0)
        changed = stock[at:at + 4] != no_front[at:at + 4]
        stock_rgb = stock[at:at + 3]
        f_rgb, r_rgb = front[at:at + 3], rear[at:at + 3]
        counts["emitted_front"] += fa
        counts["emitted_rear"] += ra
        if fa:
            counts["stock_front_rgb_matches_when_emitted"] += stock_rgb == f_rgb
        if fa and not ra:
            counts["front_only"] += 1
            counts["front_only_removal_final_deltas"] += changed
            good = stock_rgb == f_rgb and changed
        elif ra and not fa:
            counts["rear_only"] += 1
            counts["stock_rear_rgb_matches_on_rear_only"] += stock_rgb == r_rgb
            good = stock_rgb == r_rgb and not changed
        elif fa and ra and f_rgb != r_rgb:
            counts["overlap_different_rgb"] += 1
            counts["different_overlap_final_deltas"] += changed
            reveals = no_front[at:at + 3] == r_rgb
            counts["removed_reveals_rear_rgb_on_different_overlap"] += reveals
            good = stock_rgb == f_rgb and reveals and changed
        elif fa and ra:
            counts["overlap_equal_rgb"] += 1
            counts["equal_overlap_no_final_delta"] += not changed
            good = stock_rgb == f_rgb == r_rgb and not changed
        else:
            good = not changed
        if not fa and changed:
            counts["other_final_changed_pixels"] += 1
        if not good:
            counts["unexpected_original_source_priority_pixels"] += 1
            if len(errors) < 12:
                y, x = divmod(pos, WIDTH)
                errors.append([x, y])
    return {
        "status": ("exact-upper-original-ppu-priority-observation"
                   if counts["unexpected_original_source_priority_pixels"] == 0
                   else "unproven-ppu-observation"),
        "counts": counts,
        "bounded_disagreement_xy_examples": errors,
        "all_emitted_front_pixels_stock_rgb_equal_front_source": (
            counts["emitted_front"] ==
            counts["stock_front_rgb_matches_when_emitted"]
        ),
        "all_rear_only_stock_rgb_equal_rear_source": (
            counts["rear_only"] ==
            counts["stock_rear_rgb_matches_on_rear_only"]
        ),
        "all_overlap_different_reveals_rear_rgb_on_front_removal": (
            counts["overlap_different_rgb"] ==
            counts["removed_reveals_rear_rgb_on_different_overlap"]
        ),
        "source_rgb_equal_is_unique_ppu_owner_proof": False,
        "native_paint_or_hd_removal_permitted": False,
    }


def verify(root: Path, frame: int) -> dict:
    if frame not in FRAMES:
        raise ValueError("only accepted native 2P upper frames1856 and1872")
    original_name = f"ur-baldosa-ws342-{frame:06d}.pam"
    stock_path = root / "baldosa-ws342-captures" / original_name
    removed_dir = ("baldosa-ws342-counterfactual-slot98" if frame == 1856
                   else "baldosa-ws342-counterfactual-slot98-frame1872")
    removed_path = root / removed_dir / original_name
    if stock_path.resolve() == removed_path.resolve():
        raise ValueError("stock and removed Original must be independent outputs")
    stock, no_front = read_pam(stock_path), read_pam(removed_path)
    src = {}
    metas = {}
    for slot in SLOTS:
        path = root / "baldosa-ws342-obj-slots" / (
            f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
        report_path = root / "baldosa-evidence" / (
            f"ws342_obj_slot_{slot}" + (f"_frame{frame}" if frame == 1872
                                      else "") + ".json")
        pixels, meta = read_pam(path), read_source(path, slot)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (report.get("status") != "passed" or
            report.get("schema_version") != 1 or
            report.get("source_log_matches_pam") is not True or
            report.get("identical_complete_original_342_rasters") != 6 or
            report.get("shared_full_frame_guest_ids") !=
                [1808, 1824, 1840, 1856, 1872, 1888] or
            report.get("differing_original_rasters") != [] or
            report.get("source") != meta or
            report.get("source_frame_main_raster_sha256") !=
                hashlib.sha256(stock).hexdigest() or
            meta.get("top_opaque_source_pixels", 0) <= 0 or
            meta.get("bottom_opaque_source_pixels") != 0):
            raise ValueError(f"authentic source slot{slot}/frame{frame} invalid")
        src[slot] = pixels
        metas[slot] = meta
    native_report = json.loads((root / "baldosa-evidence" /
                               f"ws342_slot98_final_visibility_{frame}.json").read_text())
    measured = classify(stock, src[98], src[99], no_front)
    cnt = measured["counts"]
    if (native_report.get("status") != "passed" or
        native_report.get("schema_version") != 1 or
        native_report.get("guest_frame") != frame or
        native_report.get("source_oam_slot") != 98 or
        native_report.get("guest_crc_equal_in_all_three_processes") is not True or
        native_report.get("single_slot_original_ppu_removal_armed") is not True or
        native_report.get("source_emitted_alpha_pixels") != cnt["emitted_front"] or
        native_report.get("native_ppu_final_contributed_pixels") !=
            (cnt["front_only_removal_final_deltas"] +
             cnt["different_overlap_final_deltas"]) or
        native_report.get("native_ppu_changed_outside_emitted_source_alpha") != 0 or
        native_report.get("stock_sha256") != hashlib.sha256(stock).hexdigest() or
        native_report.get("source_sha256") != metas[98]["source_sha256"] or
        native_report.get("counterfactual_sha256") !=
            hashlib.sha256(no_front).hexdigest()):
        raise ValueError(f"actual native slot98 causal report frame{frame} invalid")
    if measured["status"] != "exact-upper-original-ppu-priority-observation":
        raise ValueError(f"original native front/rear raster does not satisfy expected PPU evidence: {frame}")
    return {
        "native_guest_frame": frame,
        "source_report_and_native_deletion_verified": True,
        "full_stock_original_sha256": native_report["stock_sha256"],
        "source98_sha256": metas[98]["source_sha256"],
        "source99_sha256": metas[99]["source_sha256"],
        "removed98_final_sha256": native_report["counterfactual_sha256"],
        **measured,
    }


def assess(root: Path) -> dict:
    scenes = {str(frame): verify(root, frame) for frame in FRAMES}
    if scenes["1856"]["full_stock_original_sha256"] == scenes["1872"]["full_stock_original_sha256"]:
        raise ValueError("two moving frames reuse a stale Original PPU image")
    return {
        "schema_version": 1,
        "status": "two-moving-native-upper-2p-front-rear-composition-witnesses",
        "native_frames": list(FRAMES),
        "per_original_guest_frame": scenes,
        "correct_original_source_pixels_not_shippable_hd_mask": True,
        "authoritative_bg_window_or_single_ppu_winner_proven": False,
        "safe_to_remove_original_or_author_hd": False,
        "limits": ("Strict same-frame native Original PPU stock/front/rear/"
                   "front-only removal observations show final visible "
                   "source contribution at two authenticated 2P scenes. "
                   "Even changed pixels and rear colour reveal do not "
                   "establish all BG/window/OBJ priority in general or "
                   "approve renderer changes or artistic reconstruction."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-artifact-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    report = assess(a.native_artifact_root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                     encoding="utf-8")
    for frame in FRAMES:
        c = report["per_original_guest_frame"][str(frame)]["counts"]
        print(f"UR_QA08_2P_TOP_PPU_REVEAL frame={frame} "
              f"front_only={c['front_only']} "
              f"overlap_rear_reveal={c['overlap_different_rgb']} "
              f"equal_rgb_redundant={c['overlap_equal_rgb']} "
              f"violations={c['unexpected_original_source_priority_pixels']} HD_admitted=0")


if __name__ == "__main__":
    main()
