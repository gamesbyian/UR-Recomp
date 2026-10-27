#!/usr/bin/env python3
"""Examine actual final flagship MP4 frames against owner-approved source art.

This is a bounded screenshot/pixel audit of existing 80s/27s videos, NOT a
substitute for editorial human review or a claim of gameplay correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "assets/promo/canonical"
SAMPLES = (
    ("ur-recomp-blue-action-80s-1080p.mp4", 17.5,
     "blueprint-16x9-logo-right.png", (1920, 1080), "wide-evidence-card"),
    ("ur-recomp-blue-action-80s-1080p.mp4", 77.0,
     "blueprint-16x9-logo-right.png", (1920, 1080), "wide-call-to-action"),
    ("ur-recomp-blue-action-27s-vertical.mp4", 1.0,
     "blueprint-9x16-portrait-2160x3840.png", (1080, 1920), "portrait-title"),
    ("ur-recomp-blue-action-27s-vertical.mp4", 25.0,
     "blueprint-9x16-portrait-2160x3840.png", (1080, 1920), "portrait-call-to-action"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def check(export: Path, out: Path) -> dict:
    receipt = json.loads((export / "flagship-provenance.json").read_text(encoding="utf-8"))
    required = {"landscape": "blueprint-16x9-logo-right.png",
                "portrait": "blueprint-9x16-portrait-2160x3840.png"}
    if receipt.get("approved_visual_assets") != required:
        raise ValueError("Source export receipt does not attest the approved artwork")
    for filename, digest in receipt["output_sha256"].items():
        candidate = export / filename
        if not candidate.is_file() or sha256(candidate) != digest:
            raise ValueError(f"Missing or modified source export: {filename}")

    out.mkdir(parents=True, exist_ok=False)
    results = []
    for filename, seconds, art, (w, h), label in SAMPLES:
        source = export / filename
        sample_path = out / (label + ".png")
        subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                        "-y", "-ss", str(seconds), "-i", str(source),
                        "-frames:v", "1", str(sample_path)], check=True)
        with Image.open(ART / art) as image:
            expected = image.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
        with Image.open(sample_path) as image:
            actual = image.convert("RGB")
            if actual.size != (w, h):
                raise ValueError(f"{label}: unexpected exported image dimensions")
            # Fixed corners are outside the actual footage overlay and title text.
            # Compare regions, not individual edge pixels, to tolerate YUV420 and
            # repeated video encoding while detecting substituted/padded artwork.
            extent = 50
            boxes = ((12, 12, 12 + extent, 12 + extent),
                     (w - 12 - extent, 12, w - 12, 12 + extent),
                     (12, h - 12 - extent, 12 + extent, h - 12),
                     (w - 12 - extent, h - 12 - extent, w - 12, h - 12))
            scores = []
            for bounds in boxes:
                difference = ImageChops.difference(expected.crop(bounds), actual.crop(bounds))
                channel_means = ImageStat.Stat(difference).mean
                score = max(channel_means)
                scores.append(round(score, 2))
            if max(scores) > 55:
                raise ValueError(f"{label}: approved background absent/altered at corners: {scores}")
        results.append({"label": label, "timestamp_seconds": seconds,
                        "approved_background": art, "sample": sample_path.name,
                        "corner_region_mean_abs_difference": scores,
                        "result": "approved-background-visible"})
    verdict = {"source_export": str(export), "samples": results,
               "source_provenance_verified": True, "claim": "automated pixel-sample acceptance only"}
    (out / "full-export-frame-review.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    return verdict


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--export", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.export, args.out), indent=2))
