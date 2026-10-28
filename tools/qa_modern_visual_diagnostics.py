#!/usr/bin/env python3
"""Deterministic geometry/clipping/focus/contrast/multi-resolution diagnostics
for ORIGINAL final-SDL RGB_ALPHA P7 frames of the Modern UI.

Pure measurement of literal framebuffer RGB. Companion of
qa_modern_visual_native_contrast.py (same P7 contract) and of the native
policy in native/product/modern_ui_access.hpp, whose integer scale and
title/action-safe formulas are mirrored here and cross-checked by tests.
Passing is an engineering check, never human art approval, physical monitor
acceptance or original-game parity (every report states so).

Output mapping: the shipped final-SDL path fits the logical canvas into the
window with the 7:6 original pixel aspect and nearest-neighbour sampling, so
blocks are fractional (e.g. 342x224 -> 1280x720 is ~3.74 x ~3.21 px per
logical pixel), NOT an integer multiple. `--mode fit` (default, `--par 7/6`)
models that; `--mode integer` models whole-number density with letterbox.
Measured against a real committed native capture: the true logical width
shows 0% non-uniform block interiors, a wrong width several percent.

Subcommands: contrast, clip, focus, compare, detect (see --help). Every report
carries the input SHA-256 and, with --expect-sha256, refuses a frame whose
bytes differ from the independently qualified artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

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


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PIXELS = 3840 * 2160


def unpack_png(data: bytes) -> tuple[int, int, bytes]:
    """Strict 8-bit RGB/RGBA non-interlaced PNG -> RGBA bytes (no colour
    management, gamma or resampling; anything else is refused)."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG")
    pos, ihdr, idat = len(PNG_SIGNATURE), None, []
    while pos + 8 <= len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length or pos + 12 + length > len(data):
            raise ValueError("truncated PNG chunk")
        if zlib.crc32(tag + body) != struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]:
            raise ValueError("PNG chunk CRC mismatch")
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat.append(body)
        elif tag == b"IEND":
            break
        pos += 12 + length
    if ihdr is None or not idat:
        raise ValueError("PNG missing IHDR or IDAT")
    width, height, depth, ctype, _, _, interlace = ihdr
    if depth != 8 or ctype not in (2, 6) or interlace:
        raise ValueError("only 8-bit non-interlaced RGB/RGBA PNG supported")
    if not (0 < width * height <= MAX_PIXELS):
        raise ValueError("PNG dimensions out of range")
    bpp = 3 if ctype == 2 else 4
    stride = width * bpp
    raw = zlib.decompress(b"".join(idat))
    if len(raw) != height * (stride + 1):
        raise ValueError("PNG scanline data length mismatch")
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    for y in range(height):
        base = y * (stride + 1)
        ft, line = raw[base], bytearray(raw[base + 1:base + 1 + stride])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 0:
                pred = 0
            elif ft == 1:
                pred = a
            elif ft == 2:
                pred = b
            elif ft == 3:
                pred = (a + b) >> 1
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            else:
                raise ValueError("bad PNG filter")
            line[i] = (line[i] + pred) & 255
        for x in range(width):
            o = (y * width + x) * 4
            out[o:o + 3] = line[x * bpp:x * bpp + 3]
            out[o + 3] = line[x * bpp + 3] if bpp == 4 else 255
        prev = line
    return width, height, bytes(out)


class Frame:
    def __init__(self, data: bytes):
        self.sha256 = hashlib.sha256(data).hexdigest()
        if data.startswith(PNG_SIGNATURE):
            self.width, self.height, self.rgba = unpack_png(data)
        else:
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


PAR_DEFAULT = 7 / 6


class Mapping:
    """Logical canvas -> output pixels (sx,sy px per logical pixel; vx,vy origin)."""

    def __init__(self, sx, sy, vx, vy, lw, lh, mode):
        self.sx, self.sy, self.vx, self.vy = sx, sy, vx, vy
        self.lw, self.lh, self.mode = lw, lh, mode

    def rect(self):
        return (self.vx, self.vy, self.lw * self.sx, self.lh * self.sy)

    def logical_x(self, x):
        return (x + 0.5 - self.vx) / self.sx

    def logical_y(self, y):
        return (y + 0.5 - self.vy) / self.sy


def mapping(lw: int, lh: int, out_w: int, out_h: int,
            mode: str = "fit", par: float = PAR_DEFAULT) -> Mapping:
    if lw <= 0 or lh <= 0 or out_w < lw or out_h < lh or out_w > 16384 or out_h > 16384:
        raise ValueError("output cannot hold the logical canvas")
    if mode == "integer":
        s = integer_scale(lw, lh, out_w, out_h)
        if s is None:
            raise ValueError("output cannot hold the logical canvas at integer scale")
        f, vx, vy, _, _ = s
        return Mapping(f, f, vx, vy, lw, lh, mode)
    if mode != "fit" or not 0.5 <= par <= 2.0:
        raise ValueError("unknown mapping mode or pixel aspect")
    s = min(out_w / (lw * par), out_h / lh)
    sx, sy = s * par, s
    return Mapping(sx, sy, (out_w - lw * sx) / 2, (out_h - lh * sy) / 2, lw, lh, mode)


def _sample(frame, m, lx, ly, a, b):
    x = min(frame.width - 1, max(0, int(m.vx + (lx + a) * m.sx)))
    y = min(frame.height - 1, max(0, int(m.vy + (ly + b) * m.sy)))
    return frame.rgb(x, y)


def extract_logical(frame: Frame, logical_w: int, logical_h: int,
                    mode: str = "fit", par: float = PAR_DEFAULT,
                    phase_x: float = 0.0) -> dict:
    """Undo the output mapping; report blocks whose interior is not uniform.

    Each logical pixel is read at its centre; its block interior (25%-75%)
    must be one colour for a faithful nearest-neighbour presentation, so a
    non-zero fraction means filtering, a wrong logical width or a stale scale.
    Block edges are excluded: SDL's rounding of the fractional boundary is
    not part of the contract.
    """
    m = mapping(logical_w, logical_h, frame.width, frame.height, mode, par)
    # SDL can snap a fractional horizontal viewport origin to an integer.
    # Phase is a bounded diagnostic correction, never a renderer change.
    m.vx += phase_x
    W, H, buf = frame.width, frame.height, frame.rgba
    clampx = lambda v: min(W - 1, max(0, int(v)))
    clampy = lambda v: min(H - 1, max(0, int(v)))
    # Byte offsets of the centre and the four interior sample columns/rows.
    xs = [[clampx(m.vx + (lx + a) * m.sx) * 4 for a in (0.5, 0.25, 0.75)]
          for lx in range(logical_w)]
    ys = [[clampy(m.vy + (ly + b) * m.sy) * W * 4 for b in (0.5, 0.25, 0.75)]
          for ly in range(logical_h)]
    pixels, bad = [], 0
    for ly in range(logical_h):
        yc, y0, y1 = ys[ly]
        for lx in range(logical_w):
            xc, x0, x1 = xs[lx]
            o = yc + xc
            ref = buf[o:o + 3]
            pixels.append((ref[0], ref[1], ref[2]))
            if (buf[y0 + x0:y0 + x0 + 3] != ref or buf[y0 + x1:y0 + x1 + 3] != ref
                    or buf[y1 + x0:y1 + x0 + 3] != ref
                    or buf[y1 + x1:y1 + x1 + 3] != ref):
                bad += 1
    total = logical_w * logical_h
    return {"mode": mode, "scale": [m.sx, m.sy],
            "viewport": [m.vx, m.vy, logical_w * m.sx, logical_h * m.sy],
            "pixels": pixels, "nonuniform_blocks": bad,
            "nonuniform_fraction": bad / total}


def _outside_viewport_nonblack(frame: Frame, m: Mapping) -> int:
    """Count RGB content outside a candidate nearest-neighbour viewport.

    Sampling at output pixel centres matches the production fit contract.
    A 256-column fit in an 856px window has 108px sidebars; a real 342-wide
    root with visible content there cannot be explained as 256 columns.
    Alpha is intentionally ignored, matching the RGB diagnostic contract.
    """
    def bounds(origin, span, limit):
        return (max(0, min(limit, math.ceil(origin - 0.5))),
                max(0, min(limit, math.ceil(origin + span - 0.5))))

    left, right = bounds(m.vx, m.lw * m.sx, frame.width)
    top, bottom = bounds(m.vy, m.lh * m.sy, frame.height)
    buf, width, height = frame.rgba, frame.width, frame.height
    count = 0
    for y in range(height):
        spans = ((0, left), (right, width)) if top <= y < bottom else ((0, width),)
        for x0, x1 in spans:
            for p in range((y * width + x0) * 4, (y * width + x1) * 4, 4):
                if buf[p] or buf[p + 1] or buf[p + 2]:
                    count += 1
    return count


def detect_logical(frame: Frame, widths=(256, 342), logical_h: int = 224,
                   mode: str = "fit", par: float = PAR_DEFAULT,
                   tolerance: float = 0.002, margin: float = 0.0005) -> dict:
    """Find a uniquely supported source width without trusting a host marker.

    At fractional fit origins SDL may snap the viewport by <=1 output pixel.
    Only if the ordinary diagnostic is inconclusive do we test those integer
    snaps. A phase match must ALSO have black pixels outside its predicted
    viewport. Widths with identical pixel pitch and no distinguishing edge
    content remain ambiguous rather than earning a false acceptance.
    """
    fractions = {}
    phases = {}
    for w in widths:
        try:
            fractions[w] = extract_logical(frame, w, logical_h, mode, par)[
                "nonuniform_fraction"]
            phases[w] = 0.0
        except ValueError:
            fractions[w] = None
    scored = {w: v for w, v in fractions.items() if v is not None}

    def candidates():
        best = min(scored.values()) if scored else None
        return ([w for w, v in scored.items()
                 if v <= tolerance and v <= best + margin] if best is not None
                else [])

    ok = candidates()
    outside = {}
    if len(ok) != 1 and mode == "fit":
        for w in scored:
            try:
                m = mapping(w, logical_h, frame.width, frame.height, mode, par)
            except ValueError:
                continue
            # Consider both integer snaps, never arbitrary phase fitting.
            shifts = {math.floor(m.vx) - m.vx, math.ceil(m.vx) - m.vx}
            for shift in sorted(shifts):
                if abs(shift) < 1e-9:
                    continue
                score = extract_logical(frame, w, logical_h, mode, par,
                                        phase_x=shift)["nonuniform_fraction"]
                if score < scored[w]:
                    scored[w] = fractions[w] = score
                    phases[w] = shift
        ok = candidates()
    # Even an unshifted, uniquely uniform candidate must not claim a 256px
    # source when the supposed letterbox contains actual guest RGB content.
    # Black/flat frames can still leave both widths ambiguous.
    if mode == "fit":
        for w in ok:
            try:
                m = mapping(w, logical_h, frame.width, frame.height, mode, par)
            except ValueError:
                continue
            m.vx += phases[w]
            outside[w] = _outside_viewport_nonblack(frame, m)
        ok = [w for w in ok if outside.get(w, 0) == 0]
    return {"schema": SCHEMA, "check": "detect", "input_sha256": frame.sha256,
            "output": [frame.width, frame.height], "mode": mode,
            "nonuniform_fraction": fractions, "phase_x": phases,
            "outside_viewport_nonblack": outside,
            "consistent_widths": ok,
            "pass": len(ok) == 1, **DISCLAIMER}


EXPLAIN_WIDTHS = (256, 292, 298, 304, 320, 342, 352, 384)
EXPLAIN_PARS = (7 / 6, 1.0, 8 / 7, 4 / 3 * 224 / 256)


def explain_mapping(frame: Frame, widths=EXPLAIN_WIDTHS, pars=EXPLAIN_PARS,
                    logical_h: int = 224, top: int = 5) -> list[dict]:
    """Diagnostic for a frame no standard canvas explains: score a wider grid
    of logical widths and pixel aspects (fractional fit) plus integer-density
    mappings, best first. A near-zero score means the frame IS a nearest-scaled
    canvas of that shape, so the standard check used the wrong assumption; if
    nothing scores well the frame is not a clean nearest-scaled logical canvas
    at all (filtered art, a mid-transition frame, or a different pipeline)."""
    results = []
    for w in widths:
        for par in pars:
            try:
                frac = extract_logical(frame, w, logical_h, "fit", par)[
                    "nonuniform_fraction"]
            except ValueError:
                continue
            results.append({"logical_width": w, "mode": "fit",
                            "par": round(par, 4), "nonuniform_fraction": frac})
        try:
            frac = extract_logical(frame, w, logical_h, "integer")[
                "nonuniform_fraction"]
            results.append({"logical_width": w, "mode": "integer", "par": 1.0,
                            "nonuniform_fraction": frac})
        except ValueError:
            pass
    results.sort(key=lambda r: r["nonuniform_fraction"])
    return results[:top]


def compare_resolutions(a: Frame, b: Frame, logical_w: int, logical_h: int,
                        max_diff: int = 0, mode: str = "fit",
                        par: float = PAR_DEFAULT,
                        max_nonuniform: float = 0.002) -> dict:
    la, lb = (extract_logical(x, logical_w, logical_h, mode, par) for x in (a, b))
    diff = [i for i, (p, q) in enumerate(zip(la["pixels"], lb["pixels"])) if p != q]
    box = None
    if diff:
        xs, ys = [i % logical_w for i in diff], [i // logical_w for i in diff]
        box = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    side = lambda fr, lg: {"sha256": fr.sha256, "output": [fr.width, fr.height],
                           "scale": lg["scale"],
                           "nonuniform_fraction": lg["nonuniform_fraction"]}
    return {"schema": SCHEMA, "check": "compare", "mode": mode,
            "logical": [logical_w, logical_h],
            "a": side(a, la), "b": side(b, lb),
            "differing_logical_pixels": len(diff), "difference_bbox": box,
            "pass": (len(diff) <= max_diff and
                     la["nonuniform_fraction"] <= max_nonuniform and
                     lb["nonuniform_fraction"] <= max_nonuniform),
            **DISCLAIMER}


def encode_png(width: int, height: int, rgb_rows: list[bytes]) -> bytes:
    """Minimal 8-bit RGB PNG (filter 0) from packed rows; stdlib only."""
    def chunk(tag: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + tag + body +
                struct.pack(">I", zlib.crc32(tag + body)))
    raw = b"".join(b"\x00" + row for row in rgb_rows)
    return (PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                                      8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def diff_png(a: Frame, b: Frame, logical_w: int, logical_h: int,
             mode: str = "fit", par: float = PAR_DEFAULT, zoom: int = 3) -> bytes:
    """Logical-canvas difference picture for reviewers: unchanged pixels are
    dimmed grayscale of A, differing logical pixels are solid red. The exact
    set and its bounding box are in compare_resolutions(); this is only the
    picture a reviewer can open from a CI artifact."""
    la = extract_logical(a, logical_w, logical_h, mode, par)["pixels"]
    lb = extract_logical(b, logical_w, logical_h, mode, par)["pixels"]
    rows = []
    for y in range(logical_h):
        row = bytearray()
        for x in range(logical_w):
            pa, pb = la[y * logical_w + x], lb[y * logical_w + x]
            if pa != pb:
                px = bytes((255, 0, 0))
            else:
                g = (pa[0] * 30 + pa[1] * 59 + pa[2] * 11) // 100 // 3 + 40
                px = bytes((g, g, g))
            row += px * zoom
        rows += [bytes(row)] * zoom
    return encode_png(logical_w * zoom, logical_h * zoom, rows)


def _rect_check(frame: Frame, roi, name):
    l, t, r, b = roi
    if not (0 <= l < r <= frame.width and 0 <= t < b <= frame.height):
        raise ValueError(f"invalid {name} ROI")


def clip_audit(frame: Frame, logical_w: int, logical_h: int,
               colours: list[tuple[int, int, int]], region: str = "title",
               mode: str = "fit", par: float = PAR_DEFAULT) -> dict:
    """Bounding box of the given content colours vs the safe region, plus
    content touching the physical framebuffer or viewport edge (clipping)."""
    m = mapping(logical_w, logical_h, frame.width, frame.height, mode, par)
    safe = (title_safe if region == "title" else action_safe)(logical_w, logical_h)
    wanted = set(colours)
    vx, vy, vw, vh = m.rect()
    x0, x1 = max(0, int(vx + 0.999)), min(frame.width, int(vx + vw + 0.001))
    y0, y1 = max(0, int(vy + 0.999)), min(frame.height, int(vy + vh + 0.001))
    xs, ys = [], []
    edge_touch = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            if frame.rgb(x, y) in wanted:
                xs.append(x); ys.append(y)
                if x in (x0, x1 - 1) or y in (y0, y1 - 1):
                    edge_touch += 1
    if not xs:
        raise ValueError("no pixels of the requested content colours observed")
    box = [(min(xs) - m.vx) / m.sx, (min(ys) - m.vy) / m.sy,
           (max(xs) + 1 - m.vx) / m.sx, (max(ys) + 1 - m.vy) / m.sy]
    # Fractional block boundaries are good to about one output pixel.
    tx, ty = 1 / m.sx, 1 / m.sy
    sx, sy, sw, sh = safe
    inside = (box[0] >= sx - tx and box[1] >= sy - ty and
              box[2] <= sx + sw + tx and box[3] <= sy + sh + ty)
    return {"schema": SCHEMA, "check": "clip", "input_sha256": frame.sha256,
            "output": [frame.width, frame.height], "logical": [logical_w, logical_h],
            "mode": mode, "scale": [m.sx, m.sy], "region": region,
            "safe_rect": list(safe), "content_bbox_logical": box,
            "content_pixels": len(xs), "viewport_edge_pixels": edge_touch,
            "pass": inside and edge_touch == 0, **DISCLAIMER}


def focus_audit(frame: Frame, marker: tuple[int, int, int], scale: float,
                min_logical_width: int = 3, min_height_logical: int = 8,
                scale_y: float | None = None) -> dict:
    """Find vertical focus bars: runs of `marker` at least min_logical_width*scale
    wide and min_height_logical*scale tall. Exactly one bar must exist."""
    sy_ = scale if scale_y is None else scale_y
    # Fractional block edges lose up to one output pixel; at 1:1 no slack.
    slack = lambda sc: 1 if sc > 1.5 else 0
    need_w = max(1, int(min_logical_width * scale) - slack(scale))
    need_h = max(1, int(min_height_logical * sy_) - slack(sy_))
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


FOCUS_RING_DARK = (0x0C, 0x0C, 0x18)
FOCUS_RING_LIGHT = (0xF8, 0xF8, 0xF8)


def focus_ring_audit(frame: Frame, bar, m: "Mapping") -> dict:
    """The shared focus band's two-tone ring (kModernMenuFocusRing*): given a
    located leading bar [x, y, w, h] in output pixels, sample the logical
    pixels beside it and require dark outer / light inner lines at the top
    and bottom edges (inset, so the row above and below stay untouched)."""
    x0, y0, w, h = bar
    top = int(m.logical_y(y0 + m.sy / 2))
    bottom = int(m.logical_y(y0 + h - m.sy / 2))
    lx = int(m.logical_x(x0 + w + m.sx * 3.5))  # clear of the 3px marker
    px = lambda ly: frame.rgb(min(frame.width - 1, int(m.vx + (lx + 0.5) * m.sx)),
                              min(frame.height - 1, int(m.vy + (ly + 0.5) * m.sy)))
    samples = {"top_outer": px(top), "top_inner": px(top + 1),
               "bottom_inner": px(bottom - 1), "bottom_outer": px(bottom)}
    ok = (samples["top_outer"] == FOCUS_RING_DARK == samples["bottom_outer"]
          and samples["top_inner"] == FOCUS_RING_LIGHT == samples["bottom_inner"])
    return {"schema": SCHEMA, "check": "focus-ring", "input_sha256": frame.sha256,
            "samples": {k: list(v) for k, v in samples.items()}, "pass": ok,
            **DISCLAIMER}


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
        sp.add_argument("--mode", choices=("fit", "integer"), default="fit")
        sp.add_argument("--par", type=float, default=PAR_DEFAULT,
                        help="pixel aspect for --mode fit (default 7/6)")

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
    f.add_argument("--logical", nargs=2, type=int, required=True)
    f.add_argument("--scale", type=float,
                   help="override px per logical pixel (default: from mapping)")
    m = sub.add_parser("compare"); common(m)
    m.add_argument("other", type=Path)
    m.add_argument("--other-expect-sha256")
    m.add_argument("--logical", nargs=2, type=int, required=True)
    m.add_argument("--max-diff", type=int, default=0)
    m.add_argument("--diff-png", type=Path,
                   help="write a logical-canvas difference picture (red = differs)")
    x = sub.add_parser("explain"); common(x)
    x.add_argument("--top", type=int, default=5)
    t = sub.add_parser("detect"); common(t)
    t.add_argument("--widths", nargs="+", type=int, default=[256, 342])
    a = p.parse_args(argv)
    try:
        frame = load(a.p7, a.expect_sha256)
        if a.cmd == "contrast":
            rep = local_contrast(frame, tuple(a.roi), a.foreground, a.threshold)
        elif a.cmd == "clip":
            rep = clip_audit(frame, *a.logical, a.colour, a.region, a.mode, a.par)
        elif a.cmd == "focus":
            m = mapping(*a.logical, frame.width, frame.height, a.mode, a.par)
            rep = focus_audit(frame, a.marker, a.scale or m.sx, scale_y=(
                a.scale or m.sy))
        elif a.cmd == "explain":
            rep = {"schema": SCHEMA, "check": "explain", "input_sha256": frame.sha256,
                   "output": [frame.width, frame.height],
                   "ranked_mappings": explain_mapping(frame, top=a.top),
                   "pass": True, **DISCLAIMER}
        elif a.cmd == "detect":
            rep = detect_logical(frame, tuple(a.widths), mode=a.mode, par=a.par)
        else:
            other = load(a.other, a.other_expect_sha256)
            rep = compare_resolutions(frame, other, *a.logical, a.max_diff,
                                      a.mode, a.par)
            if a.diff_png:
                a.diff_png.write_bytes(diff_png(frame, other, *a.logical,
                                                a.mode, a.par))
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return _emit(rep, a.require)


if __name__ == "__main__":
    raise SystemExit(main())
