#!/usr/bin/env python3
"""Audit actual ROM raster motion versus frozen experimental 2026 GLB poses.

Source ROM pixels, real GLBs, pose labels and camera must be independently
SHA-bound. Distinguishes per-source *placement* from model *articulation*.
This is a negative-control study, not 1994 skeletal animation recovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import inspect_viewer, POSES
    from tools.art.compare_original_chroma_axes_to_glb_poses import (
        CAMERA_SHA, POSE_GLB_SHA,
    )
    from tools.art.evaluate_original_racer_wheel_holdout import (
        originals_from_corpus, translated_4x_source_mask,
    )
    from tools.art.fit_original_racer_pose_sequence import fit
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.prepare_original_racer_pose_sequence import build_input
    from tools.art.render_racer_glb_projection import (
        camera_config, model_mesh, render_mask,
    )
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import inspect_viewer, POSES
    from compare_original_chroma_axes_to_glb_poses import CAMERA_SHA, POSE_GLB_SHA
    from evaluate_original_racer_wheel_holdout import (
        originals_from_corpus, translated_4x_source_mask,
    )
    from fit_original_racer_pose_sequence import fit
    from freeze_racer_source_family_splits import validate_corpus
    from prepare_original_racer_pose_sequence import build_input
    from render_racer_glb_projection import camera_config, model_mesh, render_mask
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-AUTHENTIC-ROM-EXPERIMENTAL-GLB-PIXEL-MOTION/1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pixel_change(before, after, predicted_before, predicted_after,
                 predicted_pose_only_after) -> dict:
    """Separate authentic raster changes, placed-model changes and pose alone.

    A model whose pose does not change can still have different pixels when
    translated to the *source's* changing bottommost alpha anchor. Compare the
    next pose again at the PREVIOUS source anchor for the pose-only control.
    """
    items = (before, after, predicted_before, predicted_after,
             predicted_pose_only_after)
    if (any(not isinstance(item, (bytes, bytearray)) or len(item) != 4096
            or not any(item) or any(x not in (0, 1) for x in item)
            for item in items)):
        raise ValueError("motion edges require five nonempty 64x64 binary masks")
    reference = {i for i in range(4096) if before[i] != after[i]}
    predicted = {i for i in range(4096)
                 if predicted_before[i] != predicted_after[i]}
    pose_only = {i for i in range(4096)
                 if predicted_before[i] != predicted_pose_only_after[i]}
    overlap = len(reference & predicted)
    pose_overlap = len(reference & pose_only)
    return {
        "source_changed_pixel_count": len(reference),
        "model_placed_changed_pixel_count": len(predicted),
        "model_pose_only_changed_pixel_count": len(pose_only),
        "source_changed_pixels_explained_by_placed_model": overlap,
        "source_changed_pixels_overlapping_pose_only_model_change": pose_overlap,
        "source_changed_pixels_not_overlapping_pose_only_model_change":
            len(reference) - pose_overlap,
        "pose_only_model_source_change_recall":
            round(pose_overlap / len(reference), 8) if reference else None,
        "pose_only_model_source_change_precision":
            round(pose_overlap / len(pose_only), 8) if pose_only else None,
        "source_changed_pixels_not_explained_by_placed_model":
            len(reference) - overlap,
        "model_placed_changed_pixels_not_in_source": len(predicted) - overlap,
        "placed_model_change_iou": (round(overlap / len(reference | predicted), 8)
                                    if reference or predicted else 1.0),
        "placed_model_source_change_recall": (round(overlap / len(reference), 8)
                                              if reference else None),
        "placed_model_source_change_precision": (round(overlap / len(predicted), 8)
                                                 if predicted else None),
        "original_source_binary_silhouette_changed": bool(reference),
        "model_pose_only_raster_changed": bool(pose_only),
        "model_placed_raster_changed": bool(predicted),
        "both_source_and_model_stationary": not reference and not predicted,
    }


def summarize(edges: list[dict]) -> dict:
    if not edges:
        raise ValueError("no original observed consecutive source edges")
    counts = [row["motion"] for row in edges]
    source_events = sum(x["original_source_binary_silhouette_changed"] for x in counts)
    source_pixels = sum(x["source_changed_pixel_count"] for x in counts)
    explained = sum(x["source_changed_pixels_explained_by_placed_model"] for x in counts)
    model_pixels = sum(x["model_placed_changed_pixel_count"] for x in counts)
    pose_pixels = sum(x["model_pose_only_changed_pixel_count"] for x in counts)
    pose_overlap = sum(x["source_changed_pixels_overlapping_pose_only_model_change"]
                       for x in counts)
    return {
        "actually_consecutive_original_guest_frame_edges": len(edges),
        "original_binary_silhouette_changed_edges": source_events,
        "original_binary_silhouette_held_edges": len(edges) - source_events,
        "source_binary_changed_pixels_total": source_pixels,
        "placed_model_changed_pixels_total": model_pixels,
        "placed_model_overlapping_source_change_pixels": explained,
        "pose_only_model_changed_pixel_count": pose_pixels,
        "pose_only_model_overlapping_source_changed_pixels": pose_overlap,
        "pose_only_model_changed_pixel_recall":
            round(pose_overlap / source_pixels, 8) if source_pixels else None,
        "pose_only_model_changed_pixel_precision":
            round(pose_overlap / pose_pixels, 8) if pose_pixels else None,
        "placed_model_pixel_recall_across_source_changes":
            round(explained / source_pixels, 8) if source_pixels else None,
        "placed_model_pixel_precision_across_predicted_changes":
            round(explained / model_pixels, 8) if model_pixels else None,
        "model_pose_label_transition_edges":
            sum(row["model_pose_label_changed"] for row in edges),
        "source_placement_anchor_changed_edges":
            sum(row["source_visible_alpha_anchor_changed"] for row in edges),
        "source_moving_edges_with_no_model_pose_change":
            sum(x["original_source_binary_silhouette_changed"]
                and not row["model_pose_label_changed"]
                for row, x in zip(edges, counts)),
        "source_moving_edges_with_no_placed_model_pixel_change":
            sum(x["original_source_binary_silhouette_changed"]
                and not x["model_placed_raster_changed"] for x in counts),
        "source_moving_edges_with_no_pose_only_pixel_change":
            sum(x["original_source_binary_silhouette_changed"]
                and not x["model_pose_only_raster_changed"] for x in counts),
        "source_stationary_edges_with_spurious_model_pixel_change":
            sum(not x["original_source_binary_silhouette_changed"]
                and x["model_placed_raster_changed"] for x in counts),
    }


def compute(corpus_path: Path, matrix_path: Path, sequence_path: Path,
            site: Path, camera_path: Path) -> dict:
    corpus, verified = validate_corpus(corpus_path)
    originals = originals_from_corpus(corpus_path, corpus)
    if set(originals) != verified["all_masks"] or len(originals) != 35:
        raise ValueError("authentic original source mask census changed")
    raw_matrix, raw_sequence = matrix_path.read_bytes(), sequence_path.read_bytes()
    matrix, sequence = json.loads(raw_matrix), json.loads(raw_sequence)
    inputs = build_input(
        corpus, matrix, corpus["registered_source_windows"],
        corpus_sha=verified["corpus_sha256"],
    )
    if (sequence.get("schema") != "UR-ART4K-SOURCE-BOUND-POSE-LABEL-EXPERIMENT/1"
            or sequence.get("actual_original_source_pngs_revalidated") is not True
            or sequence.get("pose_matrix_report_sha256") != digest(raw_matrix)
            or sequence.get("provenance") != inputs["provenance"]
            or sequence.get("frame_count") != len(inputs["frames"])
            or type(sequence.get("change_penalty")) not in (int, float)
            or not math.isfinite(sequence["change_penalty"])
            or sequence["change_penalty"] < 0
            or sequence.get("authentic_original_3d_pose_registration") is not False):
        raise ValueError("incomplete or mismatched actual-ROM temporal label evidence")
    inputs["change_penalty"] = sequence["change_penalty"]
    if sequence.get("temporal_experiment") != fit(inputs):
        raise ValueError("original source path labels differ from reproducible fit")
    if len(inputs["frames"]) != 144 or len(sequence["temporal_experiment"]["sequences"]) != 35:
        raise ValueError("original source P1/P2 chronology census changed")
    raw_camera = camera_path.read_bytes()
    if (digest(raw_camera) != CAMERA_SHA
            or matrix["camera_manifest_sha256"] != CAMERA_SHA
            or matrix["registration_mode"] != "source-registered"):
        raise ValueError("not the fixed original source-registered camera")
    camera = json.loads(raw_camera)
    camera_config(camera)
    model, _, pose_paths = inspect_viewer(site)
    if set(matrix["viewer_five_pose_glb_sha256"]) != set(POSES):
        raise ValueError("expected the same five real GLB identities")
    projections = {}
    for pose in POSES:
        if (matrix["viewer_five_pose_glb_sha256"][pose] != POSE_GLB_SHA[pose]
                or model["poses"][pose]["sha256"] != POSE_GLB_SHA[pose]):
            raise ValueError("original source-authored 2026 GLB mismatch")
        vertices, faces, actual_sha, _ = model_mesh(pose_paths[pose], POSE_GLB_SHA[pose])
        if actual_sha != POSE_GLB_SHA[pose] or len(faces) == 0:
            raise ValueError("missing real projected source rig")
        projections[pose] = render_mask(vertices, faces, camera)
    source_by_frame = {}
    for frame in inputs["frames"]:
        key = (frame["window"], frame["player"], frame["guest_frame"])
        sha = frame["source_binary_mask_sha256"]
        source_by_frame[key] = originals[sha]
    registered_projection = {}
    for mask_sha, group in sorted(originals.items()):
        anchor = group["source_alpha_anchor_x2_y2"]
        registered_projection[mask_sha] = {
            pose: translated_4x_source_mask(projections[pose], anchor)
            for pose in POSES
        }
    # Independently reproduce every 35×5 matrix IoU using actual projected
    # GLB pixels rather than trusting the matrix's scoring assertions.
    if len(matrix["rows"]) != 35:
        raise ValueError("wrong original 35×5 pixel matrix")
    for row in matrix["rows"]:
        sha = row["source_binary_mask_sha256"]
        if sha not in originals:
            raise ValueError("unrecognized source binary mask in matrix")
        original = originals[sha]["mask"]
        for pose in POSES:
            candidate = registered_projection[sha][pose]
            intersection = sum(a and b for a, b in zip(original, candidate))
            union = sum(a or b for a, b in zip(original, candidate))
            actual_iou = round(intersection / union, 8)
            if actual_iou != row["unpaired_pose_scores"][pose]["mask_iou"]:
                raise ValueError("real GLB render does not reproduce source-pose score")
    edges = []
    for segment in sequence["temporal_experiment"]["sequences"]:
        player, window = segment["player"], segment["window"]
        frames, labels = segment["guest_frames"], segment["sequence_poses"]
        for index in range(1, len(frames)):
            prev, curr = frames[index - 1], frames[index]
            if curr != prev + 1:
                raise ValueError("original source segmentation bridges guest-frame gap")
            prior_sha = next(f["source_binary_mask_sha256"] for f in inputs["frames"]
                             if (f["window"], f["player"], f["guest_frame"]) ==
                                (window, player, prev))
            current_sha = next(f["source_binary_mask_sha256"] for f in inputs["frames"]
                               if (f["window"], f["player"], f["guest_frame"]) ==
                                  (window, player, curr))
            a, b = source_by_frame[window, player, prev], source_by_frame[window, player, curr]
            prior_pose, next_pose = labels[index - 1], labels[index]
            left = registered_projection[prior_sha][prior_pose]
            right = registered_projection[current_sha][next_pose]
            next_at_previous_anchor = registered_projection[prior_sha][next_pose]
            edges.append({
                "window": window, "player": player,
                "from_guest_frame": prev, "to_guest_frame": curr,
                "from_original_binary_sha256": prior_sha,
                "to_original_binary_sha256": current_sha,
                "from_experimental_GLb_pose": prior_pose,
                "to_experimental_GLb_pose": next_pose,
                "model_pose_label_changed": prior_pose != next_pose,
                "source_visible_alpha_anchor_changed":
                    a["source_alpha_anchor_x2_y2"] != b["source_alpha_anchor_x2_y2"],
                "motion": pixel_change(
                    a["mask"], b["mask"], left, right,
                    next_at_previous_anchor,
                ),
            })
    result = summarize(edges)
    if (result["actually_consecutive_original_guest_frame_edges"] != 109
            or result["original_binary_silhouette_changed_edges"] != 19
            or result["original_binary_silhouette_held_edges"] != 90):
        raise ValueError("authentic source raster transition ledger disagrees")
    return {
        "schema": SCHEMA,
        "source_rom_sha256": corpus["source_rom_sha256"],
        "source_corpus_sha256": verified["corpus_sha256"],
        "actual_original_source_pngs_revalidated": True,
        "source_original_pose_matrix_sha256": digest(raw_matrix),
        "source_original_sequence_sha256": digest(raw_sequence),
        "provisional_camera_sha256": CAMERA_SHA,
        "five_actual_2026_glb_sha256_by_pose": dict(POSE_GLB_SHA),
        "exact_35_by_5_source_iou_independently_reproduced": True,
        "model_pose_2026_discrete_diagnostic_only": True,
        "source_1994_camera_or_3d_joint_pose_recovered": False,
        "source_visible_bottom_anchor_is_physical_contact": False,
        "original_1994_art_likeness_approved": False,
        "shipping_art_approved": False,
        "summary": result,
        "edges": edges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--pose-matrix", type=Path, required=True)
    parser.add_argument("--pose-sequence", type=Path, required=True)
    parser.add_argument("--model-review-dir", type=Path, required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = json.dumps(compute(args.corpus, args.pose_matrix, args.pose_sequence,
                                args.model_review_dir, args.camera),
                        sort_keys=True, indent=2) + "\n"
    if args.out:
        publish_text_once(args.out, report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
