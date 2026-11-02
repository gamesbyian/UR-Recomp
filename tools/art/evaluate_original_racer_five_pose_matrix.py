#!/usr/bin/env python3
"""Real five-pose GLB silhouettes scored against 35 authenticated ROM masks.

Reuses current original-source validators, existing viewer artifact and exact
4x source-anchor projection; does not infer any 1994 sprite's 3D pose identity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import inspect_viewer, POSES
    from tools.art.compare_original_chroma_axes_to_glb_poses import CAMERA_SHA, POSE_GLB_SHA
    from tools.art.evaluate_original_racer_wheel_holdout import (
        originals_from_corpus, translated_4x_source_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus, CANONICAL_ROM_SHA
    from tools.art.render_racer_glb_projection import camera_config, model_mesh, render_mask
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import inspect_viewer, POSES
    from compare_original_chroma_axes_to_glb_poses import CAMERA_SHA, POSE_GLB_SHA
    from evaluate_original_racer_wheel_holdout import originals_from_corpus, translated_4x_source_mask
    from freeze_racer_source_family_splits import validate_corpus, CANONICAL_ROM_SHA
    from render_racer_glb_projection import camera_config, model_mesh, render_mask
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ACTUAL-USA-ROM-FIVE-GLB-POSE-MATRIX/1"


def validate_matrix_rows(rows, originals, poses=POSES):
    """Pure negative-control audit, one vote per actual original binary mask."""
    if (not isinstance(rows, list) or len(rows) != len(originals)
            or len({r.get("source_binary_mask_sha256") for r in rows}) != len(rows)
            or {r.get("source_binary_mask_sha256") for r in rows} != set(originals)):
        raise ValueError("original 35-mask census or uniqueness altered")
    for row in rows:
        scores = row.get("unpaired_pose_scores")
        if not isinstance(scores, dict) or set(scores) != set(poses):
            raise ValueError("incomplete actual five-pose score row")
        for pose in poses:
            result = scores[pose]
            if (not isinstance(result, dict)
                    or type(result.get("mask_iou")) not in (float, int)
                    or not 0 <= result["mask_iou"] <= 1):
                raise ValueError("invalid real-source IoU")
        if row.get("unpaired_best_fit_pose") not in poses:
            raise ValueError("missing original-source best-pose diagnostic")
    return True


def evaluate(corpus_path: Path, site: Path, camera_path: Path):
    original, verified = validate_corpus(corpus_path)
    if (original["source_rom_sha256"] != CANONICAL_ROM_SHA
            or len(verified["all_masks"]) != 35):
        raise ValueError("expected exact authentic 35-mask USA-ROM corpus")
    masks = originals_from_corpus(corpus_path, original)
    if set(masks) != verified["all_masks"]:
        raise ValueError("source original pixels disagree with verified corpus")
    model, _, paths = inspect_viewer(site)
    camera_raw = camera_path.read_bytes()
    if hashlib.sha256(camera_raw).hexdigest() != CAMERA_SHA:
        raise ValueError("provisional first-family camera SHA changed")
    camera = json.loads(camera_raw)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional"
            or camera.get("source_witness", {}).get("player") != "p1"
            or camera.get("source_witness", {}).get("guest_frame") != 1205):
        raise ValueError("source witness or camera changed")
    projected = {}
    model_hashes = {}
    for pose in POSES:
        expected = model["poses"][pose]["sha256"]
        if expected != POSE_GLB_SHA[pose]:
            raise ValueError("not the five source-authored original experimental GLBs")
        vertices, faces, sha, _ = model_mesh(paths[pose], expected)
        if sha != expected or not len(faces):
            raise ValueError("empty or substituted real GLB")
        projected[pose] = render_mask(vertices, faces, camera)
        model_hashes[pose] = sha
    observations = {}
    for frame in original["source_temporal_frame_observations"]:
        for player, rid in frame["representations"].items():
            info = original["source_representations"][rid]
            if info["player"] != player:
                raise ValueError("original registered player identity changed")
            mask = info["source_binary_mask_sha256"]
            observations.setdefault(mask, []).append({
                "window": frame["window"], "player": player,
                "guest_frame": frame["guest_frame"],
            })
    if set(observations) != set(masks):
        raise ValueError("original temporal shape representation changed")
    rows = []
    for mask_sha, group in sorted(masks.items()):
        measured = {}
        for pose in POSES:
            projected_source = translated_4x_source_mask(
                projected[pose], group["source_alpha_anchor_x2_y2"])
            metrics = score(group["mask"], projected_source)
            measured[pose] = {
                key: metrics[key] for key in (
                    "mask_iou", "mask_xor_pixels",
                    "boundary_chamfer_mean_physical_px",
                )
            }
        ordered = sorted(POSES, key=lambda p: (
            -measured[p]["mask_iou"],
            measured[p]["boundary_chamfer_mean_physical_px"], p))
        rows.append({
            "source_binary_mask_sha256": mask_sha,
            "original_source_observations": sorted(
                observations[mask_sha], key=lambda f: (
                    f["window"], f["player"], f["guest_frame"])),
            "source_observation_count": len(observations[mask_sha]),
            "unpaired_pose_scores": measured,
            "unpaired_best_fit_pose": ordered[0],
        })
    validate_matrix_rows(rows, masks)
    if len(rows) != 35 or len(original["source_temporal_frame_observations"]) != 91:
        raise ValueError("authentic original temporal or silhouette census changed")
    # This authentic first-family source mask was independently scored
    # before this study, so it is a positive source/rendering control.
    first = next(x for x in rows if {"window": "first-1205-1220",
                 "player": "p1", "guest_frame": 1205}
                 in x["original_source_observations"])
    if abs(first["unpaired_pose_scores"]["upright"]["mask_iou"] - 0.5828877) > 1e-7:
        raise ValueError("historic real-GLB P1:1205 reference no longer reproduces")
    return {
        "schema": SCHEMA,
        "source_original_rom_sha256": CANONICAL_ROM_SHA,
        "source_original_corpus_sha256": verified["corpus_sha256"],
        "source_original_frame_observations": len(original["source_temporal_frame_observations"]),
        "unique_original_binary_silhouettes": len(rows),
        "viewer_five_pose_glb_sha256": model_hashes,
        "viewer_original_source_model_sha256": model["source_model_sha256"],
        "camera_manifest_sha256": CAMERA_SHA,
        "camera_status": "provisional",
        "camera_shared_across_all_comparisons": True,
        "registration_mode": "source-registered",
        "per_pair_auto_alignment": False,
        "similarities_are_unpaired_hypotheses_not_source_pose_mapping": True,
        "original_1994_3d_camera_recovered": False,
        "original_1994_pose_labels_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--model-review-dir", type=Path, required=True)
    ap.add_argument("--camera", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = json.dumps(evaluate(args.corpus, args.model_review_dir, args.camera),
                        indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
