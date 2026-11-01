#!/usr/bin/env python3
"""Privately re-extract exact registered original racer sprites from canonical ROM.

This is an offline opt-in source export. It reuses the existing proven ROM
composer, does not commit/redistribute original pixels and does not assert
original native PPU, final-foreground, new camera or recovered 3D geometry.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from prototype_racer_hd_replacement import build_stock_rgba
from extract_racer_presentation_family import encode_png_rgba
try:
    from tools.art.racer_source_pixels import alpha_metrics
except ModuleNotFoundError:
    from racer_source_pixels import alpha_metrics

SOURCE_REGISTRY = ROOT / "analysis/data/racer-hd-replacement-prototype.json"
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
CANONICAL_ROM_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCHEMA = "UR-RACER-ROM-COMPOSED-SOURCE-CORPUS/1"
FIRST = "first-1205-1220"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def windows_from_registry(registry: dict) -> dict:
    if registry.get("schema_version") != 1 or not isinstance(registry.get("entries"), list):
        raise ValueError("unrecognized racer source registry")
    sequences = {FIRST: registry.get("motion_review_sequence")}
    more = registry.get("motion_review_sequences")
    if not isinstance(more, dict) or FIRST in more:
        raise ValueError("invalid duplicated extra source windows")
    sequences.update(more)
    return sequences


def collect(registry: dict, render, selected_windows: list[str] | None = None) -> tuple[dict, dict]:
    """Return only metadata and derived PNG bytes, never ROM or guest memory."""
    sequences = windows_from_registry(registry)
    if selected_windows is None:
        selected_windows = sorted(sequences)
    if not selected_windows or len(set(selected_windows)) != len(selected_windows):
        raise ValueError("select at least one unique source window")
    if any(name not in sequences for name in selected_windows):
        raise ValueError("unknown source window")
    entries = registry["entries"]
    by_id = {x.get("representation_id"): x for x in entries}
    if len(by_id) != len(entries) or any(not isinstance(k, str) or not k for k in by_id):
        raise ValueError("duplicate or invalid canonical representation identity")
    selected = set()
    frames = []
    for name in selected_windows:
        sequence = sequences[name]
        if not isinstance(sequence, dict) or not isinstance(sequence.get("frames"), list):
            raise ValueError("invalid source window")
        old = -1
        for f in sequence["frames"]:
            n = f.get("frame")
            if type(n) is not int or n <= old:
                raise ValueError("source frames are not strictly increasing")
            old = n
            identities = {}
            for player in ("p1", "p2"):
                rid = f.get(player + "_representation_id")
                if rid is None:
                    continue
                if rid not in by_id or by_id[rid].get("player") != player:
                    raise ValueError("unrecognized original player representation")
                selected.add(rid)
                identities[player] = rid
            if not identities:
                raise ValueError("frame lacks an authenticated representation")
            frames.append({"window": name, "guest_frame": n, "representations": identities})
        if (not sequence["frames"] or sequence["window_start"] != sequence["frames"][0]["frame"]
                or sequence["window_end"] != sequence["frames"][-1]["frame"]):
            raise ValueError("source frame window has mismatched boundary")
    assets = {}
    representations = {}
    for rid in sorted(selected):
        item = by_id[rid]
        pixels = render(item)
        if not isinstance(pixels, bytes) or len(pixels) != 64*64*4:
            raise ValueError("source ROM composer did not produce 64x64 RGBA")
        metrics = alpha_metrics(pixels, 64, 64)
        rgba_sha = metrics["source_rgba_sha256"]
        name = "stock/source-" + rgba_sha + ".png"
        if rgba_sha not in assets:
            assets[rgba_sha] = encode_png_rgba(64, 64, pixels)
        representations[rid] = {
            "player": item["player"],
            "source_rgba_sha256": rgba_sha,
            "source_alpha_sha256": metrics["source_alpha_sha256"],
            "source_binary_mask_sha256": metrics["binary_mask_sha256"],
            "source_opaque_pixels": metrics["nonzero_alpha_pixels"],
            "source_alpha_bbox_xyxy": metrics["alpha_bbox_xyxy_inclusive"],
            "local_file": name,
            "local_png_sha256": sha(assets[rgba_sha]),
        }
    families = defaultdict(list)
    for rid, info in representations.items():
        families[info["source_binary_mask_sha256"]].append(rid)
    manifest = {
        "schema": SCHEMA,
        "source_kind": "deterministic_canonical_USA_ROM_registered_composition",
        "source_rom_sha256": CANONICAL_ROM_SHA256,
        "registered_source_windows": list(selected_windows),
        "source_temporal_frame_observations": frames,
        "source_representations": representations,
        "identical_original_binary_silhouette_groups": {
            h: sorted(ids) for h, ids in sorted(families.items())
        },
        "unique_representations": len(representations),
        "unique_rgba_images": len(assets),
        "unique_binary_silhouettes": len(families),
        "source_rom_verified_and_used_for_composition": False,
        "native_live_original_PPU_or_1994_3d_camera_independently_verified": False,
        "source_3d_geometry_recovered": False,
        "original_sprite_pixels_publicly_distributable": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }
    return manifest, assets


def verify_retained_first_family(manifest: dict) -> None:
    """Cross-check independent existing 2026 original-source review hashes."""
    if FIRST not in manifest["registered_source_windows"]:
        return
    first_frames = {f["guest_frame"]: f for f in manifest["source_temporal_frame_observations"]
                    if f["window"] == FIRST}
    for player in ("p1", "p2"):
        path = ROOT / f"media/showcase/art-reconstruction/2026-10-10/inputs-{player}.json"
        review = json.loads(path.read_text(encoding="utf-8"))
        if (review.get("player") != player or review.get("source_rom_sha256") != CANONICAL_ROM_SHA256
                or review.get("window") != [1205, 1220]):
            raise ValueError("original review witness identity changed")
        if len(review["frames"]) != 16:
            raise ValueError("original source review witness frame count changed")
        for f in review["frames"]:
            original = first_frames.get(f["frame"])
            if original is None:
                raise ValueError("missing first-family source")
            rid = original["representations"].get(player)
            metrics = manifest["source_representations"].get(rid)
            if (rid != f["registered_representation_id"] or
                    metrics is None or metrics["source_rgba_sha256"] != f["stock_rgba_sha256"]):
                raise ValueError("fresh canonical ROM source differs from retained original evidence")


def publish_private_corpus_stage(stage: Path, out: Path) -> None:
    """Claim destination exclusively; publish receipt last with no replacements.

    A complete directory cannot be atomically renamed with portable no-replace
    semantics on every supported filesystem. Instead, exclusively create the
    target, hardlink already-complete immutable files on the SAME filesystem,
    and make source-corpus.json visible as the LAST atomic hardlink. If linking
    is unsupported, fail closed and leave a receipt-less incomplete directory,
    never overwrite a foreign destination or return success.
    """
    original_images = stage / "stock"
    receipt = stage / "source-corpus.json"
    if not original_images.is_dir() or not receipt.is_file():
        raise ValueError("missing completed staged source corpus")
    # Only create the new path; unlike POSIX rename this cannot replace a
    # concurrent, preexisting EMPTY directory, symlink or foreign path.
    out.mkdir(mode=0o700, exist_ok=False)
    stock = out / "stock"
    stock.mkdir(mode=0o700, exist_ok=False)
    for image in sorted(original_images.iterdir()):
        if (not image.is_file() or image.is_symlink() or
                not image.name.startswith("source-") or
                len(image.name) != len("source-") + 64 + len(".png") or
                not image.name.endswith(".png") or
                any(c not in "0123456789abcdef" for c in image.name[7:-4])):
            raise ValueError("staged source image name or identity is invalid")
        os.link(image, stock / image.name, follow_symlinks=False)
    # The single receipt is the read-completion signal. It is linked only
    # after *every* original PNG was successfully published.
    with receipt.open("rb") as fp:
        os.fsync(fp.fileno())
    os.link(receipt, out / "source-corpus.json", follow_symlinks=False)


def export(rom_path: Path, registry_path: Path, out: Path,
           selected_windows: list[str] | None = None) -> dict:
    # Source sprite pixels belong in an explicitly private scratch location.
    # Never populate even an ignored directory inside the public checkout.
    if out.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("original source corpus output must be outside repository")
    if out.exists():
        raise ValueError("destination exists; use a new private immutable corpus directory")
    raw_rom = rom_path.read_bytes()
    if len(raw_rom) != 2097152 or sha(raw_rom) != CANONICAL_ROM_SHA256:
        raise ValueError("canonical USA ROM bytes/SHA256 do not match")
    raw_registry = registry_path.read_bytes()
    registry = json.loads(raw_registry)
    manifest, assets = collect(registry, lambda entry: build_stock_rgba(raw_rom, entry),
                               selected_windows)
    verify_retained_first_family(manifest)
    manifest["source_rom_verified_and_used_for_composition"] = True
    manifest["source_registry_sha256"] = sha(raw_registry)
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".ur-racer-rom-source-", dir=out.parent))
    try:
        (stage / "stock").mkdir()
        for rgba_sha, png in assets.items():
            (stage / "stock" / ("source-" + rgba_sha + ".png")).write_bytes(png)
        (stage / "source-corpus.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        publish_private_corpus_stage(stage, out)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROM)
    parser.add_argument("--registry", type=Path, default=SOURCE_REGISTRY)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--window", action="append", dest="windows",
                        help="Repeat to select exact registry windows; default all windows")
    args = parser.parse_args()
    result = export(args.rom, args.registry, args.out, args.windows)
    print(json.dumps({
        "schema": result["schema"],
        "output_directory": str(args.out),
        "source_registry_sha256": result["source_registry_sha256"],
        "unique_representations": result["unique_representations"],
        "unique_rgba_images": result["unique_rgba_images"],
        "unique_binary_silhouettes": result["unique_binary_silhouettes"],
        "native_live_original_PPU_or_1994_3d_camera_independently_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }, indent=2))


if __name__ == "__main__":
    main()
