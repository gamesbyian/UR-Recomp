#!/usr/bin/env python3
"""Audit *actual* five-pose viewer GLBs for geometry continuity and animation.

Research diagnostic only: no inferred 1994 source-pose mapping, no new rig.
Source GLBs and viewer original sprites are independently hash-verified first.
Requires optional numpy/trimesh for offline model inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

try:
    from tools.art.audit_real_viewer_glbs import inspect_viewer, POSES
    from tools.art.render_racer_glb_projection import model_mesh, np, trimesh
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_real_viewer_glbs import inspect_viewer, POSES
    from render_racer_glb_projection import model_mesh, np, trimesh
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-FIVE-GLB-RIG-CONTINUITY-AUDIT/1"
PARTS = ("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")


def glb_structure(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise ValueError("invalid GLB header")
    version, length = struct.unpack_from("<II", raw, 4)
    size, tag = struct.unpack_from("<I4s", raw, 12)
    if (version != 2 or length != len(raw) or tag != b"JSON" or
            size < 2 or size > len(raw)-20):
        raise ValueError("invalid GLB version, chunk length or JSON")
    body = json.loads(raw[20:20+size])
    if not isinstance(body, dict) or body.get("asset", {}).get("version") != "2.0":
        raise ValueError("invalid glTF 2.0 structure")
    for key in ("animations", "skins", "meshes", "nodes"):
        if key in body and not isinstance(body[key], list):
            raise ValueError("invalid GLB "+key)
    return {key: len(body.get(key, [])) for key in
            ("animations", "skins", "meshes", "nodes")}


def geometry_fingerprint(mesh) -> str:
    """Hash the actual *local* mesh vertex/index buffers, not world transforms."""
    if np is None:
        raise RuntimeError("numpy required for offline geometry audit")
    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    if (len(vertices) < 3 or len(faces) < 1 or
            not np.isfinite(vertices).all() or
            not np.issubdtype(faces.dtype, np.integer)):
        raise ValueError("empty or non-finite GLB mesh")
    # Canonical dtype stabilizes local endianness and compiler array types.
    raw = vertices.astype("<f4", copy=False).tobytes()
    raw += faces.astype("<i4", copy=False).tobytes()
    return hashlib.sha256(raw).hexdigest()


def summarize_components(per_pose: dict) -> dict:
    """Pure bounded reducer, synthetic-testable without optional GLB modules."""
    if set(per_pose) != set(POSES):
        raise ValueError("exact five named studies required")
    names = None
    for pose in POSES:
        value = per_pose[pose]
        if not isinstance(value, dict) or not value:
            raise ValueError("missing pose mesh measurements")
        if names is None:
            names = set(value)
        if set(value) != names:
            raise ValueError("pose component set differs from other exported GLBs")
    if not all(any(name.startswith(part+"__material_") for name in names) for part in PARTS):
        raise ValueError("one of the five part parent material groups is missing")
    result = {}
    for name in sorted(names):
        values = [per_pose[pose][name] for pose in POSES]
        for row in values:
            if (not isinstance(row.get("local_mesh_sha256"), str) or
                    len(row["local_mesh_sha256"]) != 64 or
                    type(row.get("triangle_count")) is not int or row["triangle_count"] <= 0):
                raise ValueError("invalid local mesh metric")
        hashes = {v["local_mesh_sha256"] for v in values}
        triangles = {v["triangle_count"] for v in values}
        result[name] = {
            "local_mesh_identical_across_poses": len(hashes) == 1,
            "triangle_count_varies_across_poses": len(triangles) > 1,
            "triangle_count_by_pose": {
                pose: per_pose[pose][name]["triangle_count"] for pose in POSES},
            "local_mesh_sha256_by_pose": {
                pose: per_pose[pose][name]["local_mesh_sha256"] for pose in POSES},
        }
    return {
        "component_count": len(names),
        "exact_local_mesh_reused_component_count": sum(
            v["local_mesh_identical_across_poses"] for v in result.values()),
        "pose_dependent_local_mesh_component_count": sum(
            not v["local_mesh_identical_across_poses"] for v in result.values()),
        "pose_dependent_triangle_topology_component_count": sum(
            v["triangle_count_varies_across_poses"] for v in result.values()),
        "components": result,
    }


def audit(site: Path) -> dict:
    if np is None or trimesh is None:
        raise RuntimeError("offline geometry audit requires numpy and trimesh")
    model, _, paths = inspect_viewer(site)  # Also verifies all 32 original refs.
    records, structure = {}, {}
    for pose in POSES:
        path = paths[pose]
        structure[pose] = glb_structure(path)
        verts, faces, _, count = model_mesh(path, model["poses"][pose]["sha256"])
        scene = trimesh.load_scene(path, file_type="glb", process=False)
        names = set(scene.geometry)
        # This particular published exporter promises material-split meshes
        # with exactly one parent for each of its five assembly parts.
        if not set(PARTS).issubset(scene.graph.nodes):
            raise ValueError("GLB missing articulated part parent nodes")
        if set(scene.graph.nodes_geometry) != names:
            raise ValueError("viewer GLB geometry-node identity ambiguous")
        records[pose] = {}
        for name in sorted(names):
            mesh = scene.geometry[name]
            records[pose][name] = {
                "local_mesh_sha256": geometry_fingerprint(mesh),
                "triangle_count": int(len(mesh.faces)),
            }
        if structure[pose]["meshes"] != len(names) or structure[pose]["nodes"] != count:
            raise ValueError("GLB JSON mesh/node counts disagree with scene")
    summary = summarize_components(records)
    return {
        "schema": SCHEMA,
        "source_model_commit": model["source_commit"],
        "source_scad_sha256": model["source_model_sha256"],
        "source_five_pose_glb_sha256": {
            pose: model["poses"][pose]["sha256"] for pose in POSES},
        "glb_structure_by_pose": structure,
        **summary,
        "separate_pose_snapshot_glbs": True,
        "all_five_have_embedded_animation_channels": all(
            structure[p]["animations"] > 0 for p in POSES),
        "all_five_have_gltf_skins": all(
            structure[p]["skins"] > 0 for p in POSES),
        "local_geometry_hash_is_a_3d_kinematic_authenticity_proof": False,
        "source_1994_rig_kinematics_recovered": False,
        "original_sprite_to_experimental_pose_mapping_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "viewer_files_modified": False,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = audit(args.model_review_dir)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
