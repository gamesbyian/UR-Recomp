#!/usr/bin/env python3
"""Strict offline QA oracle for a *real* 3840x2160 Original-mode host capture.

Input consists of same-guest-frame native PPU logical RGBA, its 4x
nearest-density capture, and an independently captured full desktop drawable.
This cannot capture a host or prove that one currently exists. In particular,
a 1368x896 screenshot is *not* evidence of a physical 4K drawable.

The expected 4K frame is the existing Original display contract: full-height
256x224 with 7:6 PAR centered in 16:9, or genuine 342x224 expanded world
with the 512/513 fit filling 16:9. No host overlays or CRT filtering are
allowed in this deliberately strict nearest-only source-raster oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SOURCE_SIZES = {256: (2880, 480), 342: (3840, 0)}
HEIGHT = 224
FOUR_X = 4
OUT_W, OUT_H = 3840, 2160
HEADER = re.compile(
    rb"\AP7\nWIDTH (\d+)\nHEIGHT (\d+)\nDEPTH 4\nMAXVAL 255\n"
    rb"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
SAME_FRAME_NAME = re.compile(r"^.+-(\d{6})\.pam$")


def read_pam(path: Path) -> tuple[int, int, bytes]:
    content = path.read_bytes()
    match = HEADER.match(content)
    if match is None:
        raise ValueError(f"invalid 8-bit RGBA PAM header: {path}")
    width, height = (int(x) for x in match.groups())
    if width <= 0 or height <= 0:
        raise ValueError("nonpositive PNG/PAM image dimensions")
    data = content[match.end():]
    if len(data) != width * height * 4:
        raise ValueError(f"truncated or oversized actual PPU raster: {path}")
    return width, height, data


def check_same_frame(paths: tuple[Path, Path, Path], frame: int) -> None:
    if frame < 0:
        raise ValueError("negative guest frame")
    for path in paths:
        m = SAME_FRAME_NAME.fullmatch(path.name)
        if m is None or int(m[1]) != frame:
            raise ValueError(f"no exact same-frame PAM provenance: {path}")


def nearest_index(position: int, target_extent: int, source_extent: int) -> int:
    # Destination texel-center to source texel-center nearest sampling.
    return min((2 * position + 1) * source_extent //
               (2 * target_extent), source_extent - 1)


def _verify_four_x(logical: bytes, four_x: bytes, width: int) -> None:
    for sy in range(HEIGHT):
        original_row = logical[sy * width * 4:(sy + 1) * width * 4]
        expected_row = b"".join(
            original_row[x * 4:(x + 1) * 4] * FOUR_X
            for x in range(width)
        )
        expected_start = sy * FOUR_X * width * FOUR_X * 4
        for repeat in range(FOUR_X):
            start = expected_start + repeat * width * FOUR_X * 4
            if four_x[start:start + len(expected_row)] != expected_row:
                raise ValueError(
                    f"not an exact native 4x source-density frame: source row {sy}, "
                    f"output repeat {repeat}"
                )


def _verify_physical(logical: bytes, screen: bytes, width: int) -> None:
    output_width, output_x = SOURCE_SIZES[width]
    matte = b"\x00\x00\x00\xff"
    xmap = [nearest_index(x, output_width, width)
            for x in range(output_width)]
    # Cache one source row at a time; the physical 3840x2160 buffer stays
    # original-capture-owned and is never synthesized or silently accepted.
    y_last = -1
    expected_row = b""
    for y in range(OUT_H):
        sy = nearest_index(y, OUT_H, HEIGHT)
        if sy != y_last:
            row = logical[sy * width * 4:(sy + 1) * width * 4]
            projected = b"".join(row[sx * 4:(sx + 1) * 4] for sx in xmap)
            expected_row = matte * output_x + projected + (
                matte * (OUT_W - output_x - output_width))
            y_last = sy
        row_start = y * OUT_W * 4
        actual = screen[row_start:row_start + OUT_W * 4]
        if actual != expected_row:
            # Retain the first exact physical coordinate; a generic
            # mismatched SHA lacks actionable output-sampling context.
            for x in range(OUT_W):
                start = x * 4
                if actual[start:start + 4] != expected_row[start:start + 4]:
                    raise ValueError(
                        f"physical 4K mismatch at ({x},{y}), "
                        f"guest row {sy}, expected={expected_row[start:start+4].hex()} "
                        f"observed={actual[start:start+4].hex()}"
                    )
            raise ValueError(f"physical 4K row mismatch {y}")


def assess(source: Path, density_4x: Path, captured_4k: Path,
           frame: int) -> dict:
    check_same_frame((source, density_4x, captured_4k), frame)
    logical_width, logical_height, src = read_pam(source)
    if logical_width not in SOURCE_SIZES or logical_height != HEIGHT:
        raise ValueError("expected complete 256x224 or genuine 342x224 PPU source")
    density_w, density_h, scaled = read_pam(density_4x)
    if (density_w, density_h) != (logical_width * FOUR_X, HEIGHT * FOUR_X):
        raise ValueError("wrong 4x native presentation dimensions")
    physical_w, physical_h, physical = read_pam(captured_4k)
    if (physical_w, physical_h) != (OUT_W, OUT_H):
        raise ValueError("not a real 3840x2160 host screenshot")
    _verify_four_x(src, scaled, logical_width)
    _verify_physical(src, physical, logical_width)
    output_width, output_x = SOURCE_SIZES[logical_width]
    return {
        "schema_version": 1,
        "status": "exact-native-capture-pixel-parity",
        "frame": frame,
        "source_ppu_size": [logical_width, HEIGHT],
        "native_density_size": [density_w, density_h],
        "physical_capture_size": [physical_w, physical_h],
        "original_pixel_aspect": [7, 6],
        "wide_horizontal_fit": [512, 513] if logical_width == 342 else [1, 1],
        "output_viewport": [output_x, 0, output_width, OUT_H],
        "full_height_224_rows_preserved": True,
        "native_density_and_output_distinct": True,
        "rgba_source_sha256": hashlib.sha256(src).hexdigest(),
        "rgba_density_sha256": hashlib.sha256(scaled).hexdigest(),
        "rgba_capture_sha256": hashlib.sha256(physical).hexdigest(),
        "limits": (
            "Exact same-frame, no-overlays, unfiltered-nearest Original video "
            "raster only. This proves host pixels in a supplied physical capture "
            "match the accepted source/pixel-aspect output projection. It does "
            "not establish that a native host can request that drawable, live "
            "renderer capability, HD art, final depth/priority, original emulator "
            "scene parity, or device/hardware output."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--density-4x", type=Path, required=True)
    ap.add_argument("--physical-4k", type=Path, required=True)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = assess(args.source, args.density_4x,
                    args.physical_4k, args.frame)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("UR_BALDOSA_PHYSICAL_4K_SOURCE_PARITY PASS "
          f"frame={args.frame} logical={result['source_ppu_size']} "
          f"density={result['native_density_size']} "
          f"physical={result['physical_capture_size']} "
          f"viewport={result['output_viewport']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
