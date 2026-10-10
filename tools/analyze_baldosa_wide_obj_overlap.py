#!/usr/bin/env python3
"""Attribute real Baldosa 342-wide racer-source overlap without inventing riders.

Four independently executed pinned PPU captures each isolate exactly one
hardware OAM slot (96..99), with RemoveFromGame disabled. Inspect their
emitted source-alpha masks and compare source RGB with the independently
captured unmodified PPU main raster at the *same guest frame*.

Emitted OBJ pixels are not equivalent to final visible pixels. In particular
a slot can be hidden by another slot, BG/window priority or color processing.
Record all exact witnesses and ambiguities; do not grant HD admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

WIDTH, HEIGHT = 342, 224
SLOTS = (96, 97, 98, 99)
HEADER = (
    b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)


def read_pam(path: Path) -> bytes:
    contents = path.read_bytes()
    if not contents.startswith(HEADER) or len(contents) != (
        len(HEADER) + WIDTH * HEIGHT * 4
    ):
        raise ValueError(f"Invalid P7 342x224 RGBA raster: {path}")
    return contents[len(HEADER):]


def analyze(main: bytes, source: dict[int, bytes], frame: int) -> dict:
    if frame < 0 or set(source) != set(SLOTS):
        raise ValueError("Expect precisely four distinct source OAM slots 96..99")
    expected = WIDTH * HEIGHT * 4
    if len(main) != expected or any(len(v) != expected for v in source.values()):
        raise ValueError("All PPU rasters must be 342x224 with four channels")
    counts = {
        slot: {
            "source_opaque": 0, "source_opaque_top": 0,
            "source_opaque_bottom": 0, "unique_source_pixels": 0,
            "overlap_source_pixels": 0,
            "main_rgb_matches_source": 0,
            "main_rgb_differs_source": 0,
            "unique_main_rgb_matches": 0,
            "unique_main_rgb_differs": 0,
            "overlap_main_rgb_matches": 0,
            "overlap_main_rgb_differs": 0,
        }
        for slot in SLOTS
    }
    overlap_pairs = {
        f"{a}-{b}": 0 for index, a in enumerate(SLOTS)
        for b in SLOTS[index + 1:]
    }
    # For each split band, compare the two genuine overlapping source OBJ
    # colours to the already composed Original RGB. A rear-only match is an
    # observational priority/foreground candidate, never a proven winner.
    # Multi-sprite contamination is counted separately rather than silently
    # interpreted as a clean two-racer witness.
    split_pair_color = {
        name: {
            "front_slot": front, "rear_slot": rear,
            "shared_source_pixels": 0,
            "front_only_matches_original": 0,
            "rear_only_matches_original": 0,
            "both_match_original": 0,
            "neither_matches_original": 0,
            "additional_obj_source_present": 0,
        }
        for name, front, rear in (("top", 98, 99), ("bottom", 96, 97))
    }
    multi_source_pixels = 0
    union_source_pixels = 0
    # RGB equality is only an observational comparison; an unrelated
    # background pixel can coincidentally have the same color.
    for offset in range(0, expected, 4):
        present = [slot for slot in SLOTS if source[slot][offset + 3]]
        if not present:
            continue
        union_source_pixels += 1
        multiple = len(present) > 1
        if multiple:
            multi_source_pixels += 1
        y = (offset // 4) // WIDTH
        final_rgb = main[offset:offset + 3]
        witness = split_pair_color["top" if y < 112 else "bottom"]
        front, rear = witness["front_slot"], witness["rear_slot"]
        if front in present and rear in present:
            witness["shared_source_pixels"] += 1
            if len(present) > 2:
                witness["additional_obj_source_present"] += 1
            front_match = source[front][offset:offset + 3] == final_rgb
            rear_match = source[rear][offset:offset + 3] == final_rgb
            if front_match and rear_match:
                witness["both_match_original"] += 1
            elif front_match:
                witness["front_only_matches_original"] += 1
            elif rear_match:
                witness["rear_only_matches_original"] += 1
            else:
                witness["neither_matches_original"] += 1
        for index, slot in enumerate(present):
            item = counts[slot]
            item["source_opaque"] += 1
            item["source_opaque_top" if y < 112 else "source_opaque_bottom"] += 1
            item["overlap_source_pixels" if multiple else "unique_source_pixels"] += 1
            equal = final_rgb == source[slot][offset:offset + 3]
            item["main_rgb_matches_source" if equal else "main_rgb_differs_source"] += 1
            prefix = "overlap" if multiple else "unique"
            item[f"{prefix}_main_rgb_{'matches' if equal else 'differs'}"] += 1
            for other in present[index + 1:]:
                overlap_pairs[f"{slot}-{other}"] += 1
    all_source_pixels = sum(x["source_opaque"] for x in counts.values())
    overlap_top = overlap_pairs["98-99"]
    overlap_bottom = overlap_pairs["96-97"]
    front_top = counts[98]
    front_bottom = counts[96]
    # This describes the known frame-1856 actual PPU witness, not a
    # generalized claim about SNES priority or arbitrary race geometry.
    stable_witness = (
        overlap_top > 0 and overlap_bottom > 0 and
        front_top["source_opaque_top"] > 0 and
        front_bottom["source_opaque_bottom"] > 0 and
        front_top["main_rgb_differs_source"] == 0 and
        front_bottom["main_rgb_differs_source"] == 0 and
        counts[99]["overlap_main_rgb_differs"] > 0 and
        counts[97]["overlap_main_rgb_differs"] > 0
    )
    return {
        "schema_version": 1,
        "guest_frame": frame,
        "status": "passed" if stable_witness else "unproven",
        "physical_1x_original_raster": [WIDTH, HEIGHT],
        "stock_ppu_sha256": hashlib.sha256(main).hexdigest(),
        "source_obj_sha256": {
            str(slot): hashlib.sha256(source[slot]).hexdigest()
            for slot in SLOTS
        },
        "per_slot": {str(slot): counts[slot] for slot in SLOTS},
        "source_alpha_total_across_slots": all_source_pixels,
        "source_alpha_union_pixels": union_source_pixels,
        "source_alpha_multi_slot_pixels": multi_source_pixels,
        "source_overlap_pairs": overlap_pairs,
        # No equality class proves final ownership; 'neither' may be
        # foreground/window occlusion, colour math or PPU processing.
        "split_pair_final_color_witness": split_pair_color,
        "expected_front_source_color_witness": {
            "top_oam_98_vs_99": front_top["main_rgb_differs_source"] == 0,
            "bottom_oam_96_vs_97": front_bottom["main_rgb_differs_source"] == 0,
            "top_shared_source_pixels": overlap_top,
            "bottom_shared_source_pixels": overlap_bottom,
        },
        "limits": (
            "Pre-foreground PPU emission and final-raster RGB observations. "
            "Color equality is not proof of owner or final visibility; a "
            "nonmatching unique source pixel may be BG/window obscuration. "
            "No authorization for authored wide HD replacement, changed "
            "object priority, or modified guest state."
        ),
    }


def assess(
    main_path: Path, directory: Path, reports: Path, frame: int
) -> dict:
    source = {}
    originals = {}
    for slot in SLOTS:
        path = directory / (
            f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
        source[slot] = read_pam(path)
        evidence = json.loads(
            (reports / (
                f"ws342_obj_slot_{slot}.json" if frame == 1856
                else f"ws342_obj_slot_{slot}_frame{frame}.json"
            )).read_text(
                encoding="utf-8")
        )
        meta = evidence["source"]
        if (
            evidence["status"] != "passed" or
            meta["slot"] != slot or meta["guest_frame"] != frame or
            meta["source_sha256"] != hashlib.sha256(source[slot]).hexdigest()
        ):
            raise ValueError(f"Failed native slot/PAM provenance for {slot}")
        originals[slot] = evidence["source_frame_main_raster_sha256"]
    if len(set(originals.values())) != 1:
        raise ValueError("Different guest main rasters in source-slot routes")
    main = read_pam(main_path)
    if hashlib.sha256(main).hexdigest() != next(iter(originals.values())):
        raise ValueError("Main raster no longer matches the captured guest frame")
    return analyze(main, source, frame)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--main-pam", type=Path, required=True)
    p.add_argument("--slot-dir", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--frame", type=int, default=1856)
    p.add_argument("--record-only", action="store_true",
                   help="Retain exact PPU/provenance observations even when "
                        "this later frame lacks the historic dual-overlap witness")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = assess(a.main_pam, a.slot_dir, a.reports, a.frame)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"UR_BALDOSA_WIDE_OBJ_OVERLAP {result['status']} frame={a.frame} "
        f"total_source={result['source_alpha_total_across_slots']} "
        f"union={result['source_alpha_union_pixels']} "
        f"overlap={result['source_alpha_multi_slot_pixels']} "
        f"top={result['source_overlap_pairs']['98-99']} "
        f"bottom={result['source_overlap_pairs']['96-97']}"
    )
    return 0 if a.record_only or result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
