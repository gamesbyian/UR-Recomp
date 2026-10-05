#!/usr/bin/env python3
"""Measure what a widened race view reveals that the 4:3 view does not.

Two kinds of extra information reach the player in 16:9:

* objects: sprites drawn in a side margin. Each OAM entry is classified
  per frame as `margin_only` (wholly outside the stock 256 columns, so new
  information) or `extends` (partly visible in 4:3 already). The OAM shadow
  in each frame's WRAM gives identity and boxes; an OBJ-only framedump
  (`SNESRECOMP_LAYER_MASK=0x10`) confirms the sprite really drew margin
  pixels. Optional full and OBJ-less composites of the same route show
  whether those pixels survive layer priority in the final picture.
* course: the margin shows track ahead earlier. With the camera moving
  `v` px/frame, `margin` extra pixels arrive `margin / v` frames sooner.

Split-screen bands apply the sprite-rip high-OAM values for sprites 96-99
(see tools/check_split_sprite_rip_margin.py).
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import struct
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope

OAM_LOW = 0x1381
OAM_HIGH = 0x1581
SMALL, LARGE = 32, 64  # OBSEL $83 during races
SPLIT_LINE = 112
RIP_TOP, RIP_BOTTOM = 0xA5, 0x5A
DEFAULT_MARGIN = 43


def read_bmp(path: Path) -> tuple[int, int, bytes, int]:
    raw = path.read_bytes()
    offset = struct.unpack_from("<I", raw, 10)[0]
    width = struct.unpack_from("<i", raw, 18)[0]
    height = struct.unpack_from("<i", raw, 22)[0]
    bpp = struct.unpack_from("<H", raw, 28)[0]
    if height > 0:
        raise ValueError(f"{path}: expected a top-down framedump BMP")
    return width, -height, raw[offset:], bpp // 8


class Frame:
    def __init__(self, path: Path):
        self.width, self.height, self.pixels, self.bpp = read_bmp(path)
        counts = collections.Counter(self.px(x, 0) for x in range(self.width))
        self.background = counts.most_common(1)[0][0]

    def px(self, x: int, y: int) -> bytes:
        i = (y * self.width + x) * self.bpp
        return self.pixels[i:i + 3]

    def drawn(self, x0: int, x1: int, y0: int, y1: int) -> int:
        return sum(
            1
            for y in range(max(0, y0), min(self.height, y1))
            for x in range(max(0, x0), min(self.width, x1))
            if self.px(x, y) != self.background
        )


def sprite_boxes(wram: bytes, split: bool):
    """Yield (sprite, screen_x, size, first_line, end_line) per visible band."""
    for i in range(128):
        x = wram[OAM_LOW + i * 4]
        y = wram[OAM_LOW + i * 4 + 1]
        high = (wram[OAM_HIGH + i // 4] >> ((i % 4) * 2)) & 3
        bands = [(high, 0, 224)]
        if split and 96 <= i <= 99:
            shift = (i - 96) * 2
            bands = [((RIP_TOP >> shift) & 3, 0, SPLIT_LINE),
                     ((RIP_BOTTOM >> shift) & 3, SPLIT_LINE, 224)]
        for bits, lo, hi in bands:
            size = LARGE if bits & 2 else SMALL
            sx = x - 256 if bits & 1 else x
            lines = [line for line in ((y + k) & 0xFF for k in range(size)) if lo <= line < hi]
            if lines:
                yield i, sx, size, min(lines), max(lines) + 1


def classify_objects(obj_frames: Path, margin: int, split: bool) -> dict[str, Any]:
    counts: collections.Counter = collections.Counter()
    per_sprite: collections.Counter = collections.Counter()
    boxes: dict[str, list] = collections.defaultdict(list)
    frames = 0
    for bmp in sorted(obj_frames.glob("frame_*.bmp")):
        wram_path = bmp.with_name(bmp.stem + "_wram.bin")
        if not wram_path.exists():
            continue
        frame = Frame(bmp)
        stock = frame.width - 2 * margin
        if stock != 256:
            continue
        frames += 1
        wram = wram_path.read_bytes()
        number = int(bmp.stem[6:12])
        for sprite, sx, size, y0, y1 in sprite_boxes(wram, split):
            x0, x1 = sx + margin, sx + size + margin
            if x1 <= 0 or x0 >= frame.width:
                continue
            in_stock = x1 > margin and x0 < margin + stock
            in_margin = x0 < margin or x1 > margin + stock
            if not in_margin:
                continue
            margin_px = (frame.drawn(x0, min(x1, margin), y0, y1)
                         + frame.drawn(max(x0, margin + stock), x1, y0, y1))
            if not margin_px:
                continue
            side = "left" if x0 < margin else "right"
            kind = f"{'extends' if in_stock else 'margin_only'}_{side}"
            counts[kind] += 1
            per_sprite[f"{sprite}:{kind}"] += 1
            if kind.startswith("margin_only"):
                boxes[f"{sprite}:{side}"].append(
                    {"frame": number, "box": [x0 - margin, y0, x1 - margin, y1],
                     "margin_px": margin_px})
    return {
        "frames": frames,
        "counts": dict(counts),
        "per_sprite": dict(sorted(per_sprite.items())),
        "margin_only_boxes": {k: v[:4] for k, v in boxes.items()},
        "margin_only_regions": {
            k: [min(b["box"][0] for b in v), min(b["box"][1] for b in v),
                max(b["box"][2] for b in v), max(b["box"][3] for b in v)]
            for k, v in boxes.items()
        },
    }


def composite_visibility(full: Path, no_obj: Path, regions: dict[str, list],
                         margin: int) -> dict[str, Any]:
    """Frames where OBJ changes the final picture inside each margin region."""
    visible: collections.Counter = collections.Counter()
    any_margin = 0
    frames = 0
    for bmp in sorted(full.glob("frame_*.bmp")):
        other = no_obj / bmp.name
        if not other.exists():
            continue
        a, b = Frame(bmp), Frame(other)
        frames += 1
        stock = a.width - 2 * margin
        cols = list(range(margin)) + list(range(margin + stock, a.width))
        if any(a.px(x, y) != b.px(x, y) for y in range(a.height) for x in cols):
            any_margin += 1
        for key, (x0, y0, x1, y1) in regions.items():
            if any(a.px(x + margin, y) != b.px(x + margin, y)
                   for y in range(max(0, y0), min(a.height, y1))
                   for x in range(max(-margin, x0), min(stock + margin, x1))):
                visible[key] += 1
    return {"frames": frames, "obj_in_margin_frames": any_margin,
            "margin_only_region_visible_frames": dict(visible)}


def course_lookahead(wram_frames: Path, camera_addrs: list[int], margin: int) -> dict[str, Any]:
    out = {}
    paths = sorted(wram_frames.glob("frame_*_wram.bin"))
    for addr in camera_addrs:
        xs = [(lambda w: w[addr] | w[addr + 1] << 8)(p.read_bytes()) for p in paths]
        speeds = [abs(((b - a + 0x8000) & 0xFFFF) - 0x8000) for a, b in zip(xs, xs[1:])]
        moving = [s for s in speeds if s]
        median = statistics.median(moving) if moving else 0
        out[f"0x{addr:04X}"] = {
            "frames": len(speeds),
            "moving_frames": len(moving),
            "median_px_per_frame": median,
            "max_px_per_frame": max(moving) if moving else 0,
            "lead_frames_at_median": round(margin / median, 2) if median else None,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", required=True)
    parser.add_argument("--obj-frames", required=True, type=Path,
                        help="OBJ-only 16:9 framedump with per-frame WRAM")
    parser.add_argument("--full-frames", type=Path)
    parser.add_argument("--no-obj-frames", type=Path)
    parser.add_argument("--split", action="store_true")
    parser.add_argument("--camera", action="append", default=[],
                        help="camera X address (hex) for course lookahead")
    parser.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    objects = classify_objects(args.obj_frames, args.margin, args.split)
    metrics: dict[str, Any] = {"objects": objects}
    if args.full_frames and args.no_obj_frames:
        metrics["composite"] = composite_visibility(
            args.full_frames, args.no_obj_frames, objects["margin_only_regions"], args.margin)
    if args.camera:
        metrics["course_lookahead"] = course_lookahead(
            args.obj_frames, [int(a, 16) for a in args.camera], args.margin)
    envelope = make_envelope(
        evidence_type="widescreen-information-exposure",
        producer="tools/measure_widescreen_exposure.py",
        subject={"route": args.route},
        inputs={"margin": args.margin, "split": args.split},
        metrics=metrics,
        assertions=[assertion(f"{args.route}-frames-measured", objects["frames"] > 0,
                              {"frames": objects["frames"]})],
    )
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
