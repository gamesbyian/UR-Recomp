#!/usr/bin/env python3
"""Read actual Baldosa 342-wide OBJ slot planes against the Original PPU frame.

At the same guest frame each slot's isolated RGBA emission comes from the
already-pinned PPU. The original main raster is RGBX32: compare RGB bytes,
never treat its unused alpha byte as source visibility. The per-slot isolated
planes report alpha, *before* final BG/window compositing.

This analysis does not paint racers, mutate guest state, reconstruct BG, or
change the approved authored art pipeline. Its output is source attribution
evidence, not automatic HD promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

WIDTH, HEIGHT = 342, 224
ROW_BYTES = WIDTH * 4
HEADER = (
    b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
PAIRS = ((98, 99, "top"), (96, 97, "bottom"))
SOURCE_SLOTS = (96, 97, 98, 99)


def read_native_pam(path: Path) -> bytes:
    content = path.read_bytes()
    if not content.startswith(HEADER) or len(content) != (
            len(HEADER) + ROW_BYTES * HEIGHT):
        raise ValueError(f"Malformed source 342x224 P7 raster: {path}")
    return content[len(HEADER):]


def analyze(main: bytes, slots: dict[int, bytes],
            frame: int, minimum_overlap: int = 1) -> dict:
    if frame < 0:
        raise ValueError("Guest frame must be nonnegative")
    if len(main) != ROW_BYTES * HEIGHT or set(slots) != set(SOURCE_SLOTS) or any(
            len(data) != len(main) for data in slots.values()):
        raise ValueError("Need exact 342x224 Original and four isolated OBJ slots")
    if minimum_overlap < 0:
        raise ValueError("Minimum witness must be nonnegative")
    main_view = memoryview(main)
    source_view = {slot: memoryview(data) for slot, data in slots.items()}
    result = {}
    all_ok = True
    for foremost, behind, viewport in PAIRS:
        lower, upper = source_view[foremost], source_view[behind]
        counts = {
            "front_source_pixels": 0,
            "rear_source_pixels": 0,
            "source_union_pixels": 0,
            "source_overlap_pixels": 0,
            "overlap_different_rgb": 0,
            "overlap_same_rgb_ambiguous": 0,
            "overlap_front_rgb_matches_original": 0,
            "overlap_rear_rgb_matches_original": 0,
            "overlap_neither_rgb_matches_original": 0,
            "solo_source_rgb_matches_original": 0,
            "solo_source_rgb_differs_original": 0,
            "pixels_outside_slot_viewport": 0,
            "solo_source_rgb_differs_coordinates": [],
        }
        y0, y1 = (0, 112) if viewport == "top" else (112, HEIGHT)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                i = (y * WIDTH + x) * 4
                has_front = lower[i + 3] != 0
                has_rear = upper[i + 3] != 0
                if not (has_front or has_rear):
                    continue
                if y < y0 or y >= y1:
                    counts["pixels_outside_slot_viewport"] += 1
                counts["source_union_pixels"] += 1
                counts["front_source_pixels"] += int(has_front)
                counts["rear_source_pixels"] += int(has_rear)
                source_main = main_view[i:i + 3]
                if has_front and has_rear:
                    counts["source_overlap_pixels"] += 1
                    front_rgb = lower[i:i + 3]
                    rear_rgb = upper[i:i + 3]
                    if front_rgb == rear_rgb:
                        counts["overlap_same_rgb_ambiguous"] += 1
                    else:
                        counts["overlap_different_rgb"] += 1
                        if front_rgb == source_main:
                            counts["overlap_front_rgb_matches_original"] += 1
                        elif rear_rgb == source_main:
                            counts["overlap_rear_rgb_matches_original"] += 1
                        else:
                            counts["overlap_neither_rgb_matches_original"] += 1
                else:
                    isolated = lower if has_front else upper
                    if isolated[i:i + 3] == source_main:
                        counts["solo_source_rgb_matches_original"] += 1
                    else:
                        counts["solo_source_rgb_differs_original"] += 1
                        counts["solo_source_rgb_differs_coordinates"].append(
                            [x, y]
                        )
        witnessed = (
            counts["pixels_outside_slot_viewport"] == 0 and
            counts["source_overlap_pixels"] >= minimum_overlap and
            counts["overlap_different_rgb"] >= minimum_overlap and
            counts["overlap_front_rgb_matches_original"] >= minimum_overlap and
            counts["overlap_rear_rgb_matches_original"] == 0
        )
        all_ok = all_ok and witnessed
        result[viewport] = {
            "front_hardware_oam_slot": foremost,
            "rear_hardware_oam_slot": behind,
            "source_emission_priority_witness": witnessed,
            **counts,
        }
    return {
        "schema_version": 1,
        "status": "passed" if all_ok else "unproven",
        "guest_frame": frame,
        "logical_raster": [WIDTH, HEIGHT],
        "main_stock_rgbx32_sha256": hashlib.sha256(main).hexdigest(),
        "stock_alpha_nonzero": sum(
            main[3::4][i] != 0 for i in range(WIDTH * HEIGHT)),
        "source_slot_sha256": {
            str(slot): hashlib.sha256(slots[slot]).hexdigest()
            for slot in SOURCE_SLOTS
        },
        "minimum_overlap": minimum_overlap,
        "top": result["top"],
        "bottom": result["bottom"],
        "limits": (
            "Hardware per-slot source emission and observed RGB tie-break "
            "at one real moving 2P frame; matching RGB alone cannot prove "
            "source visibility where coincident colors or higher-priority "
            "backgrounds are present. Stock main high byte is RGBX, not "
            "RGBA transparency. No authored wide rider or 4K accepted."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original-dir", type=Path, required=True)
    ap.add_argument("--slot-dir", type=Path, required=True)
    ap.add_argument("--frame", type=int, default=1856)
    ap.add_argument("--min-overlap", type=int, default=32)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    base = args.original_dir / (
        f"ur-baldosa-ws342-{args.frame:06d}.pam")
    slots = {
        slot: read_native_pam(args.slot_dir / (
            f"ur-baldosa-ws342-obj-slot{slot}-frame{args.frame:06d}.pam"))
        for slot in SOURCE_SLOTS
    }
    report = analyze(
        read_native_pam(base), slots, args.frame,
        minimum_overlap=args.min_overlap,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(
        f"UR_BALDOSA_WS342_OBJ_DEPTH {report['status']} "
        f"frame={report['guest_frame']} "
        f"top_overlap={report['top']['source_overlap_pixels']} "
        f"bottom_overlap={report['bottom']['source_overlap_pixels']} "
        f"top_front={report['top']['overlap_front_rgb_matches_original']} "
        f"bottom_front={report['bottom']['overlap_front_rgb_matches_original']} "
        f"stock_rgbx_alpha_nonzero={report['stock_alpha_nonzero']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
