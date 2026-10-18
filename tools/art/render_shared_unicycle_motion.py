#!/usr/bin/env python3
"""Offline, non-shipping continuous-rig pose review. No original pixels/ROM.

Both animation rows use ONE model, a single fixed camera and the same scale.
Fail closed on any clipped model pose. A screenshot at rest alone is
insufficient: render all nine intervals in each pedal/spin cycle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

try:
    from .render_shared_unicycle_review import inspect_model
except ImportError:
    from render_shared_unicycle_review import inspect_model

MODES = ("ride", "stunt_cycle")
STEPS = 8
RENDER_SIZE = 320
CAMERA = "0,0,1.6,90,0,0,12.5"  # deliberately zoomed out from static art
MIN_BORDER_PIXELS = 4

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def samples():
    return tuple((mode, i, i / STEPS)
                 for mode in MODES for i in range(STEPS + 1))

def occupied_bounds(im):
    """Return the model silhouette bbox; refuse all-empty/full-window frames."""
    from PIL import Image, ImageChops

    frame = im.convert("RGB")
    background = Image.new("RGB", frame.size, frame.getpixel((0, 0)))
    bounds = ImageChops.difference(frame, background).getbbox()
    if bounds is None:
        raise ValueError("all-background/empty rig motion frame")
    left, top, right, bottom = bounds
    if min(left, top, frame.width-right, frame.height-bottom) < MIN_BORDER_PIXELS:
        raise ValueError("model clipped at fixed-camera viewport boundary")
    return [left, top, right, bottom]

def render(model: Path, out: Path, openscad="openscad", xvfb=False):
    from PIL import Image, ImageDraw

    if out.exists() and any(out.iterdir()):
        raise ValueError("output must be empty; old motion images could be reused")
    s = model.read_text(encoding="utf-8")
    inspect_model(model)
    if (s.count("module continuous_rig(") != 1 or
        s.count("shared_rig(pedal=18+720*u") != 1 or
        s.count('else if(p=="ride")') != 1 or
        s.count('else if(p=="stunt_cycle")') != 1):
        raise ValueError("motion must transform one common rig, with two modes")
    out.mkdir(parents=True, exist_ok=True)
    actual = []
    for mode, i, t in samples():
        filename = f"{mode}-{i:02d}.png"
        command = (["xvfb-run", "-a"] if xvfb else []) + [
            openscad, "--hardwarnings", "-o", str(out/filename),
            f"--imgsize={RENDER_SIZE},{RENDER_SIZE}",
            "--projection=o", "--colorscheme=Tomorrow",
            f"--camera={CAMERA}", "-D", f'rig_pose="{mode}"',
            "-D", f"rig_time={t}", str(model)]
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=90, check=False)
        if result.returncode:
            raise RuntimeError(f"OpenSCAD {mode}[{i}] failed: {result.stderr[-600:]}")
        raw = (out/filename).read_bytes()
        with Image.open(out/filename) as im:
            if im.size != (RENDER_SIZE, RENDER_SIZE):
                raise ValueError("unexpected non-320px art-study frame")
            bounds = occupied_bounds(im)
        actual.append({"mode": mode, "index": i, "normalized_time": t,
                       "fixed_camera": CAMERA, "filename": filename,
                       "sha256": sha(raw), "silhouette_bbox": bounds,
                       "edge_clipped": False})
    if len(actual) != 18:
        raise ValueError("did not render the full unbroken 18-image cycle")
    tile_w, row_h = 170, 252
    sheet = Image.new("RGB", (9*tile_w, 2*row_h+55), "#f0f1f4")
    draw = ImageDraw.Draw(sheet)
    for r, mode in enumerate(MODES):
        y = r*row_h
        draw.text((8,y+6),
                  f"LOCKED SIDE CAMERA | {mode} | 9 samples, one coherent rig",
                  fill="#111")
        for i in range(STEPS+1):
            x = i*tile_w+5
            with Image.open(out/f"{mode}-{i:02d}.png") as im:
                full = im.convert("RGB").resize((160,160), Image.Resampling.LANCZOS)
            sheet.paste(full,(x,y+34))
            draw.text((x,y+194),f"t={i/STEPS:.3f}",fill="#111")
            sheet.paste(full.resize((32,32), Image.Resampling.LANCZOS),
                        (x,y+210))
    draw.text((8,sheet.height-30),
              "UNAPPROVED MODEL | CONTINUOUS RIG ONLY | NOT SOURCE-REGISTERED OR IN GAME",
              fill="#111")
    preview = out/"continuous-motion-18frame-contact.png"
    sheet.save(preview)
    result = {
        "schema": "UR-unicycle-one-rig-continuous-motion-review/1",
        "shared_rig_sha256": sha(model.read_bytes()),
        "contact_sha256": sha(preview.read_bytes()),
        "camera_one_fixed_per_all_18": CAMERA,
        "all_18_complete_320_square_pixel_frames": True,
        "all_18_source_model_unclipped": True,
        "frames": actual,
        "original_gameplay_stunt_kinematics_proven": False,
        "gameplay_contact_and_pixel_aspect_registered": False,
        "owner_visual_approval": False,
        "shipping_art_approved": False,
        "native_game_runtime_modified": False,
        "release_accepted": False,
    }
    (out/"continuous-motion-review-receipt.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n",
        encoding="utf-8")
    return preview, result

def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--model", type=Path,
                     default=Path(__file__).parent/"candidates"/"unicycle_shared_rig.scad")
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--openscad", default="openscad")
    cli.add_argument("--xvfb", action="store_true")
    args = cli.parse_args()
    try:
        preview, receipt = render(args.model.resolve(), args.out.resolve(),
                                  args.openscad, args.xvfb)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        cli.exit(2, f"UNAPPROVED_RIG_MOTION_REVIEW_FAILED: {exc}\n")
    print("UNAPPROVED_RIG_MOTION_REVIEW", str(preview),
          receipt["contact_sha256"], "source=not_registered release=0")

if __name__ == "__main__":
    main()
