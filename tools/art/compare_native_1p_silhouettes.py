#!/usr/bin/env python3
"""Compare native original PPU racer alpha geometry, not inferred 3D anatomy.

Sources: independent original PPU isolated slot98/99 342x224 PAMs from an
accepted exact guest frame/report. Align each alpha crop by its own leftmost
source pixel and by actual logical raster Y. Never align independently chosen
poses by eye or derive character-model proportions from a 32px silhouette.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.export_native_racer_obj_source_reference import make_reference
    from tools.check_baldosa_wide_single_slot_source import HEADER, WIDTH, HEIGHT
except ModuleNotFoundError:
    from export_native_racer_obj_source_reference import make_reference
    from check_baldosa_wide_single_slot_source import HEADER, WIDTH, HEIGHT


def _mask_rows(path: Path, bounding_box: list[int], target_width: int) -> list[bytes]:
    raw = path.read_bytes()
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + WIDTH * HEIGHT * 4:
        raise ValueError("native OBJ reference must retain original full PPU RGBA")
    pixels = raw[len(HEADER):]
    left, top, right, bottom = bounding_box
    if not (0 <= left <= right < WIDTH and 0 <= top <= bottom < HEIGHT):
        raise ValueError("native source alpha has invalid source bounds")
    row_width = right - left + 1
    if target_width < row_width:
        raise ValueError("truncated aligned source comparison width")
    out = []
    for y in range(HEIGHT):
        row = bytearray(target_width)
        if top <= y <= bottom:
            for relative_x in range(row_width):
                at = (y * WIDTH + left + relative_x) * 4 + 3
                if pixels[at]:
                    row[relative_x] = 1
        out.append(bytes(row))
    return out


def compare(source98: Path, source99: Path, report: Path) -> dict:
    meta98, png98 = make_reference(source98, report, slot=98)
    meta99, png99 = make_reference(source99, report, slot=99)
    if png98 is None or png99 is None:
        raise ValueError("paired original 1P source-plane silhouette comparison requires both opaque")
    shape98 = meta98.get("original_opaque_silhouette_profile")
    shape99 = meta99.get("original_opaque_silhouette_profile")
    if not shape98 or not shape99:
        raise ValueError("native source shape-profile authority absent")
    left98, top98, right98, bottom98 = meta98["native_original_source_bbox"]
    left99, top99, right99, bottom99 = meta99["native_original_source_bbox"]
    width = max(right98 - left98 + 1, right99 - left99 + 1)
    rows98 = _mask_rows(source98, meta98["native_original_source_bbox"], width)
    rows99 = _mask_rows(source99, meta99["native_original_source_bbox"], width)
    shared_y = range(max(top98, top99), min(bottom98, bottom99) + 1)
    exact = [y for y in shared_y if rows98[y] == rows99[y] and
             any(rows98[y]) and any(rows99[y])]
    longest = []
    current = []
    for y in shared_y:
        if y in exact:
            if current and y != current[-1] + 1:
                if len(current) > len(longest):
                    longest = current
                current = []
            current.append(y)
        elif current:
            if len(current) > len(longest):
                longest = current
            current = []
    if len(current) > len(longest):
        longest = current
    row_match_count = len(exact)
    all_nonempty_overlap_y = [
        y for y in shared_y if any(rows98[y]) and any(rows99[y])]
    return {
        "schema": "UR-QA08-ORIGINAL-1P-SILHOUETTE-COMPARISON/1",
        "native_guest_frame": 2208,
        "status": "exact-original-ppu-source-alpha-comparison",
        "source_original_98_rgba_sha256": meta98["native_original_source_rgba_sha256"],
        "source_original_99_rgba_sha256": meta99["native_original_source_rgba_sha256"],
        "source_98_alpha_sha256": shape98["alpha_mask_sha256"],
        "source_99_alpha_sha256": shape99["alpha_mask_sha256"],
        "original_source_98_bbox": meta98["native_original_source_bbox"],
        "original_source_99_bbox": meta99["native_original_source_bbox"],
        "source_98_projected_crop_size": meta98["cropped_rgba_dimensions"],
        "source_99_projected_crop_size": meta99["cropped_rgba_dimensions"],
        "source_98_opaque_pixels": meta98["native_original_source_opaque_pixels"],
        "source_99_opaque_pixels": meta99["native_original_source_opaque_pixels"],
        "alignment": "left-anchored-independent-native-alpha-bboxes/shared-absolute-raster-Y",
        "logical_pixel_aspect_ratio": "7:6",
        "overlapping_occupied_absolute_source_rows": len(all_nonempty_overlap_y),
        "exactly_matching_source_alpha_rows": row_match_count,
        "longest_contiguous_identical_nonempty_alpha_rows": (
            [longest[0], longest[-1]] if longest else None
        ),
        "longest_identical_row_count": len(longest),
        "all_equal_source_alpha_rows": exact,
        "all_equal_source_alpha_row_count": row_match_count,
        "new_art_approved": False,
        "original_3d_model_or_part_identity_proven": False,
        "final_bg_or_obj_ownership_proven": False,
        "limits": ("Byte-exact alpha silhouette geometry in independently "
                   "source-verified original PPU slot planes, under a "
                   "declared translation only. Similar source rows do not "
                   "prove identical 3D objects, rig hierarchy, anatomical "
                   "parts, camera/lighting, final priority or artwork approval."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source98", type=Path, required=True)
    p.add_argument("--source99", type=Path, required=True)
    p.add_argument("--validated-report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = compare(args.source98, args.source99, args.validated_report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print("UR_QA08_NATIVE_1P_ALPHA_SHAPES exact_shared_rows=" +
          str(result["all_equal_source_alpha_row_count"]) +
          " longest=" + str(result["longest_contiguous_identical_nonempty_alpha_rows"]) +
          " source_3d_approved=0")


if __name__ == "__main__":
    main()
