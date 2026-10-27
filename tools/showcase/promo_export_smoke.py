#!/usr/bin/env python3
"""ROM-free encode/readback smoke with the actual owner-approved promo images.

This verifies real FFmpeg composition and decoded pixels for each aspect ratio.
It cannot certify a full-length source-footage trailer or game-release parity.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "assets/promo/canonical"
FORMATS = {
    "16x9": ("blueprint-16x9-logo-right.png", (960, 540)),
    "4x3": ("blueprint-4x3-logo-right.png", (800, 600)),
    "portrait": ("blueprint-9x16-portrait-2160x3840.png", (540, 960)),
}


def execute(*argv: str) -> None:
    subprocess.run([str(x) for x in argv], check=True)


def probe(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
        "-of", "json", str(path),
    ], text=True)
    streams = json.loads(raw)["streams"]
    if len(streams) != 1:
        raise ValueError("Expected exactly one video stream")
    return streams[0]


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    results = {}
    for label, (filename, (w, h)) in FORMATS.items():
        src = CANONICAL / filename
        if not src.is_file():
            raise FileNotFoundError(f"Approved background missing: {src}")
        with Image.open(src) as image:
            original_pixels = image.size
            if image.width * h != image.height * w:
                raise ValueError(f"Wrong aspect ratio for {src}: {image.size}")
            sampled = image.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
        cw, ch = (w * 3 // 5) & ~1, (h * 3 // 10) & ~1
        x, y = (w - cw) // 2, (h - ch) // 2
        video = out / f"{label}-approved-background-smoke.mp4"
        still = out / f"{label}-approved-background-smoke.png"
        graph = (f"[0:v]scale={w}:{h}:flags=lanczos[approved];"
                 f"[1:v]scale={cw}:{ch}:flags=neighbor,format=rgba[clip];"
                 f"[approved][clip]overlay=x={x}:y={y}:shortest=1,"
                 "format=yuv420p[v]")
        execute("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-framerate", "6", "-i", str(src),
                "-f", "lavfi", "-i", "testsrc2=size=384x216:rate=6:duration=1",
                "-filter_complex", graph, "-map", "[v]", "-frames:v", "6",
                "-r", "6", "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "17", "-pix_fmt", "yuv420p", str(video))
        details = probe(video)
        if (details["width"], details["height"], details["r_frame_rate"],
                int(details["nb_read_frames"])) != (w, h, "6/1", 6):
            raise ValueError(f"{label} encode/readback failed: {details}")
        execute("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video), "-frames:v", "1", str(still))
        with Image.open(still) as frame:
            rendered = frame.convert("RGB")
            # These corners are never overlaid. Compare with the approved
            # source to detect black padding or substituted art.
            for point in ((8, 8), (w - 9, 8), (8, h - 9), (w - 9, h - 9)):
                before = sampled.getpixel(point)
                after = rendered.getpixel(point)
                if max(abs(a-b) for a, b in zip(before, after)) > 50:
                    raise ValueError(f"{label}: background differs at {point}")
        results[label] = {"approved_source": str(src.relative_to(ROOT)),
                          "source_pixels": original_pixels,
                          "output_pixels": [w, h], "frames": 6,
                          "video": video.name, "frame": still.name,
                          "background_pixel_check": "passed"}
    (out / "promo-smoke-results.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.out), indent=2))


if __name__ == "__main__":
    main()
