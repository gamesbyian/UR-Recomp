#!/usr/bin/env python3
"""Generate a read-only, source-verified measurement sidecar for the ONE Pages viewer.

This is an OFFLINE producer, not a second website or public publisher. The
five real GLBs and every original sprite are validated and freshly measured
by build_real_viewer_pose_matrix.compute, not trusted from a supplied JSON.
The data do not authenticate a 1994 sprite-to-2026 blockout pose mapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "UR-RACER-MODEL-REVIEW-MEASUREMENT-SIDECAR/1"
MATRIX_SCHEMA = "UR-RACER-UNPAIRED-POSE-SIMILARITY-MATRIX/1"
POSES = ("upright", "pedal", "wheelie", "stunt", "bank")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_sha256(value) -> bool:
    return (isinstance(value, str) and len(value) == 64 and
            all(c in "0123456789abcdef" for c in value))


def sanitized_sidecar(matrix: dict, site_manifest_sha: str,
                      sprite_rail_sha: str) -> dict:
    """Build a small self-contained UI handoff from a *freshly computed* matrix.

    All client-visible model/source claims are strictly limited to research
    facts. A caller cannot override the false approval/camera/pose-map flags.
    """
    if (matrix.get("schema") != MATRIX_SCHEMA or
            matrix.get("registration_mode") != "source-registered" or
            matrix.get("camera_status") != "provisional" or
            matrix.get("registered_original_contact_used_without_optimization") is not True or
            matrix.get("similarities_are_unpaired_hypotheses_not_source_pose_mapping") is not True or
            matrix.get("camera_shared_across_all_comparisons") is not True or
            matrix.get("original_1994_3d_camera_recovered") is not False or
            matrix.get("independent_pose_family_holdout_tested") is not False or
            matrix.get("shipping_art_approved") is not False or
            matrix.get("owner_likeness_approved") is not False):
        raise ValueError("sidecar requires genuine provisional, unpaired source-registered research")
    for sha in (site_manifest_sha, sprite_rail_sha,
                matrix.get("viewer_model_source_scad_sha256"),
                matrix.get("camera_manifest_sha256"),
                matrix.get("original_source_registry_sha256"),
                matrix.get("source_original_rom_sha256")):
        if not is_sha256(sha):
            raise ValueError("missing or malformed viewer/camera/original source SHA256")
    commit = matrix.get("viewer_model_source_commit")
    if (not isinstance(commit, str) or len(commit) != 40 or
            any(c not in "0123456789abcdef" for c in commit)):
        raise ValueError("model source commit must be a full lowercase Git commit")
    poses = matrix.get("viewer_five_pose_glb_sha256")
    if not isinstance(poses, dict) or set(poses) != set(POSES) or not all(is_sha256(x) for x in poses.values()):
        raise ValueError("all five actual GLB sha256 values are mandatory")
    rows = matrix.get("rows")
    if (not isinstance(rows, list) or len(rows) != 10 or
            matrix.get("unique_original_binary_silhouettes") != 10 or
            matrix.get("original_frame_observations") != 32 or
            matrix.get("comparison_count") != 50):
        raise ValueError("expected exact 32-frame / 10-distinct-source / five-GLB corpus")
    encountered_masks = set()
    encountered_frames = set()
    normalized_rows = []
    totals = {pose: [] for pose in POSES}
    leaders = {pose: 0 for pose in POSES}
    for row in rows:
        mask_sha = row.get("source_binary_mask_sha256")
        if not is_sha256(mask_sha) or mask_sha in encountered_masks:
            raise ValueError("source silhouette hash missing or duplicated")
        encountered_masks.add(mask_sha)
        source = row.get("original_source_observations")
        if (not isinstance(source, list) or not source or
                row.get("source_observation_count") != len(source)):
            raise ValueError("source mask lacks registered original frame provenance")
        unique_frames = []
        for frame in source:
            key = (frame.get("player"), frame.get("guest_frame"))
            if (key[0] not in ("p1", "p2") or
                    type(key[1]) is not int or not 1205 <= key[1] <= 1220 or
                    key in encountered_frames or
                    not isinstance(frame.get("representation_id"), str) or
                    not is_sha256(frame.get("original_png_sha256"))):
                raise ValueError("source frame reference is forged or duplicated")
            encountered_frames.add(key)
            unique_frames.append({
                "player": key[0], "guest_frame": key[1],
                "representation_id": frame["representation_id"],
                "original_png_sha256": frame["original_png_sha256"],
            })
        anchor = row.get("registered_original_contact_x2_y2")
        shift = row.get("source_registered_logical_xy_translation")
        if (not isinstance(anchor, list) or len(anchor) != 2 or
                not all(type(x) is int for x in anchor) or
                not isinstance(shift, list) or len(shift) != 2 or
                not all(type(x) is int for x in shift) or
                [anchor[0]-67, anchor[1]-76] != [shift[0]*2, shift[1]*2]):
            raise ValueError("registered source anchor must use the original P1 witness origin")
        scores = row.get("unpaired_pose_scores")
        if not isinstance(scores, dict) or set(scores) != set(POSES):
            raise ValueError("all five experimental pose scores are required")
        compact = {}
        for pose in POSES:
            entry = scores[pose]
            iou, chamfer = entry.get("mask_iou"), entry.get("boundary_chamfer_mean_physical_px")
            if (type(iou) not in (int, float) or not math.isfinite(iou) or not 0 <= iou <= 1 or
                    type(chamfer) not in (int, float) or not math.isfinite(chamfer) or not 0 <= chamfer <= 100):
                raise ValueError("invalid measured IoU or physical contour distance")
            compact[pose] = {"silhouette_iou": iou,
                             "boundary_chamfer_physical_px": chamfer}
            totals[pose].append(iou)
        best = sorted(POSES, key=lambda pose: (
            -compact[pose]["silhouette_iou"],
            compact[pose]["boundary_chamfer_physical_px"], pose))[0]
        if row.get("unpaired_best_fit_pose") != best:
            raise ValueError("source pose winner label inconsistent with metrics")
        leaders[best] += 1
        normalized_rows.append({
            "original_binary_mask_sha256": mask_sha,
            "registered_original_contact_x2_y2": anchor,
            "source_logical_translation_from_witness_xy": shift,
            "source_frames": unique_frames,
            "unpaired_scores": compact,
            "highest_iou_experimental_pose": best,
            "highest_iou_pose_is_an_authenticated_original_pose": False,
        })
    if len(encountered_frames) != 32:
        raise ValueError("not all 32 original player/frame observations are represented")
    means = {pose: round(sum(totals[pose]) / len(totals[pose]), 8) for pose in POSES}
    summary = matrix.get("summary", {})
    given_means = summary.get("equal_source_mask_weighted_mean_iou_by_experimental_pose", {})
    given_winners = summary.get("unpaired_highest_iou_source_mask_count_by_experimental_pose", {})
    if (given_means != means or given_winners != leaders):
        raise ValueError("source-shape-weighted research summary does not match original rows")
    return {
        "schema": SCHEMA,
        "purpose": "read-only verified research overlay for existing model-review viewer",
        "viewer_manifest_sha256": site_manifest_sha,
        "viewer_sprite_rail_sha256": sprite_rail_sha,
        "source_model_commit": commit,
        "source_model_scad_sha256": matrix["viewer_model_source_scad_sha256"],
        "source_pose_glb_sha256": {pose: poses[pose] for pose in POSES},
        "source_rom_sha256": matrix["source_original_rom_sha256"],
        "source_registry_sha256": matrix["original_source_registry_sha256"],
        "camera_manifest_sha256": matrix["camera_manifest_sha256"],
        "camera_status": "provisional",
        "source_registration_mode": "original-pixel-verified-contact-anchor",
        "source_anchor_is_physical_ground_contact": False,
        "distinct_original_source_binary_silhouette_count": 10,
        "experimental_glb_pose_count": 5,
        "original_frame_observations": 32,
        "equal_original_mask_weighted_mean_silhouette_iou": means,
        "experimental_pose_highest_iou_counts": leaders,
        "source_shape_measurements": normalized_rows,
        "source_to_experimental_model_pose_mapping_verified": False,
        "fresh_source_registered_matrix_sha256": digest(
            (json.dumps(matrix, indent=2, sort_keys=True) + "\n").encode("utf-8")),
        "recovered_1994_3d_camera_verified": False,
        "independent_heldout_family_tested": False,
        "owner_character_likeness_approved": False,
        "shipping_art_approved": False,
        "viewer_files_modified": False,
        "public_website_deployment_claimed": False,
        "ui_warning": (
            "Experimental five-pose model. Source-registered 2D silhouette "
            "similarities only; winning GLB labels are NOT authentic original "
            "sprite pose assignments. Camera is provisional; likeness unapproved."
        ),
    }


def create_sidecar(site: Path, camera: Path) -> dict:
    # Import lazily so cheap contract tests are ROM/GLB/optional-dependency free.
    # Call the independent input and GLB verification runner on the actual
    # staged site; never allow passing an untrusted self-reported score JSON.
    try:
        from tools.art.build_real_viewer_pose_matrix import compute
    except ModuleNotFoundError:
        from build_real_viewer_pose_matrix import compute
    site = site.resolve()
    if not site.is_dir() or site.is_symlink():
        raise ValueError("an existing real model-review site directory is required")
    matrix = compute(site, camera, "source-registered")
    manifest_raw = (site / "manifest.json").read_bytes()
    sprites_raw = (site / "sprites.json").read_bytes()
    return sanitized_sidecar(matrix, digest(manifest_raw), digest(sprites_raw))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir", type=Path, required=True)
    ap.add_argument("--camera", type=Path, required=True,
                    help="exact source-registration provisional camera manifest")
    ap.add_argument("--out", type=Path, required=True,
                    help="new JSON destination outside the site; no overwrite")
    args = ap.parse_args()
    site = args.model_review_dir.resolve()
    if args.out.resolve().is_relative_to(site):
        ap.error("sidecar must be staged separately; the viewer owner controls site publication")
    sidecar = create_sidecar(site, args.camera)
    raw = json.dumps(sidecar, indent=2, sort_keys=True) + "\n"
    try:
        from tools.art.no_replace_report import publish_text_once
    except ModuleNotFoundError:
        from no_replace_report import publish_text_once
    publish_text_once(args.out, raw)
    print(json.dumps({
        "sidecar_schema": sidecar["schema"],
        "source_model_commit": sidecar["source_model_commit"],
        "distinct_original_source_binary_silhouette_count": sidecar["distinct_original_source_binary_silhouette_count"],
        "experimental_glb_pose_count": sidecar["experimental_glb_pose_count"],
        "original_frame_observations": sidecar["original_frame_observations"],
        "sha256": digest(raw.encode("utf-8")),
        "out": str(args.out),
        "shipping_art_approved": False,
        "model_original_sprite_pose_mapping_verified": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
