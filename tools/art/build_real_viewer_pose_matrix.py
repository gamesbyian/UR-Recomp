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
    from tools.art.build_racer_source_pixel_corpus import build as source_corpus, REGISTRY
    from tools.art.racer_source_pixels import alpha_metrics, decode_rgba_png
    from tools.art.render_racer_glb_projection import camera_config, model_mesh, render_mask
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import CAMERA, POSES, inspect_viewer, safe_existing_path
    from build_racer_source_pixel_corpus import build as source_corpus, REGISTRY
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
        for pose in pose_names:
            number = results[pose].get("mask_iou")
            chamfer = results[pose].get("boundary_chamfer_mean_physical_px")
            if (type(number) not in (int, float) or not 0 <= number <= 1 or
                    type(chamfer) not in (int, float) or not 0 <= chamfer < 1e4):
                raise ValueError("invalid silhouette IoU or boundary Chamfer")
            totals[pose].append(number)
        ordered = sorted(pose_names, key=lambda pose: (
            -results[pose]["mask_iou"],
            results[pose]["boundary_chamfer_mean_physical_px"], pose))
        if row.get("unpaired_best_fit_pose") != ordered[0]:
            raise ValueError("claimed best pose disagrees with scored silhouettes")
        winners[ordered[0]] += 1
    return {
        "equal_source_mask_weighted_mean_iou_by_experimental_pose": {
            name: round(sum(totals[name]) / len(totals[name]), 8)
            for name in pose_names
        },
        "unpaired_highest_iou_source_mask_count_by_experimental_pose": winners,
        "winner_is_authentic_original_pose_mapping": False,
        "not_a_heldout_measurement": True,
    }


def translated_binary_mask(mask: bytes, logical_dx: int, logical_dy: int) -> bytes:
    """Apply ONLY independently registered integer source-object placement.

    No image feature tracking, IoU-optimizing shift, nearest candidate search,
    silent clipping, size change, or guessed half-pixel rounding is allowed.
    """
    if len(mask) != 64 * 64 or type(logical_dx) is not int or type(logical_dy) is not int:
        raise ValueError("registered placement needs 64x64 binary mask and integer shift")
    shifted = bytearray(64 * 64)
    for at, pixel in enumerate(mask):
        if not pixel:
            continue
        if pixel != 1:
            raise ValueError("source candidate mask must be strictly binary")
        y, x = divmod(at, 64)
        new_x, new_y = x + logical_dx, y + logical_dy
        if not 0 <= new_x < 64 or not 0 <= new_y < 64:
            raise ValueError("verified registered placement would clip model")
        shifted[new_y * 64 + new_x] = 1
    return bytes(shifted)


def original_lowest_alpha_anchor(mask: bytes) -> tuple[int, int]:
    """Original source-visible lowest alpha midpoint, in half-pixel units.

    This is *not* independent evidence of the tire's physical road contact.
    It is recomputed from the actual authenticated PNG rather than inferred
    from the model, the score, or self-reported registry metadata.
    """
    if len(mask) != 64 * 64 or any(x not in (0, 1) for x in mask):
        raise ValueError("source lowest-alpha calculation needs binary 64x64 raster")
    occupied = [i for i, x in enumerate(mask) if x]
    if not occupied:
        raise ValueError("source original sprite has no visible alpha")
    y = max(i // 64 for i in occupied)
    bottom_x = [i % 64 for i in occupied if i // 64 == y]
    return (min(bottom_x) + max(bottom_x), 2 * y)


def original_registered_contacts(registry_path: Path, corpus_sha: str) -> dict:
    """Use existing original source semantic anchors, never infer from IoU."""
    raw = registry_path.read_bytes()
    if digest(raw) != corpus_sha:
        raise ValueError("source corpus / original registry SHA mismatch")
    registry = json.loads(raw)
    if registry.get("schema_version") != 1:
        raise ValueError("invalid original racer representation registry")
    contacts = {}
    for entry in registry.get("entries", []):
        identity = entry.get("representation_id")
        reg = entry.get("registration")
        if not isinstance(reg, dict) or reg.get("logical_canvas_pixels") != [64, 64]:
            raise ValueError("original source registration is not a 64px source canvas")
        anchors = reg.get("semantic_anchors") or {}
        anchor = anchors.get("wheel_contact_x2_y2")
        if (anchors.get("fixed_point_scale") != 2 or
                not isinstance(anchor, list) or len(anchor) != 2 or
                any(type(x) is not int or not -256 <= x <= 256 for x in anchor) or
                identity in contacts):
            raise ValueError("original source contact anchor missing, invalid or duplicate")
        contacts[identity] = (entry["player"], tuple(anchor))
    return contacts


def compute(site: Path, camera_path: Path = CAMERA,
            registration_mode: str = "fixed-witness") -> dict:
    model, _, pose_files = inspect_viewer(site)
    camera_raw = camera_path.read_bytes()
    camera = json.loads(camera_raw)
    camera_config(camera)
    witness = camera.get("source_witness")
    if (camera.get("camera_calibration_status") != "provisional" or
            not isinstance(witness, dict) or
            (witness.get("player"), witness.get("guest_frame")) != ("p1", 1205)):
        raise ValueError("only the explicit original P1:1205 provisional camera is supported")
    if registration_mode not in ("fixed-witness", "source-registered"):
        raise ValueError("registration mode must be fixed-witness or source-registered")
    original = source_corpus()
    contacts = (original_registered_contacts(REGISTRY, original["source_registry_current_sha256"])
                if registration_mode == "source-registered" else {})
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
        contact = None
        if registration_mode == "source-registered":
            registered = contacts.get(ref["representation_id"])
            if registered is None or registered[0] != ref["player"]:
                raise ValueError("source sprite identity has no player-correct registered contact")
            contact = registered[1]
        mask = bytes(1 if x else 0 for x in rgba[3::4])
        binary_sha = digest(mask)
        if binary_sha != metrics["binary_mask_sha256"]:
            raise ValueError("corrupted original binary mask")
        if (registration_mode == "source-registered" and
                original_lowest_alpha_anchor(mask) != contact):
            raise ValueError("source registry contact disagrees with authenticated original PNG alpha")
        group = source_groups.setdefault(binary_sha, {
            "mask": mask,
            "source_binary_mask_sha256": binary_sha,
            "source_opaque_pixels": metrics["nonzero_alpha_pixels"],
            "source_registered_contact_x2_y2": contact,
            "original_source_observations": [],
        })
        if group["mask"] != mask:
            raise ValueError("original binary group hash collision")
        if group["source_registered_contact_x2_y2"] != contact:
            raise ValueError("identical original binary source mask has conflicting contact anchors")
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
        anchor = group["source_registered_contact_x2_y2"]
        shift = (0, 0)
        if registration_mode == "source-registered":
            base = camera["source_anchor_x2_y2"]
            delta = [anchor[i] - base[i] for i in (0, 1)]
            if any(x % 2 for x in delta):
                raise ValueError("source 1/2-pixel contact parity requires explicit 4x rerender")
            shift = (delta[0] // 2, delta[1] // 2)
        for pose, item in candidates.items():
            candidate = (translated_binary_mask(item["binary_mask"], *shift)
                         if registration_mode == "source-registered"
                         else item["binary_mask"])
            measured = score(group["mask"], candidate)
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
            "registered_original_contact_x2_y2": (list(anchor) if anchor is not None else None),
            "source_registered_logical_xy_translation": list(shift),
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
        "registration_mode": registration_mode,
        "registered_original_contact_used_without_optimization": registration_mode == "source-registered",
        "registered_contact_is_original_lowest_alpha_not_physical_collision_contact": True,
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
    ap.add_argument("--registration-mode",
                    choices=("fixed-witness", "source-registered"),
                    default="fixed-witness",
                    help="use one P1-1205 anchor everywhere, or each source-authenticated contact")
    ap.add_argument("--out", type=Path,
                    help="optional one-time JSON receipt, never replace existing")
    args = ap.parse_args()
    report = compute(args.model_review_dir, args.camera, args.registration_mode)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
