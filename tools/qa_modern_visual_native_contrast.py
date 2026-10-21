#!/usr/bin/env python3
"""Measure source-RGB contrast in an ORIGINAL native SDL P7 frame.

Run on a P7 whose exact successful native ZIP/log/PE was independently
qualified. This is a deliberately narrow pixel oracle, never a simulated
human-aesthetic, alpha-composited monitor or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

P7 = re.compile(rb"\AP7\nWIDTH ([1-9][0-9]*)\nHEIGHT ([1-9][0-9]*)\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
MAX_PIXELS = 3840 * 2160


def unpack_p7(data: bytes) -> tuple[int, int, bytes]:
    header = P7.match(data)
    if not header:
        raise ValueError("not original RGB_ALPHA P7")
    width, height = (int(v) for v in header.groups())
    if width * height > MAX_PIXELS or len(data) - header.end() != width * height * 4:
        raise ValueError("truncated or oversized original P7")
    return width, height, data[header.end():]


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    if len(rgb) != 3 or any(not isinstance(v, int) or not 0 <= v <= 255 for v in rgb):
        raise ValueError("invalid sampled RGB")
    linear = [v / 255 / 12.92 if v / 255 <= .04045
              else ((v / 255 + .055) / 1.055) ** 2.4 for v in rgb]
    return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))


def contrast_ratio(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


def audit_frame(data: bytes, roi: tuple[int, int, int, int],
                foreground: tuple[int, int, int],
                backgrounds: tuple[tuple[int, int, int], ...],
                threshold: float = 4.5) -> dict:
    width, height, rgba = unpack_p7(data)
    left, top, right, bottom = roi
    if (len(roi) != 4 or not 0 <= left < right <= width or
            not 0 <= top < bottom <= height or not backgrounds or
            len(set(backgrounds)) != len(backgrounds) or not 1 <= threshold <= 21):
        raise ValueError("invalid ROI, background palette or reference threshold")
    for rgb in (foreground, *backgrounds):
        relative_luminance(rgb)
    if foreground in backgrounds:
        raise ValueError("foreground equals background sample")
    rect_width = right - left
    rect_height = bottom - top
    # Compare literal raw RGB and retain observed alpha: physical compositing
    # is an entirely separate display/hardware observation.
    samples = []
    for y in range(top, bottom):
        offset = (y * width + left) * 4
        samples.append([tuple(rgba[i:i+4]) for i in range(offset, offset + rect_width * 4, 4)])
    fg_positions = [(x, y) for y in range(rect_height) for x in range(rect_width)
                    if samples[y][x][:3] == foreground]
    background_counts = []
    contrasts = []
    for bg in backgrounds:
        count = sum(px[:3] == bg for row in samples for px in row)
        background_counts.append(count)
        if count:
            contrasts.append(contrast_ratio(foreground, bg))
    if not fg_positions or not all(background_counts):
        raise ValueError("expected text and all backgrounds must be observed inside original P7 ROI")
    adjacency = []
    for bg in backgrounds:
        adjacent = 0
        for x, y in fg_positions:
            if any(samples[yy][xx][:3] == bg
                   for yy in range(max(0, y-2), min(rect_height, y+3))
                   for xx in range(max(0, x-2), min(rect_width, x+3))):
                adjacent += 1
        adjacency.append(adjacent)
    worst = min(contrasts)
    alpha_values = sorted(set(px[3] for row in samples for px in row))
    return {
        "output_pixels": [width, height], "roi": list(roi),
        "original_p7_sha256": hashlib.sha256(data).hexdigest(),
        "foreground_rgb": list(foreground), "foreground_pixels": len(fg_positions),
        "backgrounds": [{"rgb": list(bg), "pixels": count,
                         "contrast_ratio": round(contrast_ratio(foreground, bg), 4),
                         "text_pixels_within_two_pixels": nearby}
                        for bg, count, nearby in zip(backgrounds, background_counts, adjacency)],
        "worst_observed_source_rgb_contrast": round(worst, 4),
        "reference_minimum": threshold,
        "passes_source_rgb_reference": worst >= threshold,
        "alpha_values_observed": alpha_values,
        "physical_monitor_approved": False, "human_visual_approved": False,
        "original_guest_equivalence_approved": False, "release_gate_credit": 0,
        "scope": "uncomposited final SDL P7 source RGB only; not physical display contrast",
    }


def parse_rgb(s: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", s):
        raise argparse.ArgumentTypeError("RGB must be #RRGGBB")
    return tuple(bytes.fromhex(s[1:]))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("p7", type=Path)
    p.add_argument("--roi", nargs=4, type=int, required=True,
                   metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    p.add_argument("--foreground", type=parse_rgb, required=True)
    p.add_argument("--background", type=parse_rgb, action="append", required=True)
    p.add_argument("--reference", type=float, default=4.5)
    p.add_argument("--require-reference", action="store_true")
    args = p.parse_args()
    result = audit_frame(args.p7.read_bytes(), tuple(args.roi), args.foreground,
                         tuple(args.background), args.reference)
    print(json.dumps(result, indent=2))
    return 2 if args.require_reference and not result["passes_source_rgb_reference"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
