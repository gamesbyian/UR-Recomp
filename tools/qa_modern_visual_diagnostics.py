#!/usr/bin/env python3
"""Deterministic geometry/clipping/focus/contrast/multi-resolution diagnostics
for ORIGINAL final-SDL RGB_ALPHA P7 frames of the Modern UI.

Pure measurement of literal framebuffer RGB. Companion of
qa_modern_visual_native_contrast.py (same P7 contract) and of the native
policy in native/product/modern_ui_access.hpp, whose integer scale and
title/action-safe formulas are mirrored here and cross-checked by tests.
Passing is an engineering check, never human art approval, physical monitor
acceptance or original-game parity (every report states so).

Subcommands: contrast, clip, focus, compare (see --help). Every report
carries the input SHA-256 and, with --expect-sha256, refuses a frame whose
bytes differ from the independently qualified artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from tools.qa_modern_visual_native_contrast import (
        contrast_ratio, parse_rgb, unpack_p7)
except ModuleNotFoundError:  # direct CLI invocation
    from qa_modern_visual_native_contrast import (
        contrast_ratio, parse_rgb, unpack_p7)

SCHEMA = "ur-modern-visual-diagnostics-v1"
DISCLAIMER = {
    "physical_monitor_approved": False, "human_visual_approved": False,
    "original_guest_equivalence_approved": False, "release_gate_credit": 0,
    "scope": "uncomposited final SDL P7 source RGB only",
}


class Frame:
    def __init__(self, data: bytes):
        self.sha256 = hashlib.sha256(data).hexdigest()
        self.width, self.height, self.rgba = unpack_p7(data)

    def rgb(self, x: int, y: int) -> tuple[int, int, int]:
        i = (y * self.width + x) * 4
        return (self.rgba[i], self.rgba[i + 1], self.rgba[i + 2])


def load(path: Path, expect_sha256: str | None = None) -> Frame:
    data = path.read_bytes()
    frame = Frame(data)
    if expect_sha256 and frame.sha256 != expect_sha256.lower():
        raise ValueError(f"input sha256 {frame.sha256} != expected {expect_sha256}")
    return frame


def integer_scale(logical_w: int, logical_h: int, out_w: int, out_h: int):
    """Mirror of modern_ui_integer_scale: (factor, x, y, w, h) or None."""
    if (logical_w <= 0 or logical_h <= 0 or out_w < logical_w or
            out_h < logical_h or out_w > 16384 or out_h > 16384):
        return None
    f = min(out_w // logical_w, out_h // logical_h)
    if f < 1:
        return None
    w, h = logical_w * f, logical_h * f
    return f, (out_w - w) // 2, (out_h - h) // 2, w, h


def title_safe(width: int, height: int):
    """Mirror of modern_ui_title_safe: (x, y, w, h) logical, or None."""
    if not (64 <= width <= 16384 and 64 <= height <= 16384):
        return None
    dx, dy = (width * 5 + 99) // 100, (height * 5 + 99) // 100
    ix = max(dx, 8)
    return ix, dy, width - 2 * ix, height - 2 * dy


def action_safe(width: int, height: int):
    if not (64 <= width <= 16384 and 64 <= height <= 16384):
        return None
    dx, dy = (width * 5 + 199) // 200, (height * 5 + 199) // 200
    return dx, dy, width - 2 * dx, height - 2 * dy


def extract_logical(frame: Frame, logical_w: int, logical_h: int) -> dict:
    """Undo integer scaling+letterbox; report non-uniform scale blocks.

    A faithful nearest-neighbour presentation has zero non-uniform blocks, so
    a non-zero count is a filtering/scaling defect (blur, wrong factor).
    """
    s = integer_scale(logical_w, logical_h, frame.width, frame.height)
    if s is None:
        raise ValueError("output cannot hold the logical canvas at integer scale")
    f, vx, vy, _, _ = s
    pixels, bad = [], 0
    for ly in range(logical_h):
        for lx in range(logical_w):
            ref = frame.rgb(vx + lx * f, vy + ly * f)
            pixels.append(ref)
            if any(frame.rgb(vx + lx * f + dx, vy + ly * f + dy) != ref
                   for dy in range(f) for dx in range(f)
                   if (dx or dy) and (dx in (0, f - 1) or dy in (0, f - 1))):
                bad += 1
    return {"factor": f, "viewport": [vx, vy, f * logical_w, f * logical_h],
            "pixels": pixels, "nonuniform_blocks": bad}


def compare_resolutions(a: Frame, b: Frame, logical_w: int, logical_h: int,
                        max_diff: int = 0) -> dict:
    la, lb = (extract_logical(x, logical_w, logical_h) for x in (a, b))
    diff = [i for i, (p, q) in enumerate(zip(la["pixels"], lb["pixels"])) if p != q]
    box = None
    if diff:
        xs, ys = [i % logical_w for i in diff], [i // logical_w for i in diff]
        box = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    return {"schema": SCHEMA, "check": "compare",
            "logical": [logical_w, logical_h],
            "a": {"sha256": a.sha256, "output": [a.width, a.height],
                  "factor": la["factor"], "nonuniform_blocks": la["nonuniform_blocks"]},
            "b": {"sha256": b.sha256, "output": [b.width, b.height],
                  "factor": lb["factor"], "nonuniform_blocks": lb["nonuniform_blocks"]},
            "differing_logical_pixels": len(diff), "difference_bbox": box,
            "pass": (len(diff) <= max_diff and la["nonuniform_blocks"] == 0
                     and lb["nonuniform_blocks"] == 0),
            **DISCLAIMER}


def _rect_check(frame: Frame, roi, name):
    l, t, r, b = roi
    if not (0 <= l < r <= frame.width and 0 <= t < b <= frame.height):
        raise ValueError(f"invalid {name} ROI")


def clip_audit(frame: Frame, logical_w: int, logical_h: int,
               colours: list[tuple[int, int, int]], region: str = "title") -> dict:
    """Bounding box of the given content colours vs the safe region, plus
    content touching the physical framebuffer or viewport edge (clipping)."""
    s = integer_scale(logical_w, logical_h, frame.width, frame.height)
    if s is None:
        raise ValueError("output cannot hold the logical canvas")
    f, vx, vy, vw, vh = s
    safe = (title_safe if region == "title" else action_safe)(logical_w, logical_h)
    wanted = set(colours)
    xs, ys = [], []
    edge_touch = 0
    for y in range(vy, vy + vh):
        for x in range(vx, vx + vw):
            if frame.rgb(x, y) in wanted:
                xs.append(x); ys.append(y)
                if x in (vx, vx + vw - 1) or y in (vy, vy + vh - 1):
                    edge_touch += 1
    if not xs:
        raise ValueError("no pixels of the requested content colours observed")
    box = [(min(xs) - vx) / f, (min(ys) - vy) / f,
           (max(xs) + 1 - vx) / f, (max(ys) + 1 - vy) / f]
    sx, sy, sw, sh = safe
    inside = box[0] >= sx and box[1] >= sy and box[2] <= sx + sw and box[3] <= sy + sh
    return {"schema": SCHEMA, "check": "clip", "input_sha256": frame.sha256,
            "output": [frame.width, frame.height], "logical": [logical_w, logical_h],
            "factor": f, "region": region, "safe_rect": list(safe),
            "content_bbox_logical": box, "content_pixels": len(xs),
            "viewport_edge_pixels": edge_touch,
            "pass": inside and edge_touch == 0, **DISCLAIMER}


def focus_audit(frame: Frame, marker: tuple[int, int, int], scale: int,
                min_logical_width: int = 3, min_height_logical: int = 8) -> dict:
    """Find vertical focus bars: runs of `marker` at least min_logical_width*scale
    wide and min_height_logical*scale tall. Exactly one bar must exist."""
    need_w, need_h = min_logical_width * scale, min_height_logical * scale
    # per-row horizontal runs
    runs = {}
    for y in range(frame.height):
        x = 0
        while x < frame.width:
            if frame.rgb(x, y) == marker:
                x0 = x
                while x < frame.width and frame.rgb(x, y) == marker:
                    x += 1
                if x - x0 >= need_w:
                    runs.setdefault((x0, x - x0), []).append(y)
            else:
                x += 1
    bars = []
    for (x0, w), rows in runs.items():
        rows.sort()
        start = prev = rows[0]
        for y in rows[1:] + [None]:
            if y is None or y != prev + 1:
                if prev - start + 1 >= need_h:
                    bars.append([x0, start, w, prev - start + 1])
                if y is not None:
                    start = y
            if y is not None:
                prev = y
    bars.sort(key=lambda b: (b[1], b[0]))
    return {"schema": SCHEMA, "check": "focus", "input_sha256": frame.sha256,
            "marker_rgb": list(marker), "scale": scale, "bars": bars,
            "pass": len(bars) == 1, **DISCLAIMER}


def local_contrast(frame: Frame, roi, foreground, threshold: float = 4.5,
                   radius: int = 2) -> dict:
    """Per text pixel: contrast against every distinct non-text colour within
    `radius`; reports the worst ratio and the failing pixel fraction."""
    _rect_check(frame, roi, "contrast")
    l, t, r, b = roi
    fg_total = failing = 0
    worst = None
    for y in range(t, b):
        for x in range(l, r):
            if frame.rgb(x, y) != foreground:
                continue
            fg_total += 1
            neigh = {frame.rgb(xx, yy)
                     for yy in range(max(t, y - radius), min(b, y + radius + 1))
                     for xx in range(max(l, x - radius), min(r, x + radius + 1))}
            neigh.discard(foreground)
            if not neigh:
                continue
            low = min(contrast_ratio(foreground, n) for n in neigh)
            worst = low if worst is None else min(worst, low)
            failing += low < threshold
    if not fg_total or worst is None:
        raise ValueError("no text pixel with an adjacent background in ROI")
    return {"schema": SCHEMA, "check": "contrast", "input_sha256": frame.sha256,
            "roi": list(roi), "foreground_rgb": list(foreground),
            "text_pixels": fg_total, "failing_pixels": failing,
            "worst_ratio": round(worst, 4), "reference_minimum": threshold,
            "pass": failing == 0, **DISCLAIMER}


def _emit(report: dict, require: bool) -> int:
    print(json.dumps(report, indent=2))
    return 2 if require and not report["pass"] else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("p7", type=Path)
        sp.add_argument("--expect-sha256")
        sp.add_argument("--require", action="store_true",
                        help="exit 2 when the check fails")

    c = sub.add_parser("contrast"); common(c)
    c.add_argument("--roi", nargs=4, type=int, required=True)
    c.add_argument("--foreground", type=parse_rgb, required=True)
    c.add_argument("--threshold", type=float, default=4.5)
    k = sub.add_parser("clip"); common(k)
    k.add_argument("--logical", nargs=2, type=int, required=True)
    k.add_argument("--colour", type=parse_rgb, action="append", required=True)
    k.add_argument("--region", choices=("title", "action"), default="title")
    f = sub.add_parser("focus"); common(f)
    f.add_argument("--marker", type=parse_rgb, required=True)
    f.add_argument("--scale", type=int, required=True)
    m = sub.add_parser("compare"); common(m)
    m.add_argument("other", type=Path)
    m.add_argument("--other-expect-sha256")
    m.add_argument("--logical", nargs=2, type=int, required=True)
    m.add_argument("--max-diff", type=int, default=0)
    a = p.parse_args(argv)
    try:
        frame = load(a.p7, a.expect_sha256)
        if a.cmd == "contrast":
            rep = local_contrast(frame, tuple(a.roi), a.foreground, a.threshold)
        elif a.cmd == "clip":
            rep = clip_audit(frame, *a.logical, a.colour, a.region)
        elif a.cmd == "focus":
            rep = focus_audit(frame, a.marker, a.scale)
        else:
            rep = compare_resolutions(frame, load(a.other, a.other_expect_sha256),
                                      *a.logical, a.max_diff)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return _emit(rep, a.require)


if __name__ == "__main__":
    raise SystemExit(main())
