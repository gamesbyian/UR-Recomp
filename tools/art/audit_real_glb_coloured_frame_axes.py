#!/usr/bin/env python3
"""Measure the REAL five-GLB experimental coloured frame projection axis.

One fixed provisional 7:6 original camera hypothesis, existing single viewer
with original source raster and model hashes, *not* original sprite-to-rig
pose pairing or recovered 1994 model/pose pivot. Never changes or exports art.
Requires optional offline numpy, Trimesh and Pillow already used by renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import CAMERA, POSES, inspect_viewer
    from tools.art.audit_original_racer_chromatic_axes import principal_axis
    from tools.art.render_racer_glb_projection import camera_config, render_mask
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import CAMERA, POSES, inspect_viewer
    from audit_original_racer_chromatic_axes import principal_axis
    from render_racer_glb_projection import camera_config, render_mask
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-UNPAIRED-FIVE-GLB-COLOUR-FRAME-AXES/1"
FRAME = "fork_and_frame__material_0"
SOURCE_BLUE = (28, 89, 222, 255)


def source_colour_frame_pixels(scene, camera):
    import numpy as np
    import trimesh

    if set(("fork_and_frame", FRAME)) - set(scene.graph.nodes):
        raise ValueError("GLB missing original 2026 procedural frame material")
    if FRAME not in scene.graph.nodes_geometry:
        raise ValueError("original GLB blue frame has no material geometry")
    if scene.graph.transforms.parents.get(FRAME) != "fork_and_frame":
        raise ValueError("GLB blue frame material detached from one canonical parent")
    world, geometry = scene.graph.get(FRAME)
    mesh = scene.geometry[geometry]
    if not isinstance(mesh, trimesh.Trimesh) or not mesh.is_watertight:
        raise ValueError("invalid source frame geometry")
    if (mesh.visual.kind != "vertex" or
            not np.all(np.asarray(mesh.visual.vertex_colors) == SOURCE_BLUE)):
        raise ValueError("real original blockout blue frame has changed colour")
    owned = mesh.copy()
    owned.apply_transform(world)
    alpha4x = render_mask(np.asarray(owned.vertices), np.asarray(owned.faces), camera)
    source64 = alpha4x[2::4, 2::4]
    yx = np.argwhere(source64)
    if len(yx) < 4:
        raise ValueError("experimental frame projection lacks pixels")
    return [(int(x), int(y)) for y, x in yx]


def audit(site: Path, camera_path: Path = CAMERA) -> dict:
    import trimesh

    model, _, poses = inspect_viewer(site)
    raw_camera = camera_path.read_bytes()
    camera = json.loads(raw_camera)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional" or
            camera.get("source_witness", {}).get("player") != "p1" or
            camera.get("source_witness", {}).get("guest_frame") != 1205 or
            camera.get("source_anchor_x2_y2") != [67, 76]):
        raise ValueError("only one explicit original first-family provisional camera allowed")
    records = {}
    for pose in POSES:
        # A preflight in inspect_viewer is not a proof of bytes consumed later.
        data = poses[pose].read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != model["poses"][pose]["sha256"]:
            raise ValueError("real source GLB changed since viewer hash verification")
        scene = trimesh.load(io.BytesIO(data), file_type="glb", force="scene",
                             process=False)
        if not isinstance(scene, trimesh.Scene):
            raise ValueError("source GLB did not preserve actual named scene graph")
        original_source_frame = source_colour_frame_pixels(scene, camera)
        records[pose] = {
            "actual_source_glb_sha256": sha,
            "existing_blockout_material_node": FRAME,
            "source_material_rgba": list(SOURCE_BLUE),
            **principal_axis(original_source_frame),
        }
    return {
        "schema": SCHEMA,
        "model_source_commit_claim_from_viewer": model["source_commit"],
        "actual_model_source_scad_sha256": model["source_model_sha256"],
        "existing_viewer_model_manifest_sha256":
            hashlib.sha256((site / "manifest.json").read_bytes()).hexdigest(),
        "existing_provisional_camera_sha256": hashlib.sha256(raw_camera).hexdigest(),
        "original_1994_sprite_and_2026_GLBS_are_unpaired": True,
        "model_frame_axis_is_equivalent_to_original_source_coloured_body_axis": False,
        "source_chromatic_pixels_have_authenticated_1994_3d_part_identity": False,
        "one_shared_2026_experimental_rig_not_accepted_art": True,
        "original_3d_camera_or_pivot_verified": False,
        "source_3d_pose_mapping_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "five_model_poses": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-review-dir", required=True, type=Path)
    parser.add_argument("--camera", type=Path, default=CAMERA)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = json.dumps(audit(args.model_review_dir, args.camera),
                      indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
