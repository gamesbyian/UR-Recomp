#!/usr/bin/env python3
"""Native 2P post-GO front OBJ final causal delta under original text.

Use genuine stock, two independently isolated source planes (one upper or
lower front plus opposite rear), and an independently rerun exact guest2208
PPU raster with ONLY the front slot removed. The PNG/PAM is not synthesized
and no HD painter or production source removal is touched. Foreground RGB
source/final mismatch is observed, never identified as hardware BG owner.
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
SLOTS = {98: 99, 96: 97}  # upper front / lower front, observed at native post-GO
EXPECTED_STOCK_SHA = "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a"
SOURCE_SHA = {
    96: "658d79c05524ca40af81f92ce6bb0d49adbe6bbcbc07d599e7e8bcdbdd1eb580",
    97: "e9e924050ad5da46f24d4be4b3f587e80c80c8bb04bec19014e38cf06c0e5b44",
    98: "de587f5986b30663f0178a0140e746b84e601716941bb09dacab5426e8d56fe2",
    99: "836da1c261ce6ea07cc9a7a66f5a4443e494388e07cefb6da232a4b98764b564",
}
GUEST_CRC_LINES = 2473
RED_TEXT_OFFSET = (107, 0, 0)


def analyze(stock: bytes, front: bytes, rear: bytes, without_front: bytes) -> dict:
    if any(len(x) != WIDTH * HEIGHT * 4 for x in
           (stock, front, rear, without_front)):
        raise ValueError("full native 342x224 original/source/counterfactual RGBA required")
    counts = {
        "front_emitted": 0, "rear_emitted": 0,
        "front_only": 0, "shared_same_source_rgb": 0,
        "shared_different_source_rgb": 0,
        "stock_rgb_equal_front_on_emission": 0,
        "stock_rgb_different_front_on_emission": 0,
        "stock_exact_red_plus_107_over_front": 0,
        "native_final_changed_within_front_source": 0,
        "native_final_changed_outside_front_source": 0,
        "native_final_changed_at_red_text_source_positions": 0,
        "native_final_unchanged_at_red_text_source_positions": 0,
        "native_front_removal_reveals_rear_rgb_on_overlap": 0,
        "native_front_removal_overlap_changed_pixels": 0,
    }
    red_examples, other_changed_examples = [], []
    for at in range(0, len(stock), 4):
        f = front[at + 3] != 0
        r = rear[at + 3] != 0
        counts["front_emitted"] += f
        counts["rear_emitted"] += r
        changed = stock[at:at + 4] != without_front[at:at + 4]
        y, x = divmod(at // 4, WIDTH)
        if not f:
            if changed:
                counts["native_final_changed_outside_front_source"] += 1
                if len(other_changed_examples) < 12:
                    other_changed_examples.append([x, y])
            continue
        if r:
            shared_equal = front[at:at + 3] == rear[at:at + 3]
            counts["shared_same_source_rgb" if shared_equal
                   else "shared_different_source_rgb"] += 1
            counts["native_front_removal_overlap_changed_pixels"] += changed
            counts["native_front_removal_reveals_rear_rgb_on_overlap"] += (
                without_front[at:at + 3] == rear[at:at + 3]
            )
        else:
            counts["front_only"] += 1
        if stock[at:at + 3] == front[at:at + 3]:
            counts["stock_rgb_equal_front_on_emission"] += 1
        else:
            counts["stock_rgb_different_front_on_emission"] += 1
        red = tuple(int(stock[at + i]) - int(front[at + i]) for i in range(3))
        if red == RED_TEXT_OFFSET:
            counts["stock_exact_red_plus_107_over_front"] += 1
            counts["native_final_changed_at_red_text_source_positions"] += changed
            counts["native_final_unchanged_at_red_text_source_positions"] += not changed
            if len(red_examples) < 13:
                red_examples.append({
                    "xy": [x, y],
                    "source_rgb": list(front[at:at + 3]),
                    "stock_original_rgb": list(stock[at:at + 3]),
                    "native_original_after_front_removal_rgb":
                        list(without_front[at:at + 3]),
                    "native_final_changed": changed,
                })
        if changed:
            counts["native_final_changed_within_front_source"] += 1
    return {
        "counts": counts,
        "bounded_original_red_text_over_front_samples": red_examples,
        "bounded_invalid_outside_source_delta_xy": other_changed_examples,
        "all_native_final_changed_pixels_within_front_alpha": (
            counts["native_final_changed_outside_front_source"] == 0),
        "final_pixel_source_rgb_matches_not_equal_unique_ppu_owner": True,
        "exact_BG_window_OBJ_text_colour_math_owner_known": False,
        "normal_renderer_may_delete_original_front_sprite": False,
        "remastered_HDAuthorization": False,
    }


def assess(root: Path) -> dict:
    original_path = (root / "baldosa-ws342-captures" /
                     "ur-baldosa-ws342-002208.pam")
    stock = read_pam(original_path)
    if hashlib.sha256(stock).hexdigest() != EXPECTED_STOCK_SHA:
        raise ValueError("not authenticated exact original post-GO stock PPU frame")
    results = {}
    for front, rear in SLOTS.items():
        def src_path(slot: int) -> Path:
            return (root / "baldosa-ws342-obj-slots" /
                    f"ur-baldosa-ws342-obj-slot{slot}-frame002208.pam")
        plane = {}
        for slot in (front, rear):
            path = src_path(slot)
            pixels, meta = read_pam(path), read_source(path, slot)
            report = json.loads((root / "baldosa-evidence" /
                                 f"ws342_obj_slot_{slot}_frame2208.json").read_text())
            if (meta.get("guest_frame") != FRAME or
                meta.get("slot") != slot or
                meta.get("source_sha256") != SOURCE_SHA[slot] or
                report.get("source") != meta or
                report.get("schema_version") != 1 or
                report.get("status") != "passed" or
                report.get("source_log_matches_pam") is not True or
                report.get("identical_complete_original_342_rasters") != 7 or
                report.get("minimum_shared_frames") != 7 or
                report.get("shared_full_frame_guest_ids") !=
                    [1808, 1824, 1840, 1856, 1872, 1888, FRAME] or
                report.get("differing_original_rasters") != [] or
                report.get("source_frame_main_raster_sha256") != EXPECTED_STOCK_SHA or
                report.get("guest_crc_comparison") !=
                    "Externally enforced byte-exact in native workflow"):
                raise ValueError(f"post-GO source native slot{slot} provenance not accepted")
            plane[slot] = pixels
        probe_name = f"race_2p_split_ur_ws342_counterfactual_slot{front}_frame2208"
        removed = read_pam(root /
                           f"baldosa-ws342-counterfactual-slot{front}-frame2208" /
                           "ur-baldosa-ws342-002208.pam")
        evidence = root / "baldosa-evidence"
        controls = [
            evidence / "race_2p_split_ur_ws342/fd/crc.txt",
            evidence / f"race_2p_split_ur_ws342_slot_{front}/fd/crc.txt",
            evidence / f"race_2p_split_ur_ws342_slot_{rear}/fd/crc.txt",
            evidence / probe_name / "fd/crc.txt",
        ]
        streams = [p.read_bytes().splitlines() for p in controls]
        if (len(streams[0]) != GUEST_CRC_LINES or
            any(stream != streams[0] for stream in streams[1:])):
            raise ValueError("four independent native original 2P 2473-CRC guest routes disagree")
        original_log = (evidence / probe_name / "log.txt").read_text(
            encoding="utf-8", errors="replace")
        exact_marker = (f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={FRAME} "
                        f"slot={front} status=armed guest_unchanged=1")
        if sum(x.strip() == exact_marker for x in original_log.splitlines()) != 1:
            raise ValueError("original PPU native front-single-slot removal marker absent")
        observed = analyze(stock, plane[front], plane[rear], removed)
        c = observed["counts"]
        if (not c["front_emitted"] or not c["rear_emitted"] or
            c["front_emitted"] != (317 if front == 98 else 313) or
            c["stock_exact_red_plus_107_over_front"] != 13 or
            c["native_final_changed_outside_front_source"] != 0):
            raise ValueError(f"post-GO native source/front {front} and final causal proof changed")
        results[str(front)] = {
            "native_guest_frame": FRAME,
            "front_slot_removed": front,
            "rear_source_slot": rear,
            "unmodified_original_sha256": EXPECTED_STOCK_SHA,
            "front_source_sha256": SOURCE_SHA[front],
            "rear_source_sha256": SOURCE_SHA[rear],
            "native_front_removed_original_sha256": hashlib.sha256(removed).hexdigest(),
            "all_four_guest_crc_streams_equal_at_exact_frame_count": GUEST_CRC_LINES,
            "authentic_native_arm_marker_one": True,
            **observed,
        }
    return {
        "schema_version": 1,
        "status": "native-two-viewport-original-postgo-front-slot-contributions",
        "guest_frame": FRAME,
        "proven_original_2p_fronts_by_viewport": {"top": 98, "bottom": 96},
        "native_each_front_removed_in_independent_full_guest_process": True,
        "per_original_front_slot": results,
        "total_expected_original_pixel_comparisons": WIDTH * HEIGHT * 2,
        "authored_HD_priority_or_visual_likeness_approved": False,
        "original_source_removal_allowed_in_shipping": False,
        "limits": ("Two independent native original USA 2P PPU diagnostic "
                   "slot-removals only at guest2208, one for each viewport. "
                   "Guest CRC parity, exact source and original reports bound "
                   "causal final pixel changes, not general BG/window/text "
                   "colour-math ownership, visual fidelity of authored "
                   "models, or normal renderer sprite deletion."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.native_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    for slot, r in result["per_original_front_slot"].items():
        c = r["counts"]
        print("UR_QA08_POSTGO_FRONT_NATIVE " +
              f"guest={FRAME} slot={slot} emitted={c['front_emitted']} " +
              f"contributed={c['native_final_changed_within_front_source']} " +
              f"red_text={c['stock_exact_red_plus_107_over_front']} " +
              f"text_changed={c['native_final_changed_at_red_text_source_positions']} " +
              f"text_unchanged={c['native_final_unchanged_at_red_text_source_positions']} " +
              "outside=0 guestCRC=2473 HD_admitted=0")


if __name__ == "__main__":
    main()
