#!/usr/bin/env python3
"""Observe real native Original 256-center parity inside genuine 342-wide PPU.

Inputs are independent full fixed/wide guest executions at the SAME guest
frame. Their CRC streams and PAM capture identities are mandatory. Deltas
are measured, never hidden or promoted into a release/HD sprite admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from tools.check_baldosa_physical_4k_capture import read_pam
else:
    from check_baldosa_physical_4k_capture import read_pam

FRAME = re.compile(r".+-(\d{6})\.pam\Z")
STOCK_W, WIDE_W, HEIGHT, MARGIN = 256, 342, 224, 43


def assess(fixed: Path, wide: Path, fixed_crc: Path,
           wide_crc: Path, frame: int) -> dict:
    if frame < 0:
        raise ValueError("guest frame must be nonnegative")
    for filename in (fixed.name, wide.name):
        marker = FRAME.fullmatch(filename)
        if marker is None or int(marker[1]) != frame:
            raise ValueError("native images must share the exact guest frame")
    fw, fh, fixed_pixels = read_pam(fixed)
    ww, wh, wide_pixels = read_pam(wide)
    if (fw, fh) != (STOCK_W, HEIGHT) or (ww, wh) != (WIDE_W, HEIGHT):
        raise ValueError("expected genuine native 256x224 and 342x224 PPU")
    original = fixed_crc.read_bytes().splitlines()
    widened = wide_crc.read_bytes().splitlines()
    if len(original) != 2473 or original != widened:
        raise ValueError("missing or divergent complete independent guest CRC")
    rows = {}
    changed_top = changed_bottom = 0
    examples = []
    cropped = bytearray(STOCK_W * HEIGHT * 4)
    for y in range(HEIGHT):
        old_start = y * STOCK_W * 4
        new_start = (y * WIDE_W + MARGIN) * 4
        expected = fixed_pixels[old_start:old_start + STOCK_W * 4]
        actual = wide_pixels[new_start:new_start + STOCK_W * 4]
        cropped[old_start:old_start + STOCK_W * 4] = actual
        if expected == actual:
            continue
        diff = 0
        for x in range(STOCK_W):
            offset = x * 4
            if expected[offset:offset + 4] != actual[offset:offset + 4]:
                diff += 1
                if len(examples) < 20:
                    examples.append({
                        "stock_xy": [x, y], "wide_xy": [x + MARGIN, y],
                        "stock_rgba": expected[offset:offset + 4].hex(),
                        "wide_rgba": actual[offset:offset + 4].hex(),
                    })
        rows[str(y)] = diff
        if y < 112:
            changed_top += diff
        else:
            changed_bottom += diff
    total = changed_top + changed_bottom
    return {
        "schema_version": 1,
        "status": "center-exact" if total == 0 else "center-delta-observed",
        "guest_frame": frame,
        "logical_stock": [STOCK_W, HEIGHT],
        "logical_wide": [WIDE_W, HEIGHT],
        "wide_center_offset": MARGIN,
        "same_complete_guest_crc": True,
        "crc_guest_frames": len(original),
        "stock_native_sha256": hashlib.sha256(fixed_pixels).hexdigest(),
        "wide_native_sha256": hashlib.sha256(wide_pixels).hexdigest(),
        "wide_center_sha256": hashlib.sha256(cropped).hexdigest(),
        "top_center_changed_pixels": changed_top,
        "bottom_center_changed_pixels": changed_bottom,
        "total_center_changed_pixels": total,
        "changed_rows": rows,
        "bounded_pixel_examples": examples,
        "hd_sprite_replacement_admitted": False,
        "release_hud_parity_admitted": False,
        "limits": (
            "This is an independent same-frame native Original center parity "
            "observation, not an authored wide HD source-visibility proof, "
            "menu transition check or gameplay result comparison. Nonzero "
            "deltas require HUD/BG/OBJ/scroll attribution before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed", type=Path, required=True)
    parser.add_argument("--wide", type=Path, required=True)
    parser.add_argument("--fixed-crc", type=Path, required=True)
    parser.add_argument("--wide-crc", type=Path, required=True)
    parser.add_argument("--frame", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.fixed, args.wide, args.fixed_crc, args.wide_crc,
                    args.frame)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_CENTER_PARITY "
          f"frame={args.frame} status={result['status']} "
          f"top={result['top_center_changed_pixels']} "
          f"bottom={result['bottom_center_changed_pixels']} "
          f"total={result['total_center_changed_pixels']}")


if __name__ == "__main__":
    main()
