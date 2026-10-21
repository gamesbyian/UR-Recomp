#!/usr/bin/env python3
"""Privately rasterize *registered* original-ROM Modern hero reaction candidates.

This is an OFFLINE research producer. It never edits host/game/guest code or
embeds the original raster in a checked-in artifact. A real canonical USA ROM
must be explicitly supplied. Original physical/menu sprite timing and art
approval require independent review of the output, not this generator's word.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

# Support both tests importing tools.* and direct `python3 tools/<script>.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_modern_hero_source_clips import (
    CANONICAL_USA_SHA256, CANDIDATES, ClipAdmissionError, REGISTRY,
    ROOT, SOURCE, inspect_clip,
)
from tools.qualify_modern_original_hero_temporal import (
    analyze_original_hero_temporal_clip,
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
    temporal_metrics = analyze_original_hero_temporal_clip(
        frames, [row["registered_guest_frame"] for row in results],
        width=W, height=H)
    return {
        "schema_version": 1,
        "status": "original ROM P1 reconstruction; preview only, not menu animation acceptance",
        "clip": clip,
        "canonical_rom_sha256": CANONICAL_USA_SHA256,
        "format": "original 64x64 RGBA8888, not procedural 4x art",
        "native_hero_admitted": False,
        "may_reverse_or_loop": False,
        "temporal_original_raster_metrics": temporal_metrics,
        "frames": results,
    }, frames


def require_private_output_dir(out_dir: Path) -> Path:
    # Resolve existing parent symlinks too. ROM-derived plates must never be
    # deposited in the tracked source tree, even when invoked carelessly.
    # A dangling symlink resolves to its absent target and otherwise looks
    # safe to publish. Refuse it explicitly before canonicalizing paths.
    if out_dir.is_symlink():
        raise ClipAdmissionError("private review destination must not be a symlink")
    resolved = out_dir.resolve()
    root = ROOT.resolve()
    if resolved == root or root in resolved.parents:
        raise ClipAdmissionError("source art review output must be outside repository")
    return resolved


SHEET_SCALE = 4
SHEET_COLUMNS = 5
SHEET_FILENAME = "original-hero-contact-sheet-4x.png"


def nearest_original_contact_sheet(frames: list[bytes]) -> tuple[bytes, int, int]:
    """Magnify untouched 64x64 source pixels exactly 4x, in manifest order.

    No fabricated poses, blended transitions, postprocessing or background:
    canvas is transparent and unused final-row slots remain transparent.
    """
    if not 1 <= len(frames) <= 20:
        raise ClipAdmissionError("source contact sheet frame count out of bounds")
    for rgba in frames:
        if not isinstance(rgba, bytes) or len(rgba) != W * H * 4:
            raise ClipAdmissionError("malformed original 64x64 RGBA review raster")
    width = W * SHEET_SCALE * SHEET_COLUMNS
    rows = (len(frames) + SHEET_COLUMNS - 1) // SHEET_COLUMNS
    height = H * SHEET_SCALE * rows
    canvas = bytearray(width * height * 4)
    stride = width * 4
    tile_stride = W * SHEET_SCALE * 4
    for index, rgba in enumerate(frames):
        tile_x = (index % SHEET_COLUMNS) * tile_stride
        tile_y = (index // SHEET_COLUMNS) * H * SHEET_SCALE
        for source_y in range(H):
            row = rgba[source_y * W * 4:(source_y + 1) * W * 4]
            enlarged = b"".join(row[x * 4:x * 4 + 4] * SHEET_SCALE
                                for x in range(W))
            for subrow in range(SHEET_SCALE):
                pos = ((tile_y + source_y * SHEET_SCALE + subrow)
                       * stride + tile_x)
                canvas[pos:pos + tile_stride] = enlarged
    return bytes(canvas), width, height


def write_private_review(
    report: dict, frames: list[bytes], out_dir: Path
) -> Path:
    """Atomically publish ROM-derived review material to a *new* private dir.

    Existing files and symlink destinations are refused; an interrupted
    extraction leaves no partial/counterfeit review folder behind.
    """
    out_dir = require_private_output_dir(out_dir)
    if out_dir.exists() or out_dir.is_symlink():
        raise ClipAdmissionError("private review destination must be new and absent")
    if not frames or len(frames) != len(report["frames"]) or len(frames) > 20:
        raise ClipAdmissionError("incomplete source raster sequence")

    receipt = copy.deepcopy(report)
    registered = []
    images = []
    for row, rgba in zip(receipt["frames"], frames):
        if (type(row.get("registered_guest_frame")) is not int or
                row["registered_guest_frame"] < 0):
            raise ClipAdmissionError("invalid original guest-frame label")
        if (not isinstance(rgba, bytes) or len(rgba) != W * H * 4 or
                hashlib.sha256(rgba).hexdigest() !=
                row.get("original_rgba_sha256")):
            raise ClipAdmissionError("private original raster does not match source receipt")
        registered.append(row["registered_guest_frame"])
        png = encode_png_rgba(W, H, rgba)
        row["review_png_sha256"] = hashlib.sha256(png).hexdigest()
        images.append(png)
    if len(set(registered)) != len(registered):
        raise ClipAdmissionError("duplicate original guest-frame output labels")
    if registered != list(range(registered[0], registered[0] + len(registered))):
        raise ClipAdmissionError("out-of-order original guest-frame output labels")
    rgba_sheet, sheet_width, sheet_height = nearest_original_contact_sheet(frames)
    sheet_png = encode_png_rgba(sheet_width, sheet_height, rgba_sheet)
    receipt["source_contact_sheet"] = {
        "filename": SHEET_FILENAME,
        "nearest_scale": SHEET_SCALE,
        "columns": SHEET_COLUMNS,
        "source_registered_guest_frames": registered,
        "width": sheet_width,
        "height": sheet_height,
        "review_png_sha256": hashlib.sha256(sheet_png).hexdigest(),
        "source_frame_content_unchanged": True,
        "source_timing_certified": False,
        "native_screenshot": False,
        "human_visual_approval": False,
    }
    manifest_bytes = (json.dumps(receipt, indent=2) + "\n").encode("utf-8")
    # Stage every file on the destination filesystem before renaming the
    # complete directory. Existing output is never silently overwritten.
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(
        prefix=".modern-original-hero-staging-", dir=out_dir.parent))
    try:
        for row, png in zip(receipt["frames"], images):
            (staged / f"original-guest-{row['registered_guest_frame']:04d}.png").write_bytes(png)
        (staged / SHEET_FILENAME).write_bytes(sheet_png)
        (staged / "original-hero-reaction-manifest.json").write_bytes(manifest_bytes)
        if out_dir.exists() or out_dir.is_symlink():
            raise ClipAdmissionError("private review destination appeared during staging")
        os.rename(staged, out_dir)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return out_dir / "original-hero-reaction-manifest.json"


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
