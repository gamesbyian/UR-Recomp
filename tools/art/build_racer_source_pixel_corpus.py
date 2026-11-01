#!/usr/bin/env python3
"""Audit source PIXELS in retained original-racer 1205-1220 review strips.

Metadata records alone cannot establish image equality. Verify lossless 64x64
stock PNG pixel digests against original ROM-composition review manifests;
group duplicate RGBA, binary silhouettes and true temporal changes. This
does not re-run the ROM or prove independent 3D viewpoints/artist approval.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.racer_source_pixels import alpha_metrics, decode_rgba_png
except ModuleNotFoundError:
    from racer_source_pixels import alpha_metrics, decode_rgba_png

SCHEMA = "UR-RACER-SOURCE-PIXEL-CORPUS/1"
ROOT = Path(__file__).resolve().parents[2]
STRIP = ROOT / "media/showcase/art-reconstruction/2026-10-10"
REGISTRY = ROOT / "analysis/data/racer-hd-replacement-prototype.json"
PLAYERS = ("p1", "p2")
WINDOW = list(range(1205, 1221))


def _load_manifest(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _stock_path(strip: Path, name: str, player: str) -> Path:
    part = Path(name)
    if (part.is_absolute() or len(part.parts) != 2 or
            part.parts[0] != "stock" or part.parts[1] != player + "-" + part.parts[1].split("-", 1)[-1] or
            not part.name.endswith(".png") or
            not part.name.startswith(player + "-")):
        raise ValueError("unsafe or wrong-player stock image path")
    full = strip / part
    if not full.resolve().is_relative_to(strip.resolve()):
        raise ValueError("stock path escapes review strip")
    return full


def _changed_pixels(first: bytes, second: bytes) -> tuple[int, int]:
    if len(first) != len(second) or len(first) % 4:
        raise ValueError("incompatible source raster")
    mask_diff = color_diff = 0
    for index in range(0, len(first), 4):
        mask_diff += (first[index+3] != 0) != (second[index+3] != 0)
        color_diff += first[index:index+4] != second[index:index+4]
    return mask_diff, color_diff


def build(strip: Path = STRIP, registry_path: Path = REGISTRY) -> dict:
    registry, registry_hash = _load_manifest(registry_path)
    if registry.get("schema_version") != 1:
        raise ValueError("unexpected registration schema")
    identities = {x["representation_id"]: x["player"] for x in registry["entries"]}
    if len(identities) != len(registry["entries"]):
        raise ValueError("ambiguous original representation IDs")
    seq = registry["motion_review_sequence"]
    source_frames = {frame["frame"]: frame for frame in seq["frames"]}
    if len(source_frames) != len(seq["frames"]) or sorted(source_frames) != WINDOW:
        raise ValueError("original first-family frame range changed")
    observations, transitions, manifest_hashes = [], [], {}
    loaded = {}
    source_rom_sha256 = None
    for player in PLAYERS:
        manifest_file = strip / ("inputs-" + player + ".json")
        manifest, manifest_hashes[player] = _load_manifest(manifest_file)
        if (manifest.get("schema_version") != 1 or
                manifest.get("kind") != "ordered-evidence-backed-editorial-sprite-strip" or
                manifest.get("window") != [1205, 1220] or
                manifest.get("player") != player or
                manifest.get("source") != "analysis/data/racer-hd-replacement-prototype.json::motion_review_sequence" or
                len(manifest.get("frames", [])) != len(WINDOW)):
            raise ValueError("unexpected original source review manifest")
        declared_rom = manifest["source_rom_sha256"]
        if source_rom_sha256 is None:
            source_rom_sha256 = declared_rom
        if declared_rom != source_rom_sha256 or len(declared_rom) != 64:
            raise ValueError("different original USA ROM identity")
        prior_pixels = None
        for expected_frame, entry in zip(WINDOW, manifest["frames"]):
            if entry["frame"] != expected_frame or entry["player"] != player:
                raise ValueError("misordered original source frames")
            registered_id = entry["registered_representation_id"]
            if (identities.get(registered_id) != player or
                    source_frames[expected_frame][player + "_representation_id"] != registered_id):
                raise ValueError("wrong or unknown registered source representation")
            path = _stock_path(strip, entry["stock_png"], player)
            if path not in loaded:
                w, h, pixels, png_sha = decode_rgba_png(path)
                if (w, h) != (64, 64):
                    raise ValueError("original stock must remain an unrescaled 64x64 raster")
                loaded[path] = (pixels, png_sha, alpha_metrics(pixels, w, h))
            pixels, png_sha, metrics = loaded[path]
            if entry["stock_rgba_sha256"] != metrics["source_rgba_sha256"]:
                raise ValueError("source PNG pixels disagree with recorded ROM-composed RGBA SHA")
            observations.append({
                "player": player, "guest_frame": expected_frame,
                "representation_id": registered_id,
                "editorial_representation_id": entry["representation_id"],
                "source_image": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
                "png_file_sha256": png_sha, **metrics,
            })
            if prior_pixels is not None:
                alpha_diff, rgba_diff = _changed_pixels(prior_pixels, pixels)
                transitions.append({
                    "player": player, "from_frame": expected_frame-1,
                    "to_frame": expected_frame,
                    "binary_mask_changed_pixels": alpha_diff,
                    "source_rgba_changed_pixels": rgba_diff,
                })
            prior_pixels = pixels
    by_raw = defaultdict(list)
    by_mask = defaultdict(list)
    for obs in observations:
        by_raw[obs["source_rgba_sha256"]].append(obs["player"] + ":" + str(obs["guest_frame"]))
        by_mask[obs["binary_mask_sha256"]].append(obs["player"] + ":" + str(obs["guest_frame"]))
    return {
        "schema": SCHEMA,
        "source_registry_current_sha256": registry_hash,
        "showcase_manifest_sha256": manifest_hashes,
        "historical_manifest_declared_rom_sha256": source_rom_sha256,
        "source_pixel_input_kind": "retained_original_ROM_composed_review_PNG",
        "decoded_png_rgba_sha_verified_against_review_manifest": True,
        "source_rom_reextracted_in_this_run": False,
        "independent_original_3d_camera_verified": False,
        "distinct_source_pose_family_holdout_verified": False,
        "current_likeness_approved": False,
        "shipping_art_approved": False,
        "frame_observation_count": len(observations),
        "distinct_png_file_count": len(loaded),
        "distinct_rgba_pixel_groups": len(by_raw),
        "distinct_binary_silhouette_groups": len(by_mask),
        "rgba_pixel_equivalence_groups": {
            k: v for k, v in sorted(by_raw.items())
        },
        "binary_silhouette_equivalence_groups": {
            k: v for k, v in sorted(by_mask.items())
        },
        "observations": observations,
        "transitions": transitions,
        "validation_note": (
            "These are verified bytes of already-retained ROM-composed PNGs, not "
            "a fresh original-ROM/PPU run. Palette-independent shape equality is "
            "2D alpha equality, not a proven shared 3D camera or pose."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strip", type=Path, default=STRIP)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = build(args.strip, args.registry)
    result = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
