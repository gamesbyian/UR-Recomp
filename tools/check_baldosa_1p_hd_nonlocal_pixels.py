#!/usr/bin/env python3
"""Compare real 1P 4x Remastered output with its native post-OBJ PPU underlay.

The underlay is AFTER the PPU removed the source racer OBJ. It is never an
independent Original-game stock witness. Exact source-empty band preservation
guards against a phantom or nonlocal HD paint on an actual native guest frame.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.check_baldosa_physical_4k_capture import read_pam
except ModuleNotFoundError:
    from check_baldosa_physical_4k_capture import read_pam

UNDERLAY = re.compile(
    r"^ur-baldosa-hd-postcapture-underlay-(\d{6})\.pam$"
)
HD_FILE = "ur-baldosa-frame-{frame:06d}.pam"
MARK = re.compile(
    r"^UR_BALDOSA_HD_PPU_UNDERLAY frame=(\d+) saved=1 "
    r"logical=256x224 type=post-obj-removal$", re.M
)
SOURCE = re.compile(
    r"^UR_RACER_HD_SOURCE_OBJ frame=(\d+) top_opaque=(\d+) "
    r"bottom_opaque=(\d+) top_painted=[01] bottom_painted=[01]$", re.M
)
PAINT = re.compile(
    r"^UR_BALDOSA_NATIVE_PAINT frame=(\d+) raster=1024x896 pitch=(\d+) "
    r"top_changed=(\d+) bottom_changed=(\d+)$", re.M
)
HD_PRESENT = re.compile(
    r"^UR_RACER_HD_CENSUS frame=(\d+) phase=present "
    r"status=hd reason=p1-only$", re.M
)


def differing_bands(underlay: bytes, image: bytes) -> tuple[int, int]:
    if len(underlay) != 256 * 224 * 4 or len(image) != 1024 * 896 * 4:
        raise ValueError("invalid raw P1 PPU/HD capture dimensions")
    counts = [0, 0]
    for y in range(896):
        band = 0 if y < 448 else 1
        original_row = (y // 4) * 256 * 4
        image_row = y * 1024 * 4
        for x in range(1024):
            src = original_row + (x // 4) * 4
            dst = image_row + x * 4
            if underlay[src:src + 4] != image[dst:dst + 4]:
                counts[band] += 1
    return counts[0], counts[1]


def assess(directory: Path, log_path: Path) -> dict:
    log = log_path.read_text(encoding="utf-8", errors="replace")
    marks = [int(f) for f in MARK.findall(log)]
    actual_source = {int(f): (int(t), int(b))
                     for f, t, b in SOURCE.findall(log)}
    paints = {int(f): (int(pitch), int(t), int(b))
              for f, pitch, t, b in PAINT.findall(log)}
    hd = {int(f) for f in HD_PRESENT.findall(log)}
    if not marks or len(marks) != len(set(marks)):
        raise ValueError("no unique real native early post-removal PPU underlay evidence")
    retained = []
    for frame in sorted(marks):
        if not 1700 <= frame < 1800 or frame not in hd:
            raise ValueError("unsafe early 1P native source window or absent actual HD present")
        base = directory / f"ur-baldosa-hd-postcapture-underlay-{frame:06d}.pam"
        dest = directory / HD_FILE.format(frame=frame)
        if not base.exists() or not dest.exists():
            raise ValueError("native frame lacks exact matching source/HD screenshot pair")
        source_w, source_h, source = read_pam(base)
        width, height, output = read_pam(dest)
        if (source_w, source_h) != (256, 224) or (width, height) != (1024, 896):
            raise ValueError("source/dense native dimensions are incompatible")
        top, bottom = differing_bands(source, output)
        if frame not in paints or paints[frame] != (4096, top, bottom):
            raise ValueError("native authored-pixel report differs from actual captured raster")
        if frame not in actual_source:
            raise ValueError("missing original-native PPU source OBJ witness")
        top_opaque, bottom_opaque = actual_source[frame]
        if (top and not top_opaque) or (bottom and not bottom_opaque):
            raise ValueError("source-absent viewport acquired a phantom Remastered rider")
        retained.append({
            "guest_frame": frame,
            "actual_source_opaque_top": top_opaque,
            "actual_source_opaque_bottom": bottom_opaque,
            "top_hd_changed_pixels": top,
            "bottom_hd_changed_pixels": bottom,
            "source_empty_bands_preserved": True,
            "underlay_sha256": hashlib.sha256(source).hexdigest(),
            "native_4x_hd_sha256": hashlib.sha256(output).hexdigest(),
            "ppu_underlay_type": "post-obj-removal",
        })
    if {int(m[1]) for m in map(UNDERLAY.fullmatch,
             (p.name for p in directory.glob("ur-baldosa-hd-postcapture-underlay-*.pam")))
        if m} != set(marks):
        raise ValueError("unaccounted original-PPU removal source frame on disk")
    return {
        "schema_version": 1,
        "status": ("observed-guarded-1p-source-positive-hd" if
                   any(x["top_hd_changed_pixels"] or x["bottom_hd_changed_pixels"]
                       for x in retained)
                   else "observed-guarded-1p-source-empty"),
        "native_early_frame_pairs": retained,
        "authored_wide_hd_admitted": False,
        "original_stock_priority_proven": False,
        "product_beta_approved": False,
        "limits": (
            "Genuine native safe fixed-256 P1-only post-OBJ-removal underlay "
            "and actual 4x host output. A source-empty viewport cannot acquire "
            "authored pixels, but this does not prove full original BG/window "
            "foreground parity, sustained animation, 342-wide HD or Windows beta."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--captures", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    report = assess(a.captures, a.log)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_1P_HD_SOURCE_EMPTY_GUARD "
          f"status={report['status']} "
          f"native_pairs={len(report['native_early_frame_pairs'])} "
          "wide_hd_admitted=0")


if __name__ == "__main__":
    main()
