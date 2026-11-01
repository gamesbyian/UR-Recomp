#!/usr/bin/env python3
"""Extract a verifiable 2D temporal motion witness from original racer sprites.

The first 16 guest frames of each P1/P2 racer are fully backed by the retained
source PNGs. This reports image geometry, holds and transitions. A source 2D
moment or silhouette change does not establish a recovered 1994 3D rig pose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.build_racer_source_pixel_corpus import build, ROOT, REGISTRY
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build, ROOT, REGISTRY
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-ORIGINAL-2D-TEMPORAL-MOTION-WITNESS/1"
FRAMES = tuple(range(1205, 1221))


def source_mask_geometry(alpha: bytes) -> dict:
    """Describe 64x64 alpha in logical and physically aspect-corrected units."""
    if len(alpha) != 4096:
        raise ValueError("original silhouette must have exactly 4096 alpha bytes")
    xs, ys = [], []
    for at, a in enumerate(alpha):
        if a:
            xs.append(at % 64)
            ys.append(at // 64)
    if not xs:
        raise ValueError("empty original source silhouette")
    n = len(xs)
    cx = sum(xs) / n
    cy = sum(ys) / n
    # Original SNES pixel aspect is 7:6; covariance uses physical X distance.
    scale_x = 7 / 6
    cov_xx = sum(((x-cx)*scale_x)**2 for x in xs)/n
    cov_yy = sum((y-cy)**2 for y in ys)/n
    cov_xy = sum(((x-cx)*scale_x)*(y-cy) for x,y in zip(xs,ys))/n
    bottom = max(ys)
    bottom_x = [x for x,y in zip(xs,ys) if y == bottom]
    return {
        "opaque_pixels": n,
        "bbox_source_logical_xyxy": [min(xs),min(ys),max(xs),max(ys)],
        "alpha_centroid_logical_xy": [round(cx,6),round(cy,6)],
        "alpha_centroid_physical_x_y": [round(cx*scale_x,6),round(cy,6)],
        "alpha_second_moment_physical_xx_xy_yy": [
            round(cov_xx,6),round(cov_xy,6),round(cov_yy,6)
        ],
        "lowest_alpha_midpoint_x2_y2": [min(bottom_x)+max(bottom_x),2*bottom],
    }


def transition(first: bytes, second: bytes, first_geom: dict, second_geom: dict) -> dict:
    """Original 2D frame-to-frame change; no generic optical flow estimate."""
    if len(first) != 4096 or len(second) != 4096:
        raise ValueError("incompatible original 64px alpha masks")
    first_mask = {i for i, a in enumerate(first) if a}
    second_mask = {i for i, a in enumerate(second) if a}
    if not first_mask or not second_mask:
        raise ValueError("empty temporal original frame")
    ci = len(first_mask & second_mask)
    cu = len(first_mask | second_mask)
    p = first_geom["alpha_centroid_logical_xy"]
    q = second_geom["alpha_centroid_logical_xy"]
    low_a = first_geom["lowest_alpha_midpoint_x2_y2"]
    low_b = second_geom["lowest_alpha_midpoint_x2_y2"]
    return {
        "original_binary_mask_overlap_iou": round(ci/cu,8),
        "binary_mask_xor_pixels": len(first_mask ^ second_mask),
        "centroid_delta_source_logical_xy": [
            round(q[0]-p[0],6),round(q[1]-p[1],6)
        ],
        "lowest_alpha_midpoint_delta_x2_y2": [
            low_b[0]-low_a[0],low_b[1]-low_a[1]
        ],
    }


def contiguous_holds(frames: list[dict], key: str) -> list[dict]:
    if not frames:
        return []
    runs = []
    for row in frames:
        value = row[key]
        if runs and runs[-1]["sha256"] == value and row["frame"] == runs[-1]["last_frame"]+1:
            runs[-1]["last_frame"] = row["frame"]
            runs[-1]["frame_count"] += 1
        else:
            runs.append({
                "first_frame": row["frame"], "last_frame": row["frame"],
                "frame_count": 1, "sha256": value
            })
    return runs


def build_witness() -> dict:
    corpus = build()  # SHA-verifies original P1 and P2 review PNGs first.
    if (corpus["frame_observation_count"] != 32 or
            corpus["decoded_png_rgba_sha_verified_against_review_manifest"] is not True or
            corpus["source_rom_reextracted_in_this_run"] is not False):
        raise ValueError("unexpected original first-family provenance")
    raw_registry = REGISTRY.read_bytes()
    if hashlib.sha256(raw_registry).hexdigest() != corpus["source_registry_current_sha256"]:
        raise ValueError("original representation registry changed during observation")
    registry = json.loads(raw_registry)
    entries = {e["representation_id"]:e for e in registry["entries"]}
    results = {}
    cache = {}
    for player in ("p1","p2"):
        original = [x for x in corpus["observations"] if x["player"] == player]
        original.sort(key=lambda x:x["guest_frame"])
        if [x["guest_frame"] for x in original] != list(FRAMES):
            raise ValueError("the authentic original temporal sequence is incomplete")
        frames = []
        changes = []
        previous_mask = previous_rgba = previous_geom = previous_binary_sha = None
        for obs in original:
            path = ROOT / obs["source_image"]
            if path not in cache:
                w,h,rgba,file_sha = decode_rgba_png(path)
                if (w,h) != (64,64):
                    raise ValueError("original temporal source was rescaled")
                cache[path] = rgba,file_sha
            rgba,file_sha = cache[path]
            metrics = alpha_metrics(rgba,64,64)
            if (file_sha != obs["png_file_sha256"] or
                    metrics["source_rgba_sha256"] != obs["source_rgba_sha256"] or
                    metrics["binary_mask_sha256"] != obs["binary_mask_sha256"]):
                raise ValueError("original source pixel identity changed")
            geom = source_mask_geometry(rgba[3::4])
            ident = obs["representation_id"]
            info = entries.get(ident)
            anchor = (info or {}).get("registration",{}).get(
                "semantic_anchors",{}).get("wheel_contact_x2_y2")
            if (not isinstance(anchor,list) or
                    anchor != geom["lowest_alpha_midpoint_x2_y2"] or
                    info.get("player") != player):
                raise ValueError("original game contact register mismatches source visible alpha")
            row = {
                "frame":obs["guest_frame"],
                "representation_id":ident,
                "original_png_sha256":file_sha,
                "source_rgba_sha256":metrics["source_rgba_sha256"],
                "source_binary_mask_sha256":metrics["binary_mask_sha256"],
                **geom
            }
            frames.append(row)
            if previous_mask is not None:
                delta=transition(previous_mask,rgba[3::4],previous_geom,geom)
                changes.append({
                    "from_frame":obs["guest_frame"]-1,
                    "to_frame":obs["guest_frame"],
                    "original_full_rgba_unchanged":previous_rgba==rgba,
                    "original_alpha_silhouette_unchanged":(
                        previous_binary_sha == metrics["binary_mask_sha256"]),
                    **delta
                })
            previous_mask = rgba[3::4]
            previous_rgba = rgba
            previous_geom = geom
            previous_binary_sha = metrics["binary_mask_sha256"]
        results[player] = {
            "frames":frames,
            "frame_transitions":changes,
            "source_rgba_hold_runs":contiguous_holds(frames,"source_rgba_sha256"),
            "source_binary_silhouette_hold_runs":contiguous_holds(frames,"source_binary_mask_sha256"),
            "distinct_original_binary_masks":len({x["source_binary_mask_sha256"] for x in frames}),
            "unchanged_binary_transitions":sum(x["original_alpha_silhouette_unchanged"] for x in changes),
            "changed_binary_transitions":sum(not x["original_alpha_silhouette_unchanged"] for x in changes)
        }
    return {
        "schema": SCHEMA,
        "source_kind":"original_1994_ROM_composed_retained_64x64_raster",
        "source_rom_sha256":corpus["historical_manifest_declared_rom_sha256"],
        "original_source_registry_sha256":corpus["source_registry_current_sha256"],
        "source_review_manifest_sha256":corpus["showcase_manifest_sha256"],
        "source_logical_canvas":[64,64],
        "source_physical_pixel_aspect":"7:6",
        "first_frame":1205,"last_frame":1220,
        "source_frame_observations":32,
        "temporal_transition_observations":30,
        "source_binary_mask_changed_transition_count":sum(
            results[p]["changed_binary_transitions"] for p in ("p1","p2")),
        "source_binary_mask_held_transition_count":sum(
            results[p]["unchanged_binary_transitions"] for p in ("p1","p2")),
        "unique_original_binary_silhouettes":corpus["distinct_binary_silhouette_groups"],
        "pixel_data_included":False,
        "original_1994_3d_pose_mapping_recovered":False,
        "true_physical_wheel_ground_contact_verified":False,
        "independent_original_camera_verified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
        "players":results,
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,help="new no-overwrite JSON receipt; otherwise stdout")
    args=ap.parse_args()
    report=build_witness()
    result=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.out:
        publish_text_once(args.out,result)
    else:
        print(result,end="")


if __name__=="__main__":
    main()
