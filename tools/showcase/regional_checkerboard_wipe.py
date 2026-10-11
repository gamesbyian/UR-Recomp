#!/usr/bin/env python3
"""Offline, presentation-only checkerboard regional title flip preview.

The effect is editorial/Modern-only, not a stock SNES animation. Source
screenshots and main-menu tile/colour measurement must be supplied by a
provenance-bound calibration before a non-synthetic render is accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # Geometry/unit tests remain runnable without preview deps.
    Image = None

CALIBRATION_SCHEMA = "UR-REGIONAL-CHECKER-CALIBRATION/1"
OUTPUT_SCHEMA = "UR-REGIONAL-CHECKER-PREVIEW/1"
DIRECTIONS = ("to-unirally", "to-uniracers")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid(width: int, height: int, cell_w: int, cell_h: int,
         offset_x: int, offset_y: int):
    """Cells including cropped edge cells, indexed in top-left reading order."""
    if not (1 <= cell_w <= width and 1 <= cell_h <= height):
        raise ValueError("tile dimensions outside the logical image")
    if not (0 <= offset_x < cell_w and 0 <= offset_y < cell_h):
        raise ValueError("grid offsets must be inside one tile")
    xs = list(range(-offset_x, width, cell_w))
    ys = list(range(-offset_y, height, cell_h))
    return [(i, j, x, y) for j, y in enumerate(ys) for i, x in enumerate(xs)], len(xs), len(ys)


def total_frames(cols: int, rows: int, flip_frames: int, stagger_frames: int) -> int:
    if flip_frames < 2 or stagger_frames < 1:
        raise ValueError("flip_frames >=2 and stagger_frames >=1 required")
    return flip_frames + (cols + rows - 2) * stagger_frames


def tile_rank(column: int, row: int, cols: int, rows: int, direction: str) -> int:
    if direction not in DIRECTIONS:
        raise ValueError("unknown direction")
    return (column + row if direction == "to-unirally"
            else (cols - 1 - column) + (rows - 1 - row))


def render(source: Image.Image, target: Image.Image, *,
           tile_w: int, tile_h: int, offset_x: int, offset_y: int,
           grey: tuple[int, int, int], direction: str, frame: int,
           flip_frames: int = 10, stagger_frames: int = 2) -> Image.Image:
    """Render one exact integer-frame sample, without interpolation or blending.

    Each tile is squeezed about its bottom-left/top-right diagonal axis.
    A signed, diagonal shear moves the edge-on blade toward the destination
    corner, distinguishing the two local flip directions. The back face uses
    the destination texture in its canonical orientation. All texels are
    nearest-neighbour samples, never blends.
    """
    if Image is None:
        raise RuntimeError("Pillow is required to render PNG previews")
    if source.mode != "RGB" or target.mode != "RGB" or source.size != target.size:
        raise ValueError("source and target must be equal-sized RGB images")
    if len(grey) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in grey):
        raise ValueError("grey must contain exactly three RGB8 channels")
    if direction not in DIRECTIONS:
        raise ValueError("unknown direction")
    cells, cols, rows = grid(*source.size, tile_w, tile_h, offset_x, offset_y)
    duration = total_frames(cols, rows, flip_frames, stagger_frames)
    if not 0 <= frame <= duration:
        raise ValueError("frame outside transition")
    if frame == 0:
        return source.copy()
    if frame == duration:
        return target.copy()

    out = Image.new("RGB", source.size, grey)
    src_pixels, dst_pixels, output = source.load(), target.load(), out.load()
    sign = 1 if direction == "to-unirally" else -1
    width, height = source.size
    for c, r, x0, y0 in cells:
        phase = (frame - stagger_frames * tile_rank(c, r, cols, rows, direction)) / flip_frames
        xmin, xmax = max(0, x0), min(width, x0 + tile_w)
        ymin, ymax = max(0, y0), min(height, y0 + tile_h)
        if phase <= 0 or phase >= 1:
            pixels = src_pixels if phase <= 0 else dst_pixels
            for y in range(ymin, ymax):
                for x in range(xmin, xmax):
                    output[x, y] = pixels[x, y]
            continue
        compression = abs(math.cos(math.pi * phase))
        if compression < 1e-10:  # edge-on: show only sampled grey backing
            continue
        # Illustrative screen-space projection, not hardware Mode 7.
        shear = sign * 0.17 * math.sin(math.pi * phase)
        pixels = src_pixels if phase < 0.5 else dst_pixels
        for y in range(ymin, ymax):
            ny = 2 * (y - y0 + 0.5) / tile_h - 1
            for x in range(xmin, xmax):
                nx = 2 * (x - x0 + 0.5) / tile_w - 1
                u, v = (nx + ny) / 2, (nx - ny) / 2
                original_u = (u - shear) / compression
                sxn, syn = original_u + v, original_u - v
                if -1 <= sxn < 1 and -1 <= syn < 1:
                    sx = x0 + int((sxn + 1) * tile_w / 2)
                    sy = y0 + int((syn + 1) * tile_h / 2)
                    if 0 <= sx < width and 0 <= sy < height:
                        output[x, y] = pixels[sx, sy]
    return out


def calibration(path: Path, menu_path: Path):
    if Image is None:
        raise RuntimeError("Pillow is required to inspect menu screenshots")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != CALIBRATION_SCHEMA or data.get("status") != "measured-original-main-menu":
        raise ValueError("calibration must be identified as measured original main-menu evidence")
    digest = sha256(menu_path)
    if data.get("menu_sha256") != digest or not data.get("capture_tag") or not data.get("source_description"):
        raise ValueError("menu hash, capture tag, or source description missing/mismatched")
    menu = Image.open(menu_path).convert("RGB")
    width, height = data["logical_size"]
    if menu.size != (width, height):
        raise ValueError("menu image does not match calibrated logical raster")
    tile_w, tile_h = int(data["tile_width"]), int(data["tile_height"])
    ox, oy = int(data["offset_x"]), int(data["offset_y"])
    grid(width, height, tile_w, tile_h, ox, oy)
    gx, gy = data["grey_sample_xy"]
    if not 0 <= gx < width or not 0 <= gy < height:
        raise ValueError("grey sample outside the menu")
    return data, menu.getpixel((gx, gy))


def demo_images():
    """Clearly synthetic demo, never evidence of actual game artwork/colour."""
    if Image is None:
        raise RuntimeError("Pillow is required for synthetic preview")
    size = (80, 56)
    menu = Image.new("RGB", size, (120, 120, 120))
    a = Image.new("RGB", size)
    b = Image.new("RGB", size)
    for y in range(size[1]):
        for x in range(size[0]):
            a.putpixel((x, y), (32 + x, 35 + y, 120))
            b.putpixel((x, y), (140, 40 + x, 45 + y))
    return a, b, menu, {"tile_width": 8, "tile_height": 8,
                          "offset_x": 0, "offset_y": 0}, (120, 120, 120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-image", type=Path, help="settled retail Uniracers RGB PNG")
    parser.add_argument("--to-image", type=Path, help="settled retail Unirally RGB PNG")
    parser.add_argument("--menu-image", type=Path, help="original main-menu screenshot")
    parser.add_argument("--calibration", type=Path, help="measured menu grid/sample manifest")
    parser.add_argument("--synthetic-demo", action="store_true", help="synthetic placeholder only")
    parser.add_argument("--direction", choices=(*DIRECTIONS, "both"), default="both")
    parser.add_argument("--flip-frames", type=int, default=10)
    parser.add_argument("--stagger-frames", type=int, default=2)
    parser.add_argument("--all-frames", action="store_true", help="otherwise only five review frames")
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    if args.synthetic_demo:
        if any((args.from_image, args.to_image, args.menu_image, args.calibration)):
            parser.error("--synthetic-demo cannot accept retail images/calibration")
        a, b, menu, geom, grey = demo_images()
        sources = {"status": "SYNTHETIC DEMO - NOT RETAIL EVIDENCE"}
    else:
        if not all((args.from_image, args.to_image, args.menu_image, args.calibration)):
            parser.error("real preview requires both retail images, menu screenshot and calibration")
        data, grey = calibration(args.calibration, args.menu_image)
        a, b = Image.open(args.from_image).convert("RGB"), Image.open(args.to_image).convert("RGB")
        if a.size != b.size or a.size != tuple(data["logical_size"]):
            parser.error("retail title images must share the calibrated logical dimensions")
        geom = {k: data[k] for k in ("tile_width", "tile_height", "offset_x", "offset_y")}
        sources = {"status": "PROVENANCE-CHECKED INPUTS; EFFECT STILL EDITORIAL",
                   "menu_sha256": sha256(args.menu_image),
                   "from_sha256": sha256(args.from_image),
                   "to_sha256": sha256(args.to_image),
                   "calibration_sha256": sha256(args.calibration),
                   "capture_tag": data["capture_tag"],
                   "source_description": data["source_description"],
                   "grey_sample_xy": data["grey_sample_xy"]}

    cells, cols, rows = grid(*a.size, geom["tile_width"], geom["tile_height"],
                             geom["offset_x"], geom["offset_y"])
    duration = total_frames(cols, rows, args.flip_frames, args.stagger_frames)
    indices = list(range(duration + 1)) if args.all_frames else sorted({
        0, duration // 4, duration // 2, (3 * duration) // 4, duration})
    dirs = DIRECTIONS if args.direction == "both" else (args.direction,)
    args.outdir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for direction in dirs:
        old, new = (a, b) if direction == "to-unirally" else (b, a)
        for frame in indices:
            image = render(old, new, grey=grey, direction=direction, frame=frame,
                           flip_frames=args.flip_frames, stagger_frames=args.stagger_frames,
                           tile_w=geom["tile_width"], tile_h=geom["tile_height"],
                           offset_x=geom["offset_x"], offset_y=geom["offset_y"])
            path = args.outdir / f"{direction}-{frame:04d}.png"
            image.save(path)
            outputs.append({"file": path.name, "frame": frame, "direction": direction,
                            "sha256": sha256(path)})
    manifest = {"schema": OUTPUT_SCHEMA, "source": sources, "logical_size": list(a.size),
                "geometry": geom, "backing_grey_rgb8": list(grey), "directions": list(dirs),
                "flip_frames": args.flip_frames, "stagger_frames": args.stagger_frames,
                "total_frames": duration, "algorithm": "diagonal-axis-nearest-projection-v1",
                "art_is_immutable": True, "authentic_gameplay_changed": False,
                "frames": outputs}
    (args.outdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(outputs)} PNGs; frame interval 0..{duration}; manifest at {args.outdir / 'manifest.json'}")


if __name__ == "__main__":
    main()
