#!/usr/bin/env python3
"""Correlate real stock, front-only and adjacent-pair native PPU removals.

Single-front removal can leave a pixel unchanged because an overlapping
rear OBJ emits the same colour. Paired removal can expose whether the
*pair* contributed causally to the final colour. Neither observation
identifies a unique painter or authorizes HD replacement.

Consumes strict native checker reports (with separately verified full
guest CRC streams, PPU frame, source hashes and removal log witnesses).
All rasters must be real same-frame 342x224 Original PPU PAMs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.check_baldosa_wide_slot_final_visibility import (
    WIDTH, HEIGHT, read_pam,
)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def classify(stock: bytes, front: bytes, rear: bytes,
             without_front: bytes, without_pair: bytes, *,
             frame: int, first_slot: int) -> dict:
    if frame < 0 or first_slot not in (96, 98):
        raise ValueError("only exact contiguous front/rear split slots allowed")
    size = WIDTH * HEIGHT * 4
    if any(len(x) != size for x in
           (stock, front, rear, without_front, without_pair)):
        raise ValueError("all real PPU raster planes must be complete 342x224 RGBA")

    counts = dict(front_alpha=0, rear_alpha=0, source_union=0,
                  source_overlap=0, source_equal_rgb_overlap=0,
                  changed_without_front=0, changed_without_pair=0,
                  front_changed_outside_source=0, pair_changed_outside_union=0,
                  same_rgb_overlap_unchanged_without_front=0,
                  redundant_pair_colour_causality=0,
                  unchanged_after_both_removed=0,
                  pair_change_after_front_no_change=0)
    examples = {
        "redundant_pair_colour": [],
        "identical_rear_unchanged_front": [],
        "front_no_change_pair_changed": [],
    }
    for offset in range(0, size, 4):
        fa = front[offset + 3] != 0
        ra = rear[offset + 3] != 0
        same_source_rgb = (fa and ra and
                           front[offset:offset + 3] == rear[offset:offset + 3])
        changed_front = stock[offset:offset + 4] != without_front[offset:offset + 4]
        changed_pair = stock[offset:offset + 4] != without_pair[offset:offset + 4]
        if fa:
            counts["front_alpha"] += 1
        if ra:
            counts["rear_alpha"] += 1
        if fa or ra:
            counts["source_union"] += 1
        if fa and ra:
            counts["source_overlap"] += 1
        if same_source_rgb:
            counts["source_equal_rgb_overlap"] += 1
        if changed_front:
            counts["changed_without_front"] += 1
            if not fa:
                counts["front_changed_outside_source"] += 1
        if changed_pair:
            counts["changed_without_pair"] += 1
            if not (fa or ra):
                counts["pair_changed_outside_union"] += 1
        if fa and ra and not changed_pair:
            counts["unchanged_after_both_removed"] += 1
        if not changed_front and changed_pair:
            counts["pair_change_after_front_no_change"] += 1
        if same_source_rgb and not changed_front:
            counts["same_rgb_overlap_unchanged_without_front"] += 1
        if len(examples["front_no_change_pair_changed"]) < 12 and (
            not changed_front and changed_pair):
            examples["front_no_change_pair_changed"].append(
                [(offset // 4) % WIDTH, (offset // 4) // WIDTH])
        # A particularly informative observation: front-only removal
        # changes NO final colour, although both source planes emitted
        # identical RGB and stock shows that colour. Pair removal DOES
        # change it. Pair-level causal redundancy, NOT unique ownership.
        if (same_source_rgb and not changed_front and changed_pair and
            stock[offset:offset + 3] == front[offset:offset + 3] and
            without_front[offset:offset + 3] == rear[offset:offset + 3]):
            counts["redundant_pair_colour_causality"] += 1
            if len(examples["redundant_pair_colour"]) < 12:
                examples["redundant_pair_colour"].append(
                    [(offset // 4) % WIDTH, (offset // 4) // WIDTH])
        elif same_source_rgb and not changed_front:
            if len(examples["identical_rear_unchanged_front"]) < 12:
                examples["identical_rear_unchanged_front"].append(
                    [(offset // 4) % WIDTH, (offset // 4) // WIDTH])

    return {
        "schema_version": 1,
        "status": "observed" if (
            counts["front_alpha"] > 0 and counts["rear_alpha"] > 0 and
            counts["changed_without_front"] > 0 and
            counts["changed_without_pair"] > 0 and
            counts["front_changed_outside_source"] == 0 and
            counts["pair_changed_outside_union"] == 0
        ) else "unproven",
        "guest_frame": frame,
        "first_oam_slot": first_slot,
        "second_oam_slot": first_slot + 1,
        "pixel_counts": counts,
        "bounded_xy_examples": examples,
        "source_pam_sha256": {
            "stock": _sha(stock), "front": _sha(front),
            "rear": _sha(rear), "without_front": _sha(without_front),
            "without_pair": _sha(without_pair),
        },
        "winner_identity_proven": False,
        "release_hd_admission": False,
        "limits": (
            "Identical front/rear RGB and positive pair-removal delta "
            "are evidence of causal overlapping colour redundancy. They "
            "cannot identify the stock OAM winner, native z/priority, "
            "window colour math or authorize destructive HD OBJ removal."
        ),
    }


def verify_native(stock: bytes, front: bytes, rear: bytes,
                  without_front: bytes, without_pair: bytes,
                  single_report: dict, pair_report: dict, *,
                  frame: int, first_slot: int) -> dict:
    """Reject unauthenticated or inconsistent native report pairings."""
    if first_slot not in (96, 98):
        raise ValueError("front OAM pair must be 96-97 or 98-99")
    common = {
        "stock": _sha(stock), "front": _sha(front), "rear": _sha(rear),
        "without_front": _sha(without_front),
        "without_pair": _sha(without_pair),
    }
    if (single_report.get("status") != "passed" or
        single_report.get("guest_frame") != frame or
        single_report.get("source_oam_slot") != first_slot or
        single_report.get("guest_crc_equal_in_all_three_processes") is not True or
        single_report.get("single_slot_original_ppu_removal_armed") is not True or
        single_report.get("stock_sha256") != common["stock"] or
        single_report.get("source_sha256") != common["front"] or
        single_report.get("counterfactual_sha256") != common["without_front"]):
        raise ValueError("invalid real native single-front-slot provenance")
    if (pair_report.get("status") != "passed" or
        pair_report.get("guest_frame") != frame or
        pair_report.get("removed_oam_slots") != [first_slot, first_slot + 1] or
        pair_report.get("guest_crc_equal_in_all_four_processes") is not True or
        pair_report.get("exact_pair_removal_armed") is not True or
        pair_report.get("stock_sha256") != common["stock"] or
        pair_report.get("first_source_sha256") != common["front"] or
        pair_report.get("second_source_sha256") != common["rear"] or
        pair_report.get("counterfactual_sha256") != common["without_pair"]):
        raise ValueError("invalid real native paired-PPU provenance")
    result = classify(stock, front, rear, without_front,
                      without_pair, frame=frame, first_slot=first_slot)
    c = result["pixel_counts"]
    if (c["front_alpha"] != single_report.get("source_emitted_alpha_pixels") or
        c["changed_without_front"] != single_report.get("native_ppu_final_contributed_pixels") or
        c["front_changed_outside_source"] != single_report.get("native_ppu_changed_outside_emitted_source_alpha") or
        c["source_union"] != pair_report.get("source_alpha_union_pixels") or
        c["source_overlap"] != pair_report.get("source_alpha_pair_overlap_pixels") or
        c["changed_without_pair"] != pair_report.get("final_changed_pixels") or
        c["pair_changed_outside_union"] != pair_report.get("changed_outside_source_union")):
        raise ValueError("correlated native PPU counters do not match authenticated reports")
    result["native_single_and_pair_reports_verified"] = True
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    for opt in ("stock", "front-source", "rear-source",
                "front-removed", "pair-removed",
                "single-report", "pair-report", "out"):
        p.add_argument("--" + opt, type=Path, required=True)
    p.add_argument("--front-slot", type=int, choices=(96, 98), required=True)
    p.add_argument("--frame", type=int, required=True)
    a = p.parse_args()
    original = f"ur-baldosa-ws342-{a.frame:06d}.pam"
    if (a.stock.name != original or
        a.front_removed.name != original or
        a.pair_removed.name != original or
        a.front_source.name !=
            f"ur-baldosa-ws342-obj-slot{a.front_slot}-frame{a.frame:06d}.pam" or
        a.rear_source.name !=
            f"ur-baldosa-ws342-obj-slot{a.front_slot + 1}-frame{a.frame:06d}.pam"):
        p.error("not identical exact native PPU frame/slot names")
    stock, front, rear, front_removed, pair_removed = [
        read_pam(file) for file in (
            a.stock, a.front_source, a.rear_source,
            a.front_removed, a.pair_removed)
    ]
    result = verify_native(
        stock, front, rear, front_removed, pair_removed,
        json.loads(a.single_report.read_text()),
        json.loads(a.pair_report.read_text()),
        frame=a.frame, first_slot=a.front_slot)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    c = result["pixel_counts"]
    print("UR_BALDOSA_WIDE_OVERLAP_CAUSALITY " + result["status"] +
          f" frame={a.frame} slots={a.front_slot}-{a.front_slot + 1}" +
          f" same_rgb={c['source_equal_rgb_overlap']}" +
          f" redundant_pair={c['redundant_pair_colour_causality']}" +
          f" pair_delta={c['changed_without_pair']}" +
          f" outside={c['pair_changed_outside_union']}")
    return 0 if result["status"] == "observed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
