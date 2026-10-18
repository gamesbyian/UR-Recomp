#!/usr/bin/env python3
"""Offline, non-shipping continuous-rig pose review. No original pixels/ROM.

Both animation rows use ONE model, a single fixed camera and the same scale.
Fail closed on any clipped model pose. A screenshot at rest alone is
insufficient: render every source interval in each pedal/spin cycle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

try:
    from .common_silhouette_preview import common_pose_crop
except ImportError:
    from common_silhouette_preview import common_pose_crop

try:
    from .render_shared_unicycle_review import (inspect_model, require_clean_border,
                                              occupied_bounds, MIN_BORDER_PIXELS)
except ImportError:
    from render_shared_unicycle_review import (inspect_model, require_clean_border,
                                            occupied_bounds, MIN_BORDER_PIXELS)

MODES = ("ride", "stunt_cycle")
STEPS = 8
RENDER_SIZE = 320
CAMERA = "0,0,1.6,90,0,0,12.5"  # deliberately zoomed out from static art

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def samples(steps=STEPS):
    if steps not in (8, 16):
        raise ValueError("only source-bounded 8/16 sample intervals supported")
    return tuple((mode, i, i / steps)
                 for mode in MODES for i in range(steps + 1))

def render(model: Path, out: Path, openscad="openscad", xvfb=False, steps=STEPS):
    from PIL import Image, ImageDraw
    samples(steps)  # validate time-grid before touching output

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
    for mode, i, t in samples(steps):
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
    count = 2*(steps+1)
    if len(actual) != count:
        raise ValueError("did not render both complete bounded motion cycles")
    # A full pedal or 360-degree stunt cycle must wrap to exactly the same
    # visible 320x320 pixels. This is an art-tool loop contract only; no
    # assertion about source game timing, stunt contact or RGB5 parity.
    from PIL import ImageChops
    for mode in MODES:
        with Image.open(out/f"{mode}-00.png") as first, \
             Image.open(out/f"{mode}-{steps:02d}.png") as last:
            if ImageChops.difference(first.convert("RGB"), last.convert("RGB")).getbbox():
                raise ValueError("animated rig loop has discontinuous rendered endpoints")
    # One crop across BOTH motion modes and ALL frames, never a per-frame
    # camera fit. At 32px preview the RACER occupies the image rather than
    # shrinking the entire 320px authoring viewport to 32px.
    sprite_crop = common_pose_crop([row["silhouette_bbox"] for row in actual],
                                   RENDER_SIZE, RENDER_SIZE)
    tile_w, row_h = 170, 252
    sheet = Image.new("RGB", ((steps+1)*tile_w, 2*row_h+55), "#f0f1f4")
    draw = ImageDraw.Draw(sheet)
    for r, mode in enumerate(MODES):
        y = r*row_h
        draw.text((8,y+6),
                  f"LOCKED SIDE CAMERA | {mode} | {steps+1} samples, one coherent rig",
                  fill="#111")
        for i in range(steps+1):
            x = i*tile_w+5
            with Image.open(out/f"{mode}-{i:02d}.png") as im:
                full = im.convert("RGB").resize((160,160), Image.Resampling.LANCZOS)
            sheet.paste(full,(x,y+34))
            draw.text((x,y+194),f"t={i/steps:.3f}",fill="#111")
            with Image.open(out/f"{mode}-{i:02d}.png") as source_im:
                sprite_thumbnail = source_im.convert("RGB").crop(sprite_crop).resize(
                    (32,32), Image.Resampling.LANCZOS)
            sheet.paste(sprite_thumbnail,(x,y+210))
    draw.text((8,sheet.height-30),
              "UNAPPROVED MODEL | CONTINUOUS RIG ONLY | NOT SOURCE-REGISTERED OR IN GAME",
              fill="#111")
    preview = out/f"continuous-motion-{count}frame-contact.png"
    sheet.save(preview)
    result = {
        "schema": "UR-unicycle-one-rig-continuous-motion-review/1",
        "shared_rig_sha256": sha(model.read_bytes()),
        "contact_sha256": sha(preview.read_bytes()),
        "camera_one_fixed_per_all_frames": CAMERA,
        "source_animation_frame_count": count,
        "source_animation_samples_per_mode": steps+1,
        "all_complete_320_square_pixel_frames": True,
        "all_source_model_unclipped": True,
        "normal_size_preview_px": 32,
        "normal_size_preview_common_crop_all_modes": list(sprite_crop),
        "normal_size_preview_per_frame_autofit": False,
        "normal_size_preview_owner_approved": False,
        "two_continuous_motion_loops_pixel_exact_at_endpoints": True,
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
    cli.add_argument("--steps", type=int, choices=(8,16), default=8,
                     help="eight or sixteen intervals, two complete cycles")
    args = cli.parse_args()
    try:
        preview, receipt = render(args.model.resolve(), args.out.resolve(),
                                  args.openscad, args.xvfb, args.steps)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        cli.exit(2, f"UNAPPROVED_RIG_MOTION_REVIEW_FAILED: {exc}\n")
    print("UNAPPROVED_RIG_MOTION_REVIEW", str(preview),
          receipt["contact_sha256"], "source=not_registered release=0")

if __name__ == "__main__":
    main()
