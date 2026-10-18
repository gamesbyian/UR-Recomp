#!/usr/bin/env python3
"""Source-pinned offline five-pose HD unicycle review; NEVER a runtime renderer.

Renders a single OpenSCAD model from two fixed cameras. Optional genuine 2014
PPU-source P7/old rejected-HD previews are SHA-bound to an archived AOT ZIP.
All preview files stay outside Git. No RGB5, OAM or character approval claims.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

try:
    from .common_silhouette_preview import common_pose_crop
except ImportError:  # standalone offline authoring script
    from common_silhouette_preview import common_pose_crop

POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
CAMERAS = {
    # Fixed common frame includes 2.2x seat and 2.0x body mass proposals.
    "side": "0,0,1.6,90,0,0,22",
    "three_quarter": "0,0,1.7,72,0,28,22",
}
AOT_SHA = "6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431"
SOURCES = {
    "original_title": ("baldosa-fixed-source/ur-baldosa-original-source-000400.pam",
                       "ee97b26ca9deac86809604665097473357d078867bad9a2f3da2384056eb9362"),
    "original_gameplay": ("baldosa-fixed-source/ur-baldosa-original-source-001856.pam",
                          "6aea6cebaf1292d962ad5ce01a73966bb0ad8948095d1e73b155712cac41039a"),
    "visually_rejected_4x": ("baldosa-hd-captures-4x/ur-baldosa-frame-001856.pam",
                            "99069e31084161f64904a5733bd275ac9933af03c8fb03df558c3b06771ec5f5"),
}
MIN_BORDER_PIXELS = 4  # both static and moving OpenSCAD crop checks
SADDLE_CHOICES = (1.0, 1.4, 1.8, 2.2)
FRAME_CHOICES = (1.0, 1.4, 1.8, 2.0)
SADDLE_CUP_CHOICES = (1.0, 1.7, 2.25)
SADDLE_DEPTH_CHOICES = (1.0, 1.45, 1.65)
GEOMETRY_MODULES = ("module tire()", "module rim_and_hub()", "module saddle(",
                    "module fork_and_frame()", "module pedals(", "module rig(")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_model(path: Path) -> str:
    data = path.read_bytes()
    text = data.decode("utf-8")
    if not all(token in text for token in GEOMETRY_MODULES):
        raise ValueError("canonical wheel/fork/pedals/saddle/rig missing")
    if "rig(rig_pose);" not in text:
        raise ValueError("pose output must invoke the same canonical rig")
    if any((f'p=="{pose}"' not in text and f'pose=="{pose}"' not in text)
           for pose in POSES):
        raise ValueError("five coherent motion poses missing")
    if "current_visual_approval=true" in text or "shipping_art_approved=true" in text:
        raise ValueError("unsupported human approval override")
    return sha(data)


def authentic_sources(path: Path) -> dict[str, bytes]:
    archive = path.read_bytes()
    if sha(archive) != AOT_SHA:
        raise ValueError("genuine source archive identity mismatch")
    result = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for label, (name, expected) in SOURCES.items():
            raw = z.read(name)
            if sha(raw) != expected:
                raise ValueError(f"archive member changed: {label}")
            result[label] = raw
    return result


def open_p7(blob: bytes):
    from PIL import Image
    marker = b"ENDHDR\n"
    if not blob.startswith(b"P7\nWIDTH ") or blob.count(marker) != 1:
        raise ValueError("not a full original P7 source")
    head, data = blob.split(marker, 1)
    props = dict(row.split(" ", 1) for row in head.decode("ascii").splitlines()[1:])
    if (props.get("DEPTH"), props.get("MAXVAL"), props.get("TUPLTYPE")) != (
        "4", "255", "RGB_ALPHA"
    ):
        raise ValueError("unsupported P7 channel order")
    width, height = int(props["WIDTH"]), int(props["HEIGHT"])
    if (width, height) not in ((256, 224), (1024, 896)) or len(data) != width*height*4:
        raise ValueError("partial or unsupported authentic raster")
    return Image.frombytes("RGBA", (width, height), data).convert("RGB")


def require_clean_border(pixels, width: int, height: int):
    """Pure pixel-access guard. Works without Pillow in dependency-free tests.

    Check four entire border strips, not just bounding boxes against a corner
    that might already contain the model. Reject too-small/empty viewports.
    """
    if width <= 2*MIN_BORDER_PIXELS or height <= 2*MIN_BORDER_PIXELS:
        raise ValueError("insufficient fixed-camera protected border")
    color = pixels[0, 0]
    if any(pixels[x, y] != color for x, y in (
        (width - 1, 0), (0, height - 1), (width - 1, height - 1)
    )):
        raise ValueError("different fixed-camera background corners")
    for y in range(height):
        for x in range(width):
            if (x < MIN_BORDER_PIXELS or y < MIN_BORDER_PIXELS or
                x >= width-MIN_BORDER_PIXELS or
                y >= height-MIN_BORDER_PIXELS):
                if pixels[x, y] != color:
                    raise ValueError("model touches protected fixed-camera border")
    return color


def occupied_bounds(im):
    """Return the silhouette bbox; reject every clipped/empty frame."""
    from PIL import Image, ImageChops

    frame = im.convert("RGB")
    width, height = frame.size
    background_color = require_clean_border(frame.load(), width, height)
    background = Image.new("RGB", frame.size, background_color)
    bounds = ImageChops.difference(frame, background).getbbox()
    if bounds is None:
        raise ValueError("all-background/empty rig motion frame")
    left, top, right, bottom = bounds
    if min(left, top, frame.width-right, frame.height-bottom) < MIN_BORDER_PIXELS:
        raise ValueError("model clipped at fixed-camera viewport boundary")
    return [left, top, right, bottom]

def validate_variant(saddle_span, frame_mass):
    """Bounded art-authoring proposals, never inferred original 3D values."""
    if (type(saddle_span) not in (int,float) or
        type(frame_mass) not in (int,float) or
        saddle_span not in SADDLE_CHOICES or
        frame_mass not in FRAME_CHOICES):
        raise ValueError("unreviewed art geometry outside bounded parameters")
    return saddle_span, frame_mass


def validate_cupped_saddle(cup, depth):
    """Only bounded, unapproved single-rig shape proposals; defaults unchanged."""
    if (type(cup) not in (float,int) or type(depth) not in (float,int) or
        cup not in SADDLE_CUP_CHOICES or depth not in SADDLE_DEPTH_CHOICES):
        raise ValueError("unreviewed original-rig saddle profile")
    return cup, depth


def render(model: Path, out: Path, *, openscad: str = "openscad",
           xvfb: bool = False, size: int = 480,
           saddle_span: float = 1.0, frame_mass: float = 1.0,
           saddle_cup: float = 1.0, saddle_depth: float = 1.0) -> list[dict]:
    validate_variant(saddle_span, frame_mass)
    validate_cupped_saddle(saddle_cup, saddle_depth)
    from PIL import Image
    if not 128 <= size <= 1024:
        raise ValueError("unbounded review render size")
    out.mkdir(parents=True, exist_ok=True)
    images = []
    for view, camera in CAMERAS.items():
        for pose in POSES:
            name = f"{view}-{pose}.png"
            args = (["xvfb-run", "-a"] if xvfb else []) + [
                openscad, "--hardwarnings", "-o", str(out/name),
                f"--imgsize={size},{size}", "--projection=o",
                "--colorscheme=Tomorrow", f"--camera={camera}",
                "-D", f'rig_pose="{pose}"',
                "-D", f"rig_saddle_span={saddle_span}",
                "-D", f"rig_frame_mass={frame_mass}",
                "-D", f"rig_saddle_cup={saddle_cup}",
                "-D", f"rig_saddle_depth={saddle_depth}", str(model)]
            result = subprocess.run(args, text=True, capture_output=True,
                                    check=False, timeout=90)
            if result.returncode or not (out/name).is_file():
                raise RuntimeError(f"OpenSCAD {view}/{pose}: {result.stderr[-500:]}")
            with Image.open(out/name) as im:
                if im.size != (size, size):
                    raise ValueError("OpenSCAD image geometry changed")
                bounds = occupied_bounds(im)
            images.append({"view": view, "pose": pose, "fixed_camera": camera,
                           "file": name, "sha256": sha((out/name).read_bytes()),
                           "silhouette_bbox": bounds, "edge_clipped": False,
                           "source_render_size_px": size,
                           "review_saddle_span": saddle_span,
                           "review_frame_mass": frame_mass,
                           "review_saddle_cup": saddle_cup,
                           "review_saddle_depth": saddle_depth})
    return images


def contact(out: Path, images: list[dict], original: dict[str, bytes] | None):
    from PIL import Image, ImageDraw, ImageEnhance
    side = 320
    row_height = 432
    height = row_height*2 + (side if original else 0) + 60
    canvas = Image.new("RGB", (5*side, height), "#f2f3f5")
    draw = ImageDraw.Draw(canvas)
    y = 0
    if original:
        for col, (name, raw) in enumerate(original.items()):
            src = open_p7(raw)
            # Game/old 4x source is SNES 7:6 PAR. Candidate 3D previews
            # stay square-pixel. This is DISPLAY-ONLY nearest, not a source
            # transform used for pixel-equality or original crop acceptance.
            src = src.resize((round(src.width*7/6),src.height),
                             Image.Resampling.NEAREST)
            if name == "original_title":
                # Display brightening is explicitly NOT a comparison transform.
                src = ImageEnhance.Brightness(src).enhance(3.5)
            src.thumbnail((side-20, side-42))
            canvas.paste(src, (col*side + (side-src.width)//2, 36))
            draw.text((col*side+10, 10), name.replace("_"," "), fill="black")
        draw.text((3*side+8, 12), "Authentic source: archived", fill="black")
        draw.text((3*side+8, 32), "Title fade preview brightened 3.5x", fill="black")
        y += side
    crops = {}
    for view in CAMERAS:
        view_rows = [item for item in images if item["view"] == view]
        sizes = {item["source_render_size_px"] for item in view_rows}
        if len(view_rows) != len(POSES) or len(sizes) != 1:
            raise ValueError("missing same-size original renders in fixed-view family")
        source_size = sizes.pop()
        crop = common_pose_crop([item["silhouette_bbox"] for item in view_rows],
                                source_size, source_size)
        crops[view] = list(crop)
        draw.text((10,y+8),f"LOCKED {view} camera | ONE shared rig",fill="black")
        for col, pose in enumerate(POSES):
            row = next(r for r in images if r["view"]==view and r["pose"]==pose)
            with Image.open(out/row["file"]) as im:
                model_rgb = im.convert("RGB")
                full = model_rgb.resize((side,side), Image.Resampling.LANCZOS)
                thumbs = {px: model_rgb.crop(crop).resize((px,px), Image.Resampling.LANCZOS)
                          for px in (64,32)}
            canvas.paste(full,(col*side,y+27))
            draw.text((col*side+12,y+side+34),pose,fill="black")
            for index, pixels in enumerate((64,32)):
                canvas.paste(thumbs[pixels],(col*side + 10+85*index,y+side+50))
        y += row_height
    draw.text((10,height-27),
              "UNAPPROVED CANDIDATE: no source PPU parity, visual or release approval",
              fill="black")
    target = out/"five-pose-fixed-camera-review.png"
    canvas.save(target)
    return target, crops


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path,
                        default=Path(__file__).parent/"candidates"/"unicycle_shared_rig.scad")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--authentic-source-zip", type=Path)
    parser.add_argument("--openscad", default="openscad")
    parser.add_argument("--saddle-span", type=float, choices=SADDLE_CHOICES,
                        default=1.0, help="unapproved model study only")
    parser.add_argument("--frame-mass", type=float, choices=FRAME_CHOICES,
                        default=1.0, help="unapproved model study only")
    parser.add_argument("--saddle-cup", type=float, choices=SADDLE_CUP_CHOICES,
                        default=1.0, help="unapproved title-direction cushion profile")
    parser.add_argument("--saddle-depth", type=float, choices=SADDLE_DEPTH_CHOICES,
                        default=1.0, help="unapproved cushion thickness")
    parser.add_argument("--xvfb", action="store_true",
                        help="launch OpenSCAD under xvfb-run -a on headless Linux")
    args = parser.parse_args()
    model=args.model.resolve()
    source_hash=inspect_model(model)
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("output directory must be empty to prevent stale pose images")
    original=authentic_sources(args.authentic_source_zip) if args.authentic_source_zip else None
    images=render(model,args.out,openscad=args.openscad,xvfb=args.xvfb,
                  saddle_span=args.saddle_span,frame_mass=args.frame_mass,
                  saddle_cup=args.saddle_cup,saddle_depth=args.saddle_depth)
    preview, preview_crops=contact(args.out,images,original)
    receipt={
        "schema":"UR-single-rig-five-pose-art-blockout/1",
        "rig_sha256":source_hash,
        "original_source_archive_sha256":AOT_SHA if original else None,
        "pose_images":images,"review_contact_sha256":sha(preview.read_bytes()),
        "single_canonical_model":True,"locked_camera_per_view":True,
        "all_static_source_model_frames_unclipped": True,
        "static_review_border_px": MIN_BORDER_PIXELS,
        "review_saddle_span": args.saddle_span,
        "review_frame_mass": args.frame_mass,
        "review_saddle_cup": args.saddle_cup,
        "review_saddle_depth": args.saddle_depth,
        "gameplay_normal_size_previews_px":[64,32],
        "normal_size_previews_common_crop_per_view": preview_crops,
        "normal_size_previews_per_pose_autofit": False,
        "normal_size_previews_likeness_approved": False,
        "original_native_RGB5_PPU_equivalence":False,
        "measured_original_landmark_proportions":False,
        "original_animation_and_contact_approval":False,
        "human_visual_approval":False,
        "asset_runtime_integration":False,
        "shipping_ready":False,"release_gate":False,
    }
    (args.out/"review-receipt.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"{preview} SHA256={receipt['review_contact_sha256']} approved=0")


if __name__=="__main__":
    main()
