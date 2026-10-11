#!/usr/bin/env python3
"""Original native 2P lower-viewport rear-only three-pixel occlusion.

Pure original 342x224 PPU source/stock/removal analysis at guest1856.
Does not infer which BG/window/OBJ layer owns three blue raster pixels,
authorize HD sprite removal or alter any renderer.
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

FRAME = 1856
FRONT, REAR = 96, 97
EXPECTED_MASKED_REAR_ONLY = (
    (188, 156, (49, 49, 49), (57, 57, 255)),
    (189, 156, (74, 74, 74), (57, 57, 255)),
    (189, 157, (16, 16, 8), (57, 57, 255)),
)
STOCK_SHA = "0e956fac212cb7413a32ee2a0de318540e58cfd5f2b7610472c2573ab6719dd9"
REMOVED_SHA = "84581f02f0b3e49b97ffb0654357aa8f9ecb8546329597dfbbc4bc4d13c47f2a"


def classify(stock: bytes, front: bytes, rear: bytes, removed_front: bytes) -> dict:
    if any(len(p) != WIDTH * HEIGHT * 4 for p in
           (stock, front, rear, removed_front)):
        raise ValueError("four exact complete 342x224 RGBA PPU planes required")
    count = {
        "front_emitted": 0, "rear_emitted": 0,
        "front_only": 0, "rear_only": 0, "overlap_different_rgb": 0,
        "overlap_equal_rgb": 0, "front_only_changed": 0,
        "front_overlap_different_changed": 0,
        "front_overlap_equal_unchanged": 0,
        "different_overlap_exact_rear_reveals": 0,
        "rear_only_original_rgb_matches": 0,
        "rear_only_original_rgb_differs": 0,
        "rear_only_unchanged_after_front_removal": 0,
        "final_changed_outside_front_source": 0,
        "unexpected_original_priority_pixels": 0,
    }
    rear_only_exceptions = []
    disagreements = []
    for pos in range(WIDTH * HEIGHT):
        at = 4 * pos
        fa = front[at + 3] != 0
        ra = rear[at + 3] != 0
        stock_rgb = stock[at:at + 3]
        front_rgb = front[at:at + 3]
        rear_rgb = rear[at:at + 3]
        changed = stock[at:at + 4] != removed_front[at:at + 4]
        count["front_emitted"] += fa
        count["rear_emitted"] += ra
        ok = True
        if fa and not ra:
            count["front_only"] += 1
            count["front_only_changed"] += changed
            ok = changed and stock_rgb == front_rgb
        elif fa and ra and front_rgb != rear_rgb:
            count["overlap_different_rgb"] += 1
            count["front_overlap_different_changed"] += changed
            revealed = removed_front[at:at + 3] == rear_rgb
            count["different_overlap_exact_rear_reveals"] += revealed
            ok = changed and revealed and stock_rgb == front_rgb
        elif fa and ra:
            count["overlap_equal_rgb"] += 1
            count["front_overlap_equal_unchanged"] += not changed
            ok = not changed and stock_rgb == front_rgb == rear_rgb
        elif ra:
            count["rear_only"] += 1
            matches = stock_rgb == rear_rgb
            count["rear_only_original_rgb_matches"] += matches
            count["rear_only_original_rgb_differs"] += not matches
            count["rear_only_unchanged_after_front_removal"] += not changed
            if not matches:
                y, x = divmod(pos, WIDTH)
                rear_only_exceptions.append({
                    "xy": [x, y],
                    "isolated_rear_source_rgb": list(rear_rgb),
                    "original_stock_rgb": list(stock_rgb),
                    "removed_front_rgb": list(removed_front[at:at + 3]),
                    "stock_rgba_alpha": stock[at + 3],
                })
            ok = not changed and (
                matches or removed_front[at:at + 3] == stock_rgb
            )
        elif changed:
            count["final_changed_outside_front_source"] += 1
            ok = False
        if not ok:
            count["unexpected_original_priority_pixels"] += 1
            if len(disagreements) < 12:
                y, x = divmod(pos, WIDTH)
                disagreements.append([x, y])
    return {
        "source_raster_relationship_status": (
            "source-and-native-front-removal-consistent"
            if count["unexpected_original_priority_pixels"] == 0
            else "source-and-native-front-removal-disagree"),
        "counts": count,
        "rear_only_source_hidden_by_stock_rgb": rear_only_exceptions,
        "bounded_unexpected_xy": disagreements,
        "rear_only_source_final_rgb_nonmatches_not_unconditionally_visible": True,
        "unknown_original_bg_window_priority": True,
        "safe_to_paint_rear_behind_front_in_hd": False,
    }


def assess(root: Path) -> dict:
    stock_path = root / "baldosa-ws342-captures" / "ur-baldosa-ws342-001856.pam"
    removed_path = (root / "baldosa-ws342-counterfactual-slot96-frame1856" /
                    "ur-baldosa-ws342-001856.pam")
    stock, removed = read_pam(stock_path), read_pam(removed_path)
    source = {}
    meta = {}
    for slot in (FRONT, REAR):
        path = (root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame001856.pam")
        report_path = root / "baldosa-evidence" / f"ws342_obj_slot_{slot}.json"
        plane, m = read_pam(path), read_source(path, slot)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (report.get("schema_version") != 1 or
            report.get("status") != "passed" or
            report.get("source_log_matches_pam") is not True or
            report.get("identical_complete_original_342_rasters") != 6 or
            report.get("minimum_shared_frames") != 4 or
            report.get("shared_full_frame_guest_ids") !=
                [1808, 1824, 1840, 1856, 1872, 1888] or
            report.get("differing_original_rasters") != [] or
            report.get("source") != m or
            report.get("source_frame_main_raster_sha256") != STOCK_SHA or
            report.get("guest_crc_comparison") !=
                "Externally enforced byte-exact in native workflow" or
            m.get("guest_frame") != FRAME or
            m.get("bottom_opaque_source_pixels", 0) <= 0 or
            m.get("top_opaque_source_pixels") != 0):
            raise ValueError(f"unaltered independent native source slot{slot} provenance invalid")
        source[slot], meta[slot] = plane, m
    p = root / "baldosa-evidence" / "ws342_slot96_final_visibility_1856.json"
    native = json.loads(p.read_text(encoding="utf-8"))
    if (hashlib.sha256(stock).hexdigest() != STOCK_SHA or
        hashlib.sha256(removed).hexdigest() != REMOVED_SHA or
        native.get("schema_version") != 1 or native.get("status") != "passed" or
        native.get("guest_frame") != FRAME or
        native.get("source_oam_slot") != FRONT or
        native.get("source_sha256") != meta[FRONT]["source_sha256"] or
        native.get("stock_sha256") != STOCK_SHA or
        native.get("counterfactual_sha256") != REMOVED_SHA or
        native.get("source_emitted_alpha_pixels") !=
            meta[FRONT]["bottom_opaque_source_pixels"] or
        native.get("guest_crc_equal_in_all_three_processes") is not True or
        native.get("single_slot_original_ppu_removal_armed") is not True or
        native.get("native_ppu_changed_outside_emitted_source_alpha") != 0):
        raise ValueError("native single-slot front96 PPU causal result/provenance invalid")
    out = classify(stock, source[FRONT], source[REAR], removed)
    counts = out["counts"]
    exceptions = tuple(
        (r["xy"][0], r["xy"][1],
         tuple(r["isolated_rear_source_rgb"]),
         tuple(r["original_stock_rgb"]))
        for r in out["rear_only_source_hidden_by_stock_rgb"]
    )
    # The original upper split-source counterpart is exactly 113
    # scanlines above each anomalous lower rear-only pixel. Verify that
    # the unmodified full Original PPU actually shows the expected
    # original rear source RGB above, even though it does not below.
    upper_mirror = []
    for exception in out["rear_only_source_hidden_by_stock_rgb"]:
        x, y = exception["xy"]
        if y < 113:
            raise ValueError("real lower rear-only source gap cannot have top mirror")
        at = 4 * ((y - 113) * WIDTH + x)
        top_rgb = list(stock[at:at + 3])
        if top_rgb != exception["isolated_rear_source_rgb"]:
            raise ValueError("upper split-view Original does not corroborate rear source colour")
        upper_mirror.append({
            "upper_mirror_xy": [x, y - 113],
            "upper_stock_original_rgb": top_rgb,
            "lower_source_original_rgb": exception["isolated_rear_source_rgb"],
            "lower_stock_original_rgb": exception["original_stock_rgb"],
        })
    if (counts["front_emitted"] != 319 or counts["rear_emitted"] != 321 or
        counts["front_only"] != 162 or counts["rear_only"] != 164 or
        counts["overlap_different_rgb"] != 143 or
        counts["overlap_equal_rgb"] != 14 or
        counts["front_only_changed"] != 162 or
        counts["front_overlap_different_changed"] != 143 or
        counts["different_overlap_exact_rear_reveals"] != 143 or
        counts["front_overlap_equal_unchanged"] != 14 or
        counts["rear_only_original_rgb_matches"] != 161 or
        counts["rear_only_original_rgb_differs"] != 3 or
        counts["rear_only_unchanged_after_front_removal"] != 164 or
        counts["final_changed_outside_front_source"] != 0 or
        counts["unexpected_original_priority_pixels"] != 0 or
        exceptions != EXPECTED_MASKED_REAR_ONLY or
        native.get("native_ppu_final_contributed_pixels") != 305):
        raise ValueError("actual pre-countdown lower PPU rear-only 3-pixel source gap changed")
    return {
        "schema_version": 1,
        "status": "original-native-2p-lower-1856-three-rear-only-source-gaps",
        "guest_frame": FRAME,
        "actual_ppu_native_artifact_source_run": 38119117927,
        "native_artifact_id": 11694649120,
        "native_stock_sha256": STOCK_SHA,
        "native_front96_source_sha256": meta[FRONT]["source_sha256"],
        "native_rear97_source_sha256": meta[REAR]["source_sha256"],
        "native_front96_removed_final_sha256": REMOVED_SHA,
        "complete_guest_crc_parity_reported": True,
        "three_upper_mirror_original_RGB_controls": upper_mirror,
        "exact_upper_lower_split_translation_rows": 113,
        **out,
        "per_pixel_background_layer_or_window_owner_proven": False,
        "all_2p_race_frames_or_hd_art_admitted": False,
        "limits": ("One real two-player original USA native PPU guest1856. "
                   "Three isolated rear-only pixels remain absent even "
                   "without front96; this is a final Original RGB gap, "
                   "not proof which BG/window/OBJ priority stage hid them.")
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-artifact-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    report = assess(a.native_artifact_root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_QA08_LOWER_REAR_RGB_GAP " + report["status"] +
          " frame=1856 front96_changed=305 rear_only_visible=161/164" +
          " rear_only_hidden=3 unexpected=0 no_HD_admission=1")


if __name__ == "__main__":
    main()
