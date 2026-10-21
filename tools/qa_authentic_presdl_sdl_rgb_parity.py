#!/usr/bin/env python3
"""Exact RGB continuity check: stock native host pre-SDL P6 -> actual SDL P7.

Validates *every RGB pixel*, including borders, using the pinned 4:3 nearest
pixel-centre projection. Preserves the true zero-alpha SDL3 observation rather
than masking/normalizing it. This is a candidate-specific source-to-SDL
readback check, NEVER a source guest oracle, human, hardware or release pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

P6 = re.compile(rb"\AP6\n([1-9][0-9]*) ([1-9][0-9]*)\n255\n")
P7 = re.compile(rb"\AP7\nWIDTH ([1-9][0-9]*)\nHEIGHT ([1-9][0-9]*)\nDEPTH 4\n"
                rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
MAX_PIXELS = 3840 * 2160


class ParityError(ValueError):
    pass


def raw_raster(path: Path, pattern: re.Pattern[bytes], channels: int):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_PIXELS * 4 + 256:
        raise ParityError("missing/redirected or oversized native raster")
    raw = path.read_bytes()
    m = pattern.match(raw)
    if m is None:
        raise ParityError("wrong native PPM/PAM header or pixel encoding")
    w, h = map(int, m.groups())
    if not (1 <= w <= 3840 and 1 <= h <= 2160 and w * h <= MAX_PIXELS and
            len(raw) == m.end() + w * h * channels):
        raise ParityError("invalid native raster dimensions/trailing bytes")
    return (w, h), memoryview(raw)[m.end():], hashlib.sha256(raw).hexdigest()


def verify(source: Path, drawable: Path) -> dict:
    (sw, sh), p6, source_hash = raw_raster(source, P6, 3)
    (dw, dh), p7, drawable_hash = raw_raster(drawable, P7, 4)
    if (sw, sh) != (256, 224):
        raise ParityError("original native guest source geometry changed")
    if dw * 3 >= dh * 4:
        content_w, content_h = dh * 4 // 3, dh
    else:
        content_w, content_h = dw, dw * 3 // 4
    if (content_w * 3 != content_h * 4 or
            (dw - content_w) % 2 or (dh - content_h) % 2):
        raise ParityError("non-integral/uncentered 4:3 native viewport")
    left, top = (dw - content_w) // 2, (dh - content_h) // 2
    if not any(p6):  # A genuinely black-only guest frame proves no image parity.
        raise ParityError("original native guest image is entirely black")
    nonzero_alpha = 0
    image_pixels = 0
    outside_pixels = 0
    palette = set()
    for y in range(dh):
        inside_y = top <= y < top + content_h
        sy = ((2 * (y - top) + 1) * sh // (2 * content_h)) if inside_y else -1
        for x in range(dw):
            off = 4 * (y * dw + x)
            rgb = bytes(p7[off:off + 3])
            nonzero_alpha += bool(p7[off + 3])
            if inside_y and left <= x < left + content_w:
                sx = (2 * (x - left) + 1) * sw // (2 * content_w)
                expected = bytes(p6[3 * (sy * sw + sx):3 * (sy * sw + sx + 1)])
                if rgb != expected:
                    raise ParityError(f"stock source-to-SDL RGB divergence at {x},{y}")
                palette.add(rgb)
                image_pixels += 1
            else:
                if rgb != b"\x00\x00\x00":
                    raise ParityError(f"nonblack RGB outside authentic source viewport at {x},{y}")
                outside_pixels += 1
    return {
        "schema_version": 1,
        "source_ppm_sha256": source_hash,
        "sdl_pam_sha256": drawable_hash,
        "source_pixels": [sw, sh],
        "drawable_pixels": [dw, dh],
        "authentic_content_viewport": [left, top, content_w, content_h],
        "source_to_sdl_exact_rgb_pixels": image_pixels,
        "outside_black_exact_rgb_pixels": outside_pixels,
        "all_rgb_pixels_checked": dw * dh,
        "rgb_pixel_match_fraction": 1.0,
        "sdl_nonzero_alpha_pixels": nonzero_alpha,
        "original_rgb_palette_colours_visible": len(palette),
        "alpha_warning": "No interpretation of physical display alpha; raw P7 remains immutable",
        "physical_display_approved": False,
        "guest_crc_oracle_approved": False,
        "authentic_final_approved": False,
        "integrated_modern_visual_approved": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_ppm", type=Path)
    p.add_argument("drawable_pam", type=Path)
    p.add_argument("--receipt", type=Path)
    args = p.parse_args()
    try:
        result = verify(args.source_ppm, args.drawable_pam)
        if args.receipt:
            if args.receipt.exists() or args.receipt.is_symlink():
                raise ParityError("source-to-SDL receipt path already exists")
            args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print("AUTHENTIC_NATIVE_RGB_PARITY_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
