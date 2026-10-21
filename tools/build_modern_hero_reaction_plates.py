#!/usr/bin/env python3
"""Privately rasterize *registered* original-ROM Modern hero reaction candidates.

This is an OFFLINE research producer. It never edits host/game/guest code or
embeds the original raster in a checked-in artifact. A real canonical USA ROM
must be explicitly supplied. Original physical/menu sprite timing and art
approval require independent review of the output, not this generator's word.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.audit_modern_hero_source_clips import (
    CANONICAL_USA_SHA256, CANDIDATES, ClipAdmissionError, REGISTRY,
    SOURCE, inspect_clip,
)
from tools.prototype_racer_hd_replacement import (
    alpha_bounds, alpha_contact_anchor_x2_y2, build_stock_rgba,
    encode_png_rgba, object_flip_pivot_x2_y2,
)

W = H = 64
MAX_ROM_BYTES = 3 * 1024 * 1024
SOURCE_CLIPS = {s[0]: s for s in CANDIDATES[1:]}


def rasterize_original_clip(
    rom: bytes, registry: dict, source: dict, clip_id: str
) -> tuple[dict, list[bytes]]:
    if clip_id not in SOURCE_CLIPS:
        raise ClipAdmissionError("only separately registered reaction/hold clips are permitted")
    if len(rom) != 2_097_152 or len(rom) > MAX_ROM_BYTES or (
            hashlib.sha256(rom).hexdigest() != CANONICAL_USA_SHA256):
        raise ClipAdmissionError("canonical USA retail ROM bytes required")
    clip = inspect_clip(registry, source, SOURCE_CLIPS[clip_id])
    entry_map = {e["representation_id"]: e for e in registry["entries"]}
    if len(entry_map) != len(registry["entries"]):
        raise ClipAdmissionError("ambiguous original pose register")

    frames = []
    results = []
    for registered in clip["registered_stock_p1_composition"]:
        entry = entry_map[registered["representation_id"]]
        rgba = build_stock_rgba(rom, entry)
        if len(rgba) != W * H * 4:
            raise ClipAdmissionError("original raster is not a 64x64 RGBA frame")
        pixels = sum(rgba[i] != 0 for i in range(3, len(rgba), 4))
        if not 100 <= pixels <= 2000:
            raise ClipAdmissionError("original alpha occupancy is not a useful racer")
        anchors = entry.get("registration", {}).get("semantic_anchors", {})
        if anchors.get("fixed_point_scale") != 2 or (
                alpha_contact_anchor_x2_y2(rgba, W, H) !=
                anchors.get("wheel_contact_x2_y2")) or (
                anchors.get("flip_pivot_x2_y2") !=
                object_flip_pivot_x2_y2(W, H)):
            raise ClipAdmissionError("original registered wheel contact or pivot mismatch")
        frames.append(rgba)
        results.append({
            "registered_guest_frame": registered["registered_guest_frame"],
            "representation_id": registered["representation_id"],
            "p1_semantic_id": registered["p1_semantic_id"],
            "original_rgba_sha256": hashlib.sha256(rgba).hexdigest(),
            "original_alpha_bounds": alpha_bounds(rgba, W, H),
            "opaque_pixels": pixels,
            "wheel_contact_x2_y2": anchors["wheel_contact_x2_y2"],
            "flip_pivot_x2_y2": anchors["flip_pivot_x2_y2"],
        })
    if len(set(row["original_rgba_sha256"] for row in results)) < 2:
        raise ClipAdmissionError("candidate contains no distinguishable original raster reaction")
    # A repeated registered representation must be byte-identical under the
    # exact ROM/palette/companion renderer; fail if provenance drifts.
    hashes: dict[str, str] = {}
    for row in results:
        prior = hashes.setdefault(row["representation_id"],
                                  row["original_rgba_sha256"])
        if prior != row["original_rgba_sha256"]:
            raise ClipAdmissionError("same source representation changed raster across guest frames")
    return {
        "schema_version": 1,
        "status": "original ROM P1 reconstruction; preview only, not menu animation acceptance",
        "clip": clip,
        "canonical_rom_sha256": CANONICAL_USA_SHA256,
        "format": "original 64x64 RGBA8888, not procedural 4x art",
        "native_hero_admitted": False,
        "may_reverse_or_loop": False,
        "frames": results,
    }, frames


def write_private_review(
    report: dict, frames: list[bytes], out_dir: Path
) -> Path:
    if not frames or len(frames) != len(report["frames"]):
        raise ClipAdmissionError("incomplete source raster sequence")
    # Encode everything *before* writing; a malformed frame must not leave
    # a partly published source-art review directory.
    images = [
        encode_png_rgba(W, H, rgba)
        for rgba in frames
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    for row, png in zip(report["frames"], images):
        path = out_dir / f"original-guest-{row['registered_guest_frame']:04d}.png"
        path.write_bytes(png)
        row["review_png_sha256"] = hashlib.sha256(png).hexdigest()
    path = out_dir / "original-hero-reaction-manifest.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--clip", choices=tuple(SOURCE_CLIPS), required=True)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="Private temp path outside the repository")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not args.rom.is_file() or args.rom.stat().st_size > MAX_ROM_BYTES:
        raise ClipAdmissionError("source ROM missing or oversized")
    receipt, frames = rasterize_original_clip(
        args.rom.read_bytes(), registry, source, args.clip)
    print(write_private_review(receipt, frames, args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
