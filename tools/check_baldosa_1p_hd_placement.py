#!/usr/bin/env python3
"""Bound actual authored P1 pixels to the original source OAM footprint.

Compare real native 1024x896 host pixels to the read-only 256x224 *post-OBJ
removal* PPU underlay. Only an admitted same-frame source-positive P1 slot
may change its corresponding scanline-112 viewport. This is not original
stock-BG priority certification or permission to widen/remaster.
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

MARK = re.compile(
    r"^UR_BALDOSA_HD_PPU_UNDERLAY frame=(\d+) saved=1 "
    r"logical=256x224 type=post-obj-removal$", re.M)
PRESENT = re.compile(
    r"^UR_RACER_HD_CENSUS frame=(\d+) phase=present status=hd "
    r"reason=p1-only$", re.M)
SOURCE = re.compile(
    r"^UR_RACER_HD_SOURCE_OBJ frame=(\d+) top_opaque=(\d+) "
    r"bottom_opaque=(\d+) top_painted=[01] bottom_painted=[01]$", re.M)
DRAW = re.compile(
    r"^UR_RACER_HD_DRAW PASS frame=(\d+) semantic=([0-9A-F]{4}) "
    r"viewport=(top|bottom) slot=(97|98) x=(-?\d+) y=(\d+) "
    r"hflip=[01] vflip=[01] density=4 output_scale=4 "
    r"guest_state_unchanged=1$", re.M)
PAINT = re.compile(
    r"^UR_BALDOSA_NATIVE_PAINT frame=(\d+) raster=1024x896 "
    r"pitch=4096 top_changed=(\d+) bottom_changed=(\d+)$", re.M)


def in_original_slot(x: int, y: int, slot: tuple[int, int, int],
                     viewport: str) -> bool:
    """SNES 9-bit signed X and 8-bit wrapped Y, split at native scanline 112."""
    signed_x, raw_y, slot_num = slot
    if (viewport == "top") != (y < 112):
        return False
    if slot_num != (98 if viewport == "top" else 97):
        return False
    return signed_x <= x < signed_x + 64 and ((y - raw_y) & 0xFF) < 64


def changed_pixels(source: bytes, output: bytes,
                   placements: dict[str, tuple[int, int, int]],
                   source_opaque: tuple[int, int]) -> tuple[list[int], list[list[int] | None]]:
    if len(source) != 256 * 224 * 4 or len(output) != 1024 * 896 * 4:
        raise ValueError("native 1P placement needs exact post-PPU and real 4x raster")
    counts = [0, 0]
    bboxes: list[list[int] | None] = [None, None]
    src = memoryview(source)
    dst = memoryview(output)
    for y in range(896):
        guest_y = y // 4
        band = int(guest_y >= 112)
        viewport = "bottom" if band else "top"
        for x in range(1024):
            guest_x = x // 4
            base = (guest_y * 256 + guest_x) * 4
            pixel = (y * 1024 + x) * 4
            if src[base:base + 4] == dst[pixel:pixel + 4]:
                continue
            if source_opaque[band] == 0:
                raise ValueError("source-empty P1 viewport acquired authored pixels")
            if not in_original_slot(guest_x, guest_y,
                                    placements[viewport], viewport):
                raise ValueError("authored HD wrote outside its registered source OAM footprint")
            counts[band] += 1
            if bboxes[band] is None:
                bboxes[band] = [x, y, x, y]
            else:
                rect = bboxes[band]
                rect[0], rect[1] = min(rect[0], x), min(rect[1], y)
                rect[2], rect[3] = max(rect[2], x), max(rect[3], y)
    return counts, bboxes


def assess(captures: Path, log_path: Path, coverage_path: Path) -> dict:
    txt = log_path.read_text(encoding="utf-8", errors="replace")
    # The pinned native first-party P1_ONLY diagnostic prints a *literal*
    # backslash-n immediately before its first DRAW PASS. It does NOT print
    # an actual line break there. Accept precisely that known split while
    # preserving every field, rather than silently dropping top slot 98.
    txt = txt.replace(r"\nUR_RACER_HD_DRAW PASS ", "\nUR_RACER_HD_DRAW PASS ")
    frames = [int(f) for f in MARK.findall(txt)]
    if not frames or len(frames) != len(set(frames)):
        raise ValueError("missing or duplicate real native underlay witnesses")
    hd = [int(f) for f in PRESENT.findall(txt)]
    alpha = {int(f): (int(t), int(b)) for f, t, b in SOURCE.findall(txt)}
    paint = {int(f): (int(t), int(b)) for f, t, b in PAINT.findall(txt)}
    draw: dict[int, dict[str, tuple[int, int, int]]] = {}
    for frame, semantic, viewport, slot, x, y in DRAW.findall(txt):
        f = int(frame)
        place = (int(x), int(y), int(slot))
        if viewport in draw.setdefault(f, {}):
            raise ValueError("duplicate same-frame 1P OAM placement")
        if not (0 <= int(y) <= 255) or not (-256 <= int(x) < 256):
            raise ValueError("invalid native SNES sprite placement")
        draw[f][viewport] = place
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    approved = set(coverage.get("verified_4x_p1_visible_image_frames", []))
    if coverage.get("native_guest_crc_equal") != 5447 or (
        coverage.get("unsafe_fixture_used") is not False
    ) or coverage.get("widescreen_hd_approved") is not False:
        raise ValueError("independent source-positive 1P guest CRC/safety report absent")
    if not set(frames) <= approved:
        raise ValueError("PPU capture frame not corroborated by native 1P guest/PAM report")
    output = []
    for frame in sorted(frames):
        if not 1700 <= frame < 1800 or hd.count(frame) != 1:
            raise ValueError("unadmitted 1P source/host frame")
        poses = draw.get(frame, {})
        if set(poses) != {"top", "bottom"} or (
            poses["top"][2] != 98 or poses["bottom"][2] != 97
        ):
            raise ValueError("missing canonical same-frame split P1 OBJ 98/97 placements")
        if frame not in alpha or frame not in paint:
            raise ValueError("missing authoritative native 1P PPU source or changed-pixel counters")
        un = captures / f"ur-baldosa-hd-postcapture-underlay-{frame:06d}.pam"
        hd_path = captures / f"ur-baldosa-frame-{frame:06d}.pam"
        if not un.is_file() or not hd_path.is_file():
            raise ValueError("missing actual paired native PPU/HD source pixels")
        sw, sh, raw = read_pam(un)
        w, h, pixels = read_pam(hd_path)
        if (sw, sh, w, h) != (256, 224, 1024, 896):
            raise ValueError("native P1 PPU/HD dimensions are wrong")
        counts, boxes = changed_pixels(raw, pixels, poses, alpha[frame])
        if tuple(counts) != paint[frame]:
            raise ValueError("real source-local authored pixel totals disagree with native host")
        if not sum(counts):
            raise ValueError("native retained P1 HD frame had no changed authored pixel")
        output.append({
            "guest_frame": frame,
            "semantic_registrations": "source-derived-original-PPU",
            "p1_top_slot": poses["top"],
            "p1_bottom_slot": poses["bottom"],
            "source_obj_opaque_top_bottom": list(alpha[frame]),
            "actual_changed_top_bottom": counts,
            "changed_native_4x_bbox_top": boxes[0],
            "changed_native_4x_bbox_bottom": boxes[1],
            "all_changed_pixels_within_source_oam_footprints": True,
            "underlay_sha256": hashlib.sha256(raw).hexdigest(),
            "authored_4x_sha256": hashlib.sha256(pixels).hexdigest(),
        })
    return {
        "schema_version": 1,
        "status": "native-fixed-1p-authored-source-footprint-contained",
        "frames": output,
        "original_final_bg_priority_accepted": False,
        "wide_hd_accepted": False,
        "release_accepted": False,
        "limitations": (
            "The underlay is post-original-OBJ removal; this rejects "
            "nonlocal host edits using the native OAM split, but does NOT "
            "prove original PPU final-composite priority, authentic racer "
            "animation, sustained race visibility or 342-wide Remastered."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--coverage", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = assess(args.captures, args.log, args.coverage)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_1P_SOURCE_FOOTPRINT "
          f"status={result['status']} frames={len(result['frames'])}")


if __name__ == "__main__":
    main()
