#!/usr/bin/env python3
"""Measure SHA-verified original 64x64 first-family upper/lower pixel masses.

This is source-raster morphology, not an original 3D mesh, camera or pose map.
Windows are intentionally frozen to guest frames 1205..1220, not generalised
to arbitrary stunt families or high-detail marketing illustrations.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.art.build_racer_source_pixel_corpus import build, STRIP, REGISTRY, _stock_path
    from tools.art.racer_source_pixels import decode_rgba_png
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build, STRIP, REGISTRY, _stock_path
    from racer_source_pixels import decode_rgba_png
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-FIRST-FAMILY-PROJECTED-MASSES/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FRAMES = range(1205, 1221)
PAR = 7 / 6
UPPER = (0, 9)
LOWER = (22, 38)


def raster_masses(rgba: bytes) -> dict:
    """Measure exact original unscaled pixels in two declared row windows."""
    if not isinstance(rgba, bytes) or len(rgba) != 64 * 64 * 4:
        raise ValueError("expected original unrescaled 64x64 RGBA")
    alpha = rgba[3::4]
    if any(a not in (0, 255) for a in alpha):
        raise ValueError("source silhouette has nonbinary alpha")

    def bbox(top, bottom):
        points = [(x, y) for y in range(top, bottom + 1) for x in range(64)
                  if alpha[y * 64 + x]]
        if not points:
            raise ValueError("empty projected mass window")
        return [min(x for x, _ in points), min(y for _, y in points),
                max(x for x, _ in points), max(y for _, y in points)]

    up, low, full = bbox(*UPPER), bbox(*LOWER), bbox(0, 63)
    uw, uh = up[2] - up[0] + 1, up[3] - up[1] + 1
    lw, lh = low[2] - low[0] + 1, low[3] - low[1] + 1
    if (full[1] < 2 or full[3] != 38 or low[1] != 22
            or not 10 <= uw <= 23 or not 14 <= lw <= 24):
        raise ValueError("not the verified ordinary-racer first-family morphology")
    ucx, lcx = (up[0] + up[2]) / 2, (low[0] + low[2]) / 2
    ucy, lcy = (up[1] + up[3]) / 2, (low[1] + low[3]) / 2
    return {
        "upper_source_bbox_xyxy_inclusive": up,
        "lower_source_bbox_xyxy_inclusive": low,
        "full_source_bbox_xyxy_inclusive": full,
        "upper_size_source_logical_pixels": [uw, uh],
        "lower_size_source_logical_pixels": [lw, lh],
        "physical_7_6_projected_ratios": {
            "upper_width_over_lower_height": round(uw * PAR / lh, 6),
            "lower_width_over_lower_height": round(lw * PAR / lh, 6),
            "upper_center_x_minus_lower_center_x_over_lower_height":
                round((ucx - lcx) * PAR / lh, 6),
            "lower_center_y_minus_upper_center_y_over_lower_height":
                round((lcy - ucy) / lh, 6),
            "intermass_clear_rows_over_lower_height":
                round((low[1] - up[3] - 1) / lh, 6),
        },
    }


def reduce_authenticated_observations(corpus: dict, load_rgba) -> dict:
    """Weight independent original binary masks once, never temporal holds."""
    if (corpus.get("schema") != "UR-RACER-SOURCE-PIXEL-CORPUS/1"
            or corpus.get("historical_manifest_declared_rom_sha256") != ROM_SHA
            or corpus.get("frame_observation_count") != 32
            or corpus.get("distinct_binary_silhouette_groups") != 10
            or corpus.get("decoded_png_rgba_sha_verified_against_review_manifest") is not True):
        raise ValueError("unverified first-family original source corpus")
    observations = corpus.get("observations")
    if not isinstance(observations, list) or len(observations) != 32:
        raise ValueError("missing original 32 player/frame observations")
    frames = defaultdict(set)
    groups = defaultdict(list)
    image_identity = {}
    for obs in observations:
        player, frame = obs.get("player"), obs.get("guest_frame")
        if (player not in ("p1", "p2") or type(frame) is not int
                or frame not in FRAMES or frame in frames[player]):
            raise ValueError("invalid/duplicate player and source frame")
        frames[player].add(frame)
        source = obs.get("source_image")
        if not isinstance(source, str) or not source:
            raise ValueError("missing original source PNG identity")
        rgba, file_sha = load_rgba(obs)
        if (file_sha != obs.get("png_file_sha256") or
                hashlib.sha256(rgba).hexdigest() != obs.get("source_rgba_sha256")):
            raise ValueError("original source PNG/RGBA SHA mismatch")
        measured = raster_masses(rgba)
        mask = bytes(int(a != 0) for a in rgba[3::4])
        mask_sha = hashlib.sha256(mask).hexdigest()
        if mask_sha != obs.get("binary_mask_sha256"):
            raise ValueError("original binary-mask SHA mismatch")
        previous = image_identity.setdefault(source, (file_sha, obs["source_rgba_sha256"]))
        if previous != (file_sha, obs["source_rgba_sha256"]):
            raise ValueError("one source image identity has contradictory bytes")
        groups[(player, mask_sha)].append((frame, obs, measured))
    if (any(frames[p] != set(FRAMES) for p in ("p1", "p2"))
            or len(groups) != 10
            or len({mask for _, mask in groups}) != 10
            or {p: sum(k[0] == p for k in groups) for p in ("p1", "p2")}
               != {"p1": 6, "p2": 4}):
        raise ValueError("authentic first-family source shape census changed")
    result = []
    for (player, mask_sha), entries in sorted(groups.items()):
        first = entries[0][2]
        if any(x[2] != first for x in entries[1:]):
            raise ValueError("same source mask measured inconsistently")
        result.append({
            "player": player, "binary_mask_sha256": mask_sha,
            "guest_frames": [x[0] for x in entries],
            "source_rgba_sha256": sorted({x[1]["source_rgba_sha256"] for x in entries}),
            "source_png_sha256": sorted({x[1]["png_file_sha256"] for x in entries}),
            "measurements": first,
        })
    summary = {}
    for player in ("p1", "p2"):
        unique = [x for x in result if x["player"] == player]
        keys = unique[0]["measurements"]["physical_7_6_projected_ratios"]
        summary[player] = {
            "independent_silhouettes": len(unique),
            "one_vote_per_binary_mask_means": {
                k: round(sum(x["measurements"]["physical_7_6_projected_ratios"][k]
                             for x in unique) / len(unique), 6)
                for k in keys
            },
        }
    return {
        "schema": SCHEMA, "historical_original_rom_sha256": ROM_SHA,
        "source_registry_sha256": corpus.get("source_registry_current_sha256"),
        "source_review_manifest_sha256": corpus.get("showcase_manifest_sha256"),
        "source_kind": "authenticated already-retained original ROM-composed PNG",
        "original_rom_reextracted_this_run": False,
        "first_family_guest_frames": [1205, 1220],
        "logical_canvas": [64, 64], "pixel_aspect": "7:6",
        "upper_row_window_inclusive": list(UPPER),
        "lower_row_window_inclusive": list(LOWER),
        "window_semantics": "upper/lower pixel occupancy are saddle-like/wheel-like regions, not independently segmented original 3D parts",
        "original_observations": 32, "distinct_source_png_images": len(image_identity),
        "independent_source_binary_shapes": len(result),
        "equal_weight_per_independent_mask": True, "groups": result, "summary": summary,
        "original_3d_camera_or_geometry_identified": False,
        "original_pose_to_2026_glb_pose_mapping_verified": False,
        "heldout_different_source_family_verified": False,
        "original_character_likeness_approved": False,
        "shipping_art_approved": False,
    }


def audit(strip: Path = STRIP, registry: Path = REGISTRY) -> dict:
    corpus = build(strip, registry)  # existing complete ROM/source SHA verifier
    prefix = "media/showcase/art-reconstruction/2026-10-10/stock/"
    def read(obs):
        source = obs["source_image"]
        if not isinstance(source, str) or (
                not source.startswith(prefix) and
                not re.fullmatch(r"p[12]-[0-9]{2}\.png", source)):
            raise ValueError("unexpected verified stock source path")
        file = _stock_path(strip, "stock/" + Path(source).name, obs["player"])
        width, height, rgba, sha = decode_rgba_png(file)
        if (width, height) != (64, 64):
            raise ValueError("resized original stock PNG")
        return rgba, sha
    return reduce_authenticated_observations(corpus, read)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strip", type=Path, default=STRIP)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    data = json.dumps(audit(args.strip, args.registry), indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, data)
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
