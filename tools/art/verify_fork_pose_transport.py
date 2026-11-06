#!/usr/bin/env python3
"""Check whether five *authored 2026* pose transformations preserve fork/tire clearance.

This is a source-verified rigid-transport inference, NOT five independent
exports of the repaired fork, 1994 pose recovery, moving-joint clearance,
faceted-tire CSG, or owner/finished-art approval.

Reuses real five-part/16-material GLBs from the existing export/CI job.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

try:
    from tools.art.collar_transition_review import BASELINE_SOURCE_SHA256
    from tools.art.glb_roundtrip_guard import geometry_signature
    from tools.art.fork_tire_surface_certificate import certify_upright_review_fork
    from tools.art.verify_collar_transition_review import EXPECTED
except ModuleNotFoundError:
    from collar_transition_review import BASELINE_SOURCE_SHA256
    from glb_roundtrip_guard import geometry_signature
    from fork_tire_surface_certificate import certify_upright_review_fork
    from verify_collar_transition_review import EXPECTED

POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
MATERIALS = ("fork_and_frame__material_0",
             "tire__material_0", "tire__material_1")


def rigid_relative_pose(tire_transform, fork_transform, expected=None):
    """Return relative 4×4 transform and maximal deviation from expected.

    Reject non-rigid, reflection, nonfinite and unexpected fork/tire motion
    before claiming that a whole-surface certificate can be transported.
    """
    matrices = [np.asarray(t, dtype=np.float64)
                for t in (tire_transform, fork_transform)]
    for matrix in matrices:
        if (matrix.shape != (4, 4) or not np.isfinite(matrix).all()
                or not np.allclose(matrix[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
                or not np.allclose(matrix[:3, :3].T @ matrix[:3, :3],
                                   np.eye(3), atol=1e-6, rtol=0)
                or abs(np.linalg.det(matrix[:3, :3]) - 1) > 1e-6):
            raise ValueError("source tire/fork transform must be finite proper rigid")
    relative = np.linalg.inv(matrices[0]) @ matrices[1]
    if expected is None:
        return relative, 0.
    target = np.asarray(expected, dtype=np.float64)
    if target.shape != (4, 4) or not np.isfinite(target).all():
        raise ValueError("invalid expected relative frame")
    deviation = float(np.max(np.abs(relative - target)))
    if deviation > 1e-6:
        raise ValueError("fork/tire source pose has unshared relative motion")
    return relative, deviation


def read_original_export(root: Path, pose: str):
    """Use exact authorized output receipts, not a guessed basename/glob."""
    if pose not in POSES:
        raise ValueError("not one of the five authored source poses")
    folder = (root / pose).resolve()
    pointer = json.loads((folder / "articulated_blockout_current.json").read_text())
    latest = json.loads((folder / "articulated_blockout_last_attempt.json").read_text())
    if (pointer.get("schema") != "ur-art4k-export-current/1"
            or pointer.get("rig_pose") != pose
            or pointer.get("source_sha256") != BASELINE_SOURCE_SHA256
            or latest.get("status") != "succeeded"
            or pointer.get("attempt_id") != latest.get("attempt_id")):
        raise ValueError("pose export provenance differs from canonical 2026 rig")
    relative_path = Path(pointer["glb_path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("pose output escapes its source attempt directory")
    glb = (folder / relative_path).resolve()
    if not glb.is_relative_to(folder) or not glb.is_file():
        raise ValueError("missing exact pose GLB inside export root")
    raw = glb.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != pointer.get("glb_sha256"):
        raise ValueError("actual GLB differs from its immutable pose receipt")
    return trimesh.load(glb, force="scene", process=False), digest


def assert_sixteen_material_scene(scene):
    if (not isinstance(scene, trimesh.Scene) or scene.graph.base_frame != "world"
            or set(scene.geometry) != EXPECTED
            or set(scene.graph.nodes_geometry) != EXPECTED):
        raise ValueError("not the canonical five-parent sixteen-material GLB")
    for node in MATERIALS:
        if scene.graph.transforms.parents.get(node) != node.split("__")[0]:
            raise ValueError("source fork/tire material detached from parent")
        if not scene.geometry[node].is_watertight:
            raise ValueError("fork/tire source material must be watertight")


def verify_pose_transport(rounded_glb: Path, source_exports_root: Path):
    """Prove *conditional* five-pose rigid transport using actual source GLBs."""
    candidate = trimesh.load(rounded_glb, force="scene", process=False)
    assert_sixteen_material_scene(candidate)
    continuous = certify_upright_review_fork(candidate)
    if continuous["status"] != "certified":
        raise ValueError("rounded candidate lacks continuous ideal-torus certificate")
    candidate_relative, _ = rigid_relative_pose(
        candidate.graph.get("tire")[0],
        candidate.graph.get("fork_and_frame__material_0")[0])
    source_geometry = {}
    pose_proofs = {}
    for pose in POSES:
        scene, digest = read_original_export(source_exports_root, pose)
        assert_sixteen_material_scene(scene)
        hashes = {name: geometry_signature(scene.geometry[name])
                  for name in MATERIALS}
        colors = {name: np.unique(scene.geometry[name].visual.vertex_colors, axis=0)
                  for name in MATERIALS}
        if not source_geometry:
            source_geometry = {name: (hashes[name], colors[name])
                               for name in MATERIALS}
        for name in MATERIALS:
            previous_hash, previous_colors = source_geometry[name]
            if hashes[name] != previous_hash or not np.array_equal(
                    colors[name], previous_colors):
                raise ValueError("source pose changes fork/tire shape or paint: "
                                 + pose + "/" + name)
            if name.startswith("tire__"):
                if (geometry_signature(candidate.geometry[name]) != hashes[name]
                        or not np.array_equal(
                            np.unique(candidate.geometry[name].visual.vertex_colors, axis=0),
                            colors[name])):
                    raise ValueError("rounded fork changed source tire/stripe material")
        _, error = rigid_relative_pose(
            scene.graph.get("tire")[0],
            scene.graph.get("fork_and_frame__material_0")[0],
            candidate_relative)
        pose_proofs[pose] = {
            "canonical_source_glb_sha256": digest,
            "fork_tire_relative_transform_error_max_abs": error,
            "source_fork_and_both_tire_materials_same_oriented_surfaces": True,
            "shared_proper_rigid_pose": True,
        }
    return {
        "schema": "UR-ART4K-ROUND-FORK-FIVE-SOURCE-POSE-TRANSPORT/1",
        "rounded_upright_glb_sha256": hashlib.sha256(
            rounded_glb.read_bytes()).hexdigest(),
        "canonical_source_scad_sha256": BASELINE_SOURCE_SHA256,
        "source_material_oriented_triangle_sha256": {
            name: source_geometry[name][0] for name in MATERIALS
        },
        "source_pose_rigid_transform_receipts": pose_proofs,
        "five_authored_pose_relative_fork_tire_frames_congruent": True,
        "derived_ideal_torus_clearance_preserved_under_those_same_rigid_root_poses": True,
        "repaired_fork_independently_exported_in_all_five_poses": False,
        "real_faceted_tire_boolean_clearance_proved": False,
        "independent_animated_joints_or_deformations_cleared": False,
        "original_1994_pose_geometry_or_likeness_recovered": False,
        "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounded-upright-glb", type=Path, required=True)
    parser.add_argument("--canonical-pose-exports-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify_pose_transport(args.rounded_upright_glb,
                                   args.canonical_pose_exports_root)
    with args.out.open("x", encoding="utf-8") as file:
        json.dump(report, file, sort_keys=True, indent=2)
        file.write("\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
