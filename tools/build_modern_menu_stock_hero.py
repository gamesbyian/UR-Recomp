#!/usr/bin/env python3
"""Reconstruct an experimental ORIGINAL-raster Modern unicycle preview.

Provenance: the exact eight consecutive source-visible guest frames 1213..1220
from analysis/data/racer-hd-replacement-prototype.json. Uses the same signed-off
Original 64x64 P1 composition path as the established HD/fallback evidence,
NEVER any authored/Scale2x/procedural replacement. This is a single original
eight-frame event, not a cyclic idle animation, a title-frame pose, or approved
4x new character art.

No generated asset is committed. Only a caller explicitly supplying a verified
canonical USA retail ROM can generate a host C++ header and a source manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_modern_hero_source_clips import CANDIDATES
from build_modern_hero_reaction_plates import rasterize_original_clip
from qualify_modern_original_hero_temporal import analyze_original_hero_temporal_clip
from prototype_racer_hd_replacement import (
    alpha_contact_anchor_x2_y2,
    build_stock_rgba,
    encode_png_rgba,
    object_flip_pivot_x2_y2,
)

MANIFEST = ROOT / "analysis/data/racer-hd-replacement-prototype.json"
SOURCE = ROOT / "analysis/generated/racer-presentation-family.json"
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
WIDTH = HEIGHT = 64
START, STOP = 1213, 1220
FRAME_COUNT = STOP - START + 1
MAX_BYTES = 3 * 1024 * 1024
SOURCE_PROVENANCE = "original-synchronized-p1-guest-1213-through-1220"
# This inventory is independently registered, not a manufactured idle cycle.
# The private source reconstruction and native compositor validate the data.
CLIP_WINDOWS = {entry[0]: (entry[3], entry[4]) for entry in CANDIDATES}
DEFAULT_CLIP = "root-entry-reaction"
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211


def source_digest(argb: list[int]) -> int:
    h = FNV_OFFSET
    for p in argb:
        for shift in (24, 16, 8, 0):
            h ^= (p >> shift) & 255
            h = (h * FNV_PRIME) & ((1 << 64) - 1)
    return h


def rgba_to_argb(rgba: bytes) -> list[int]:
    if len(rgba) != WIDTH * HEIGHT * 4:
        raise ValueError("source raster must be exactly 64x64 RGBA")
    return [
        (rgba[q + 3] << 24) | (rgba[q] << 16) |
        (rgba[q + 1] << 8) | rgba[q + 2]
        for q in range(0, len(rgba), 4)
    ]


def argb_to_rgba(frame: list[int]) -> bytes:
    if len(frame) != WIDTH * HEIGHT:
        raise ValueError("source plate is not a 64x64 original raster")
    result = bytearray()
    for p in frame:
        result.extend(((p >> 16) & 255, (p >> 8) & 255,
                       p & 255, (p >> 24) & 255))
    return bytes(result)


def verified_clip(rom: bytes, registry: dict, source: dict) -> tuple[list[dict], list[list[int]]]:
    actual = hashlib.sha256(rom).hexdigest()
    if actual != source["rom_sha256"] or len(rom) != 2_097_152:
        raise ValueError("canonical USA retail ROM SHA-256 or length mismatch")
    if registry.get("schema_version") != 1:
        raise ValueError("unexpected registered source-composition schema")

    timeline = registry["motion_review_sequence"]
    if timeline["window_start"] > START or timeline["window_end"] < STOP:
        raise ValueError("requested original source window is unregistered")
    frames = [row for row in timeline["frames"]
              if START <= row["frame"] <= STOP]
    if len(frames) != FRAME_COUNT or [r["frame"] for r in frames] != list(range(START, STOP + 1)):
        raise ValueError("missing, duplicate or out-of-order genuine source frames")

    entries = {}
    for row in registry["entries"]:
        rid = row["representation_id"]
        if rid in entries:
            raise ValueError("ambiguous original pose registry ID")
        entries[rid] = row

    report = []
    buffer = []
    for row in frames:
        representation = row["p1_representation_id"]
        entry = entries.get(representation)
        if entry is None or entry.get("player") != "p1" or entry.get("palette_asset_id") != "0x06":
            raise ValueError("unknown original P1 representation or palette")
        semantic = int(entry["semantic_frame_id"], 16)
        if semantic == 0 or semantic != int(entry["composition_guards"]["p1_primary"], 16):
            raise ValueError("semantic frame disagrees with exact live P1 composition")
        rgba = build_stock_rgba(rom, entry)
        argb = rgba_to_argb(rgba)
        opaque = sum(bool(p >> 24) for p in argb)
        if opaque < 100 or opaque > 2000:
            raise ValueError("original pose alpha occupancy outside admission window")
        anchor = entry.get("registration", {}).get("semantic_anchors", {})
        stock_contact = alpha_contact_anchor_x2_y2(rgba, WIDTH, HEIGHT)
        if (anchor.get("fixed_point_scale") != 2 or
            stock_contact != anchor.get("wheel_contact_x2_y2") or
            anchor.get("flip_pivot_x2_y2") !=
                object_flip_pivot_x2_y2(WIDTH, HEIGHT)):
            raise ValueError("source Original wheel contact or flip pivot disagrees with registration")
        report.append({
            "original_guest_frame": row["frame"],
            "representation_id": representation,
            "semantic_frame_id": f"0x{semantic:04X}",
            "palette_asset_id": entry["palette_asset_id"],
            "source_rgba_sha256": hashlib.sha256(rgba).hexdigest(),
            "argb_fnv1a64": f"{source_digest(argb):016x}",
            "opaque_pixels": opaque,
            "stock_contact_x2_y2": stock_contact,
            "stock_flip_pivot_x2_y2": anchor["flip_pivot_x2_y2"],
            "composition_guards": entry["composition_guards"],
        })
        buffer.append(argb)
    if len({r["semantic_frame_id"] for r in report}) < 3:
        raise ValueError("source clip lacks qualified distinct poses")
    signatures = [r["source_rgba_sha256"] for r in report]
    # These pairs are byte-static in the measured Original guest: a single
    # semantic state is held for two consecutive 60Hz frames.
    if signatures[0] != signatures[1] or signatures[2] != signatures[3]:
        raise ValueError("Original source retained static-pose pairs diverged")
    if signatures[1] == signatures[2] or len(set(signatures)) < 3:
        raise ValueError("Original source motion unexpectedly frozen")
    return report, buffer


def original_temporal_evidence(rows: list[dict], frames: list[list[int]]) -> dict:
    """Preserve source-pixel discontinuities in the private build receipt.

    Never turn a counterfactual terminal->first seam into a loop permit, and
    never translate registered guest-frame labels into independently certified
    original menu/title 60Hz timing.
    """
    if len(rows) != len(frames) or len(rows) < 2:
        raise ValueError("source temporal evidence requires corresponding frames")
    labels = [row["original_guest_frame"] for row in rows]
    return analyze_original_hero_temporal_clip(
        [argb_to_rgba(frame) for frame in frames], labels,
        width=WIDTH, height=HEIGHT)


def cpp_header(rows: list[dict], frames: list[list[int]]) -> str:
    """Produce a single self-contained generated read-only C++17 header."""
    if len(rows) != len(frames):
        raise ValueError("incomplete source frame family")
    actual = [row.get("original_guest_frame") for row in rows]
    if not any(actual == list(range(start, stop + 1))
               for start, stop in CLIP_WINDOWS.values()):
        raise ValueError("source frame family must be one exact registered window")
    count = len(rows)
    lines = [
        "#pragma once",
        "// GENERATED from ORIGINAL USA ROM, not authored/remastered artwork.",
        f"// Experimental fixed source sequence: guest frames {actual[0]}..{actual[-1]}.",
        "// DO NOT hand-edit. Source manifest binds actual ROM, pose and palette.",
        '#include "modern_menu_stock_hero.hpp"',
        "#include <array>",
        "#include <cstdint>",
        "namespace ur::product::modern_menu_source_hero {",
        f"inline constexpr std::array<std::uint32_t, {count * WIDTH * HEIGHT}> kOriginalArgb{{{{",
    ]
    for index, frame in enumerate(frames):
        if len(frame) != WIDTH * HEIGHT:
            raise ValueError("incomplete source raster frame")
        lines.append(f"  // original guest frame {rows[index]['original_guest_frame']}")
        for i in range(0, len(frame), 8):
            lines.append("  " + ", ".join(f"0x{n:08x}u" for n in frame[i:i+8]) + ",")
    lines.extend([
        "}};",
        f"inline constexpr std::array<ModernMenuStockHeroFrame, {count}> kFrames{{{{",
    ])
    for i, row in enumerate(rows):
        semantic = row["semantic_frame_id"]
        digest = row["argb_fnv1a64"]
        lines.append(
            f"  {{kOriginalArgb.data() + {i * WIDTH * HEIGHT}, "
            f"kModernMenuStockHeroPixels, {semantic}, 0x{digest}ull, true}},")
    lines.extend([
        "}};",
        "inline constexpr ModernMenuStockHeroSequence kClip{",
        "  kFrames.data(), kFrames.size(), true};",
        "} // namespace ur::product::modern_menu_source_hero",
        "",
    ])
    return "\n".join(lines)


def publish_private_source_artifacts(
    header: bytes, receipt: bytes, plates: list[tuple[str, bytes]],
    output_header: Path, output_manifest: Path,
    frames_dir: Path | None,
) -> None:
    """Fail closed on existing evidence; stage before exposing any outputs.

    Exact original rasters may be generated at a deliberately git-ignored
    native header pathname, but earlier evidence is NEVER overwritten.
    Multiple independent output locations cannot share one atomic directory
    rename. Every individual file is published with exclusive hard-link
    creation; ordinary exceptions roll back newly created artifacts.
    """
    files = (output_header, output_manifest)
    targets = files + ((frames_dir,) if frames_dir is not None else ())
    resolved = [path.resolve() for path in targets]
    if len(set(resolved)) != len(resolved):
        raise ValueError("source header, manifest and plates must have distinct destinations")
    if frames_dir is not None:
        plate_root = frames_dir.resolve()
        for file in files:
            if plate_root in file.resolve().parents:
                raise ValueError("individual output file cannot live inside new plates directory")
    for target in targets:
        if target.exists() or target.is_symlink():
            raise ValueError("source artifact destination already exists; refuse overwrite")
    if any(not isinstance(name, str) or
           not name.startswith("original-stock-") or
           not name.endswith(".png") or
           "/" in name or "\\" in name or
           name in (".", "..") or
           not isinstance(data, bytes)
           for name, data in plates):
        raise ValueError("malformed original source review plate")
    if len({name for name, _ in plates}) != len(plates):
        raise ValueError("duplicate original source review plate")
    if frames_dir is None and plates:
        raise ValueError("review plates supplied without destination")
    # Construct and stage all outputs before any final name appears.
    staged_files: list[Path] = []
    # Record exact staging inodes: never unlink a concurrently replaced output.
    written: list[tuple[Path, Path]] = []
    staged_dir: Path | None = None
    dir_published = False
    try:
        for destination, data in zip(files, (header, receipt)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".original-source-staging-",
                dir=destination.parent, delete=False
            ) as handle:
                staged_files.append(Path(handle.name))
                handle.write(data)
        if frames_dir is not None:
            frames_dir.parent.mkdir(parents=True, exist_ok=True)
            staged_dir = Path(tempfile.mkdtemp(
                prefix=".original-plates-staging-", dir=frames_dir.parent))
            for name, data in plates:
                (staged_dir / name).write_bytes(data)
        # Link to an absent name, never rename over a newer user file.
        # Hard-links are on each target's own filesystem by construction.
        for staged, destination in zip(staged_files, files):
            os.link(staged, destination)
            written.append((destination, staged))
        if staged_dir is not None:
            # Claim a *new* directory exclusively. An ordinary directory
            # rename can replace a concurrently created empty directory on
            # POSIX; mkdir fails instead of erasing another run's evidence.
            frames_dir.mkdir(exist_ok=False)
            dir_published = True
            for name, _ in plates:
                staged_plate = staged_dir / name
                published_plate = frames_dir / name
                os.link(staged_plate, published_plate)
                written.append((published_plate, staged_plate))
    except BaseException:
        # A second process can claim or replace a published name after our
        # hard link. Undo only links still pointing at OUR staged inode.
        # This is best-effort per-file rollback, not a cross-process
        # transaction or a substitute for Windows opened-handle binding.
        for destination, staged in reversed(written):
            try:
                current = os.lstat(destination)
                owned = os.lstat(staged)
            except FileNotFoundError:
                continue
            if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                destination.unlink(missing_ok=True)
        if dir_published and frames_dir is not None:
            # Never recursively erase content a concurrent user placed in
            # the freshly claimed folder. An occupied folder is evidence
            # worth preserving; rmdir succeeds only when it is empty.
            try:
                frames_dir.rmdir()
            except OSError:
                pass
        raise
    finally:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
        if staged_dir is not None and staged_dir.exists():
            shutil.rmtree(staged_dir, ignore_errors=True)


def build(rom_path: Path, output_header: Path, output_manifest: Path,
          frames_dir: Path | None = None,
          clip_id: str = DEFAULT_CLIP) -> dict:
    if clip_id not in CLIP_WINDOWS:
        raise ValueError("unregistered original source clip")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    registry = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not rom_path.is_file() or rom_path.stat().st_size > MAX_BYTES:
        raise ValueError("missing or oversized source ROM")
    rom = rom_path.read_bytes()
    reaction_metrics = None
    if clip_id == DEFAULT_CLIP:
        rows, frames = verified_clip(rom, registry, source)
    else:
        # Reuse the separate original-register/temporal/raster qualification
        # producer. No second raster decoder or user-authored poses.
        reaction, rgba_frames = rasterize_original_clip(
            rom, registry, source, clip_id)
        reaction_metrics = reaction["temporal_original_raster_metrics"]
        rows, frames = [], []
        for candidate, rgba in zip(reaction["frames"], rgba_frames):
            argb = rgba_to_argb(rgba)
            rows.append({
                "original_guest_frame": candidate["registered_guest_frame"],
                "representation_id": candidate["representation_id"],
                "semantic_frame_id": candidate["p1_semantic_id"],
                "palette_asset_id": "0x06",
                "source_rgba_sha256": candidate["original_rgba_sha256"],
                "argb_fnv1a64": f"{source_digest(argb):016x}",
                "opaque_pixels": candidate["opaque_pixels"],
                "stock_contact_x2_y2": candidate["wheel_contact_x2_y2"],
                "stock_flip_pivot_x2_y2": candidate["flip_pivot_x2_y2"],
            })
            frames.append(argb)
        if len(rows) != CLIP_WINDOWS[clip_id][1] - CLIP_WINDOWS[clip_id][0] + 1:
            raise ValueError("registered source reaction length mismatch")
    header = cpp_header(rows, frames)
    temporal = original_temporal_evidence(rows, frames)
    # The separate original-raster reaction producer and this generated
    # native-header path must agree on every source pose transition, including
    # the deliberately unobserved last->first counterfactual edge.
    if reaction_metrics is not None and temporal != reaction_metrics:
        raise ValueError("source-raster temporal receipt mismatch")
    manifest = {
        "schema_version": 1,
        "asset_kind": "experimental_original_native_menu_showroom_clip",
        "status": "technical Original sprite reconstruction only; user visual acceptance pending",
        "original_rom_sha256": source["rom_sha256"],
        "original_motion_window": list(CLIP_WINDOWS[clip_id]),
        "clip_id": clip_id,
        "source_guest_timing_independently_certified": False,
        "source_clip_loop_certified": False,
        "human_visual_approval": False,
        "temporal_original_raster_metrics": temporal,
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "composition_register": MANIFEST.relative_to(ROOT).as_posix(),
        "sequence_contract": "one-shot original guest 60Hz P1 frames; never loop as if original idle",
        "raster": {"width": WIDTH, "height": HEIGHT, "format": "ARGB8888"},
        "generated_header_sha256": hashlib.sha256(header.encode()).hexdigest(),
        "frames": rows,
    }
    plates: list[tuple[str, bytes]] = []
    if frames_dir is not None:
        for row, argb in zip(rows, frames):
            png = encode_png_rgba(WIDTH, HEIGHT, argb_to_rgba(argb))
            name = f"original-stock-{row['original_guest_frame']:04d}.png"
            plates.append((name, png))
            row["review_png_sha256"] = hashlib.sha256(png).hexdigest()
        # Retain original source SHA fingerprints in the same manifest.
        manifest["frames"] = rows
    receipt = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    publish_private_source_artifacts(
        header.encode("utf-8"), receipt, plates,
        output_header, output_manifest, frames_dir)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROM)
    parser.add_argument("--header", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path, help="Optional original-raster review PNGs; not native screenshot evidence")
    parser.add_argument("--clip", choices=sorted(CLIP_WINDOWS), default=DEFAULT_CLIP,
                        help="One exact registered source event; never loop or reverse")
    args = parser.parse_args()
    result = build(args.rom, args.header, args.manifest, args.frames_dir,
                   clip_id=args.clip)
    print("ORIGINAL_MENU_HERO_EXPERIMENTAL_OK frames=" +
          str(len(result["frames"])) + " source=" + result["clip_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
