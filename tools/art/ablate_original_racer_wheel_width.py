#!/usr/bin/env python3
"""Opt-in real-GLB wheel-width hypothesis ablation against original source masks.

Read-only; NEVER edits a canonical GLB, 1994 sprite, viewer or OpenSCAD rig.
The wheel and rim X coordinates move together in memory only. One fixed
provisional camera and the source-registered contact are reused for all shapes.
Results cannot identify original 3D wheel shape or authentic pose correspondence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import CAMERA, inspect_viewer, safe_existing_path
    from tools.art.build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from tools.art.build_racer_source_pixel_corpus import build as source_corpus, REGISTRY
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.render_racer_glb_projection import render_mask, camera_config
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import CAMERA, inspect_viewer, safe_existing_path
    from build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from build_racer_source_pixel_corpus import build as source_corpus, REGISTRY
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from render_racer_glb_projection import render_mask, camera_config
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-REAL-GLB-WHEEL-X-ABLATION/1"
FACTORS = (0.90, 1.0, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30)
WHEEL_PREFIXES = ("tire__material_", "rim_and_hub__material_")


def wheel_node(name: str) -> bool:
    return isinstance(name, str) and name.startswith(WHEEL_PREFIXES)


def scale_component_x(vertices, name: str, factor: float):
    """Return changed-or-unchanged mesh coordinates without mutating input."""
    import numpy as np
    if (type(factor) is not float or not .85 <= factor <= 1.35
            or type(name) is not str or not name):
        raise ValueError("unsupported bounded wheel ablation factor/node")
    xyz = np.asarray(vertices)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
        raise ValueError("invalid mesh coordinates")
    new = xyz.copy()
    if wheel_node(name):
        new[:, 0] *= factor
    return new


def ablated_world_mesh(scene, factor: float):
    import numpy as np
    import trimesh
    parts = []
    touched = set()
    names = set(scene.graph.nodes_geometry)
    if not names or any(not isinstance(x, str) for x in names):
        raise ValueError("scene lacks named geometry")
    for node in sorted(names):
        world, geometry = scene.graph.get(node)
        mesh = scene.geometry[geometry].copy()
        mesh.apply_transform(world)
        before = np.asarray(mesh.vertices).copy()
        mesh.vertices = scale_component_x(before, node, factor)
        if wheel_node(node):
            touched.add(node.split("__material_")[0])
        elif not np.array_equal(before, mesh.vertices):
            raise ValueError("non-wheel geometry was changed")
        parts.append(mesh)
    if touched != {"tire", "rim_and_hub"}:
        raise ValueError("real source wheel and rim parts missing")
    merged = trimesh.util.concatenate(parts)
    return np.asarray(merged.vertices), np.asarray(merged.faces)


def source_shapes(site: Path):
    """Independent source hash/camera-contact proof, not a pose classifier."""
    corpus = source_corpus()
    original = {(o["player"], o["guest_frame"]): o
                for o in corpus["observations"]}
    if len(original) != 32 or corpus["distinct_binary_silhouette_groups"] != 10:
        raise ValueError("not the frozen authentic first-family original")
    contacts = original_registered_contacts(
        REGISTRY, corpus["source_registry_current_sha256"])
    rail = json.loads((site / "sprites.json").read_text())
    if len(rail.get("frames", [])) != 32:
        raise ValueError("original source reference rail incomplete")
    groups = {}
    seen = set()
    for item in rail["frames"]:
        key = (item.get("player"), item.get("guest_frame"))
        if key in seen or key not in original:
            raise ValueError("duplicate/foreign original sprite frame")
        seen.add(key)
        expected = original[key]
        if (item.get("sha256") != expected["png_file_sha256"] or
                item.get("representation_id") != expected["representation_id"]):
            raise ValueError("original representation/PNG mismatch")
        file = safe_existing_path(site, item["image"], ".png")
        w, h, rgba, actual_sha = decode_rgba_png(file)
        metrics = alpha_metrics(rgba, w, h)
        if ((w, h) != (64, 64) or actual_sha != expected["png_file_sha256"]
                or metrics["source_rgba_sha256"] != expected["source_rgba_sha256"]
                or metrics["binary_mask_sha256"] != expected["binary_mask_sha256"]):
            raise ValueError("source raster changed from exact original")
        mask = bytes(int(v != 0) for v in rgba[3::4])
        registered = contacts.get(item["representation_id"])
        if (registered is None or registered[0] != key[0] or
                original_lowest_alpha_anchor(mask) != registered[1]):
            raise ValueError("source semantic contact anchor disagrees with original pixels")
        mask_sha = hashlib.sha256(mask).hexdigest()
        current = groups.setdefault(mask_sha, (mask, registered[1], []))
        if current[0] != mask or current[1] != registered[1]:
            raise ValueError("original identical silhouette has different contact")
        current[2].append(key)
    if len(groups) != 10 or len(seen) != 32:
        raise ValueError("original source first-family mask census changed")
    return groups, corpus


def compute(site: Path, camera_file: Path = CAMERA) -> dict:
    import trimesh
    model, _, poses = inspect_viewer(site)
    camera_bytes = camera_file.read_bytes()
    camera = json.loads(camera_bytes)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional"
            or camera.get("source_witness", {}).get("player") != "p1"
            or camera.get("source_witness", {}).get("guest_frame") != 1205
            or camera.get("source_anchor_x2_y2") != [67, 76]):
        raise ValueError("only fixed original P1:1205 provisional camera is allowed")
    original, corpus = source_shapes(site)
    path = poses["upright"]
    scene = trimesh.load(str(path), file_type="glb", force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("source GLB scene required")
    samples = []
    for factor in FACTORS:
        vertices, faces = ablated_world_mesh(scene, float(factor))
        mask4 = render_mask(vertices, faces, camera)
        candidate = bytes(int(v) for v in mask4[2::4, 2::4].reshape(-1))
        if len(candidate) != 4096 or not any(candidate):
            raise ValueError("invalid camera model silhouette")
        results = []
        for sha, (source, contact, observations) in sorted(original.items()):
            dx2 = contact[0] - 67
            dy2 = contact[1] - 76
            if dx2 % 2 or dy2 % 2:
                raise ValueError("source contact shift is fractional")
            moved = translated_binary_mask(candidate, dx2 // 2, dy2 // 2)
            measured = score(source, moved)
            results.append({
                "source_binary_mask_sha256": sha,
                "original_frame_count": len(observations),
                "mask_iou": measured["mask_iou"],
                "boundary_chamfer_mean_physical_px":
                    measured["boundary_chamfer_mean_physical_px"],
            })
        samples.append({
            "wheel_and_rim_world_x_factor": factor,
            "only_wheel_and_rim_modified_in_memory": True,
            "candidate_opaque_logical_pixels": sum(candidate),
            "equal_original_mask_weighted_mean_iou":
                round(sum(x["mask_iou"] for x in results)/len(results), 8),
            "worst_original_mask_iou": round(min(x["mask_iou"] for x in results), 8),
            "equal_original_mask_weighted_mean_physical_boundary_chamfer":
                round(sum(x["boundary_chamfer_mean_physical_px"] for x in results)/len(results), 8),
            "per_original_mask": results,
        })
    return {
        "schema": SCHEMA,
        "viewer_model_source_commit": model["source_commit"],
        "viewer_model_scad_sha256": model["source_model_sha256"],
        "original_rom_sha256":
            corpus["historical_manifest_declared_rom_sha256"],
        "original_registry_sha256":
            corpus["source_registry_current_sha256"],
        "actual_original_upright_glb_sha256":
            model["poses"]["upright"]["sha256"],
        "provisional_camera_sha256": hashlib.sha256(camera_bytes).hexdigest(),
        "original_binary_shape_count": len(original),
        "original_source_observation_count": 32,
        "experiment": "single upright 2026 experimental GLB, constant physical 7:6 camera, source-registered bottom-alpha placement; only wheel+rim world X stretched across all shapes",
        "tested_factors_are_not_optimized_against_a_heldout_family": True,
        "authentic_1994_camera_identified": False,
        "original_1994_sprite_to_blockout_pose_mapped": False,
        "independent_original_pose_family_holdout_tested": False,
        "original_character_likeness_approved": False,
        "shipping_art_approved": False,
        "samples": samples,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir", type=Path, required=True)
    ap.add_argument("--camera", type=Path, default=CAMERA)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    text = json.dumps(compute(args.model_review_dir, args.camera),
                      indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
