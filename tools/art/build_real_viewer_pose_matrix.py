#!/usr/bin/env python3
"""Score all authentic first-family silhouettes against five existing viewer GLBs.

Rankings are deliberately UNPAIRED image-projection similarities. They do not
infer a real 1994 source sprite -> 2026 procedural rig pose mapping, provide
an independent camera holdout, or approve likeness. No image bytes are emitted.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import (
        CAMERA, POSES, inspect_viewer, safe_existing_path,
    )
    from tools.art.build_racer_source_pixel_corpus import build as source_corpus
    from tools.art.racer_source_pixels import alpha_metrics, decode_rgba_png
    from tools.art.render_racer_glb_projection import camera_config, model_mesh, render_mask
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import CAMERA, POSES, inspect_viewer, safe_existing_path
    from build_racer_source_pixel_corpus import build as source_corpus
    from racer_source_pixels import alpha_metrics, decode_rgba_png
    from render_racer_glb_projection import camera_config, model_mesh, render_mask
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-UNPAIRED-POSE-SIMILARITY-MATRIX/1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rank_unpaired(rows: list[dict], pose_names=POSES) -> dict:
    """Pure deterministic reducer: one vote per distinct original 64px mask."""
    if not rows or set(pose_names) != set(POSES):
        raise ValueError("expected all five pose candidates and at least one source shape")
    if len({row["source_binary_mask_sha256"] for row in rows}) != len(rows):
        raise ValueError("duplicate source binary silhouette may not get another vote")
    totals = {name: [] for name in pose_names}
    winners = {name: 0 for name in pose_names}
    for row in rows:
        results = row.get("unpaired_pose_scores")
        if not isinstance(results, dict) or set(results) != set(pose_names):
            raise ValueError("incomplete pose matrix")
        ordered = sorted(pose_names, key=lambda pose: (
            -results[pose]["mask_iou"],
            results[pose]["boundary_chamfer_mean_physical_px"], pose))
        if row.get("unpaired_best_fit_pose") != ordered[0]:
            raise ValueError("claimed best pose disagrees with scored silhouettes")
        winners[ordered[0]] += 1
        for pose in pose_names:
            number = results[pose]["mask_iou"]
            if type(number) not in (int, float) or not 0 <= number <= 1:
                raise ValueError("invalid silhouette IoU")
            totals[pose].append(number)
    return {
        "equal_source_mask_weighted_mean_iou_by_experimental_pose": {
            name: round(sum(totals[name]) / len(totals[name]), 8)
            for name in pose_names
        },
        "unpaired_highest_iou_source_mask_count_by_experimental_pose": winners,
        "winner_is_authentic_original_pose_mapping": False,
        "not_a_heldout_measurement": True,
    }


def compute(site: Path, camera_path: Path = CAMERA) -> dict:
    model, _, pose_files = inspect_viewer(site)
    camera_raw = camera_path.read_bytes()
    camera = json.loads(camera_raw)
    camera_config(camera)
    witness = camera.get("source_witness")
    if (camera.get("camera_calibration_status") != "provisional" or
            not isinstance(witness, dict) or
            (witness.get("player"), witness.get("guest_frame")) != ("p1", 1205)):
        raise ValueError("only the explicit original P1:1205 provisional camera is supported")
    original = source_corpus()
    expected = {(obs["player"], obs["guest_frame"]): obs
                for obs in original["observations"]}
    refs = json.loads((site / "sprites.json").read_text(encoding="utf-8"))["frames"]
    if len(refs) != len(expected):
        raise ValueError("viewer must contain every original source reference")
    source_groups = {}
    for ref in refs:
        key = (ref["player"], ref["guest_frame"])
        if key not in expected:
            raise ValueError("unregistered original frame")
        expected_row = expected[key]
        path = safe_existing_path(site, ref["image"], ".png")
        w, h, rgba, file_sha = decode_rgba_png(path)
        metrics = alpha_metrics(rgba, w, h)
        if (file_sha != expected_row["png_file_sha256"] or
                metrics["source_rgba_sha256"] != expected_row["source_rgba_sha256"] or
                metrics["binary_mask_sha256"] != expected_row["binary_mask_sha256"]):
            raise ValueError("original frame fails independent source-pixel identity")
        mask = bytes(1 if x else 0 for x in rgba[3::4])
        binary_sha = digest(mask)
        if binary_sha != metrics["binary_mask_sha256"]:
            raise ValueError("corrupted original binary mask")
        group = source_groups.setdefault(binary_sha, {
            "mask": mask,
            "source_binary_mask_sha256": binary_sha,
            "source_opaque_pixels": metrics["nonzero_alpha_pixels"],
            "original_source_observations": [],
        })
        if group["mask"] != mask:
            raise ValueError("original binary group hash collision")
        group["original_source_observations"].append({
            "player": ref["player"],
            "guest_frame": ref["guest_frame"],
            "representation_id": ref["representation_id"],
            "original_png_sha256": file_sha,
        })
    if (len(source_groups) != original["distinct_binary_silhouette_groups"] or
            sum(len(g["original_source_observations"]) for g in source_groups.values()) != 32):
        raise ValueError("unexpected authentic original source grouping")
    candidates = {}
    for pose in POSES:
        vertices, faces, actual_sha, nodes = model_mesh(
            pose_files[pose], model["poses"][pose]["sha256"])
        render = render_mask(vertices, faces, camera)
        # Match the existing scorer's 4x source pixel centre exactly.
        mask = bytes(int(x) for x in render[2::4, 2::4].reshape(-1))
        if len(mask) != 64 * 64 or not any(mask):
            raise ValueError("invalid projected GLB silhouette")
        candidates[pose] = {
            "binary_mask": mask, "binary_mask_sha256": digest(mask),
            "glb_sha256": actual_sha, "triangle_count": len(faces),
            "glb_scene_graph_node_count": nodes,
        }
    rows = []
    for key, group in sorted(source_groups.items(),
                             key=lambda kv: min(
                                (x["player"], x["guest_frame"])
                                for x in kv[1]["original_source_observations"])):
        results = {}
        for pose, item in candidates.items():
            measured = score(group["mask"], item["binary_mask"])
            results[pose] = {
                k: measured[k] for k in (
                    "mask_iou", "mask_intersection", "mask_union",
                    "mask_xor_pixels", "boundary_chamfer_mean_physical_px",
                    "lowest_alpha_delta_x2_y2",
                )
            }
        order = sorted(POSES, key=lambda pose: (
            -results[pose]["mask_iou"],
            results[pose]["boundary_chamfer_mean_physical_px"], pose))
        rows.append({
            "source_binary_mask_sha256": key,
            "source_opaque_pixels": group["source_opaque_pixels"],
            "source_observation_count": len(group["original_source_observations"]),
            "original_source_observations": sorted(
                group["original_source_observations"],
                key=lambda item: (item["player"], item["guest_frame"])),
            "unpaired_pose_scores": results,
            "unpaired_best_fit_pose": order[0],
            "unpaired_pose_iou_order": order,
        })
    return {
        "schema": SCHEMA,
        "viewer_model_source_commit": model["source_commit"],
        "viewer_model_source_scad_sha256": model["source_model_sha256"],
        "viewer_five_pose_glb_sha256": {
            pose: candidates[pose]["glb_sha256"] for pose in POSES
        },
        "projected_source_binary_mask_sha256_by_pose": {
            pose: candidates[pose]["binary_mask_sha256"] for pose in POSES
        },
        "camera_manifest_sha256": digest(camera_raw),
        "camera_status": "provisional",
        "camera_shared_across_all_comparisons": True,
        "camera_witness_is_only_source_p1_frame1205": True,
        "per_pair_auto_alignment": False,
        "source_original_rom_sha256": original["historical_manifest_declared_rom_sha256"],
        "original_source_registry_sha256": original["source_registry_current_sha256"],
        "original_frame_observations": len(refs),
        "unique_original_binary_silhouettes": len(rows),
        "comparison_count": len(rows) * len(POSES),
        "similarities_are_unpaired_hypotheses_not_source_pose_mapping": True,
        "original_1994_3d_camera_recovered": False,
        "independent_pose_family_holdout_tested": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "rows": rows,
        "summary": rank_unpaired(rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir", type=Path, required=True)
    ap.add_argument("--camera", type=Path, default=CAMERA)
    ap.add_argument("--out", type=Path,
                    help="optional one-time JSON receipt, never replace existing")
    args = ap.parse_args()
    report = compute(args.model_review_dir, args.camera)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
