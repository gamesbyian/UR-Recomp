#!/usr/bin/env python3
"""Prove 2026 authored pedal-platform orbit semantics from FIVE real source GLBs.

Unlike the independent JS math-only viewer test, this reads the original
OpenSCAD exporter artifacts and immutable receipts. All source 2026 poses,
not source-ROM 1994 frames. No geometric/aesthetic approval or new exporters.

The source writes fixed-axis aligned black footpads and orange treads,
translated along two opposite circular paths. OpenSCAD re-meshes the
rounded crank hull at each pose, so it must be reported as a faceted
approximation rather than falsely asserted byte-rigid.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

try:
    from tools.art.collar_transition_review import BASELINE_SOURCE_SHA256
    from tools.art.export_articulated_unicycle import pose_recipe
    from tools.art.verify_fork_pose_transport import (
        POSES, assert_sixteen_material_scene, read_original_export,
        rigid_relative_pose,
    )
except ModuleNotFoundError:
    from collar_transition_review import BASELINE_SOURCE_SHA256
    from export_articulated_unicycle import pose_recipe
    from verify_fork_pose_transport import (
        POSES, assert_sixteen_material_scene, read_original_export,
        rigid_relative_pose,
    )

PLATFORM_NAMES = ("pedals__material_1", "pedals__material_2")
CRANK_NAME = "pedals__material_0"
BASE_RADIUS = 0.31
FULL_CLOUD_MAX_DISTANCE = 4e-6
AXLE_SIDE_EXCLUSION_Y = 0.10


def sided_cloud(geometry, side: int) -> np.ndarray:
    """Take an actual material GLB triangle component from one spindle side."""
    if side not in (-1, 1):
        raise ValueError("side must be +1 or -1")
    points = np.asarray(geometry.vertices, dtype=np.float64)
    faces = np.asarray(geometry.faces, dtype=np.int64)
    if (points.ndim != 2 or points.shape[1] != 3 or not len(points)
            or faces.ndim != 2 or faces.shape[1] != 3 or not len(faces)
            or not np.isfinite(points).all()
            or (np.abs(points[:, 1]) <= AXLE_SIDE_EXCLUSION_Y).any()):
        raise ValueError("source pedal platform is absent, nonfinite or crosses spindle plane")
    indices = np.sign(points[:, 1])
    if not np.isin(indices, [-1, 1]).all():
        raise ValueError("invalid platform side assignment")
    if (faces.min() < 0 or faces.max() >= len(points)
            or (indices[faces] != indices[faces[:, 0]][:, None]).any()):
        raise ValueError("source material triangle bridges the two pedals")
    part = points[indices == side]
    if not len(part) or len(part) != len(points) - len(part):
        raise ValueError("source material lacks equal opposite platform vertex populations")
    return part


def bidirectional_nearest(a: np.ndarray, b: np.ndarray) -> dict:
    """Finite vertex-cloud discrepancy, explicitly NOT full-surface Hausdorff."""
    a, b = (np.asarray(x, dtype=np.float64) for x in (a, b))
    if (a.ndim != 2 or b.ndim != 2 or a.shape[1:] != (3,)
            or b.shape[1:] != (3,) or not len(a) or not len(b)
            or not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("finite, nonempty 3D vertex clouds required")
    forward = cKDTree(b).query(a, k=1)[0]
    backward = cKDTree(a).query(b, k=1)[0]
    return {
        "maximum_nearest_vertex_distance": float(max(forward.max(), backward.max())),
        "mean_bidirectional_nearest_vertex_distance": float(
            (forward.mean() + backward.mean()) / 2),
        "source_vertex_count": len(a),
        "target_vertex_count": len(b),
        "continuous_surface_distance_certified": False,
    }


def translated_platform(points, phase_from: float, phase_to: float,
                        side: int) -> np.ndarray:
    """Translate source 2026 pad geometry without local roll or deformation."""
    if (side not in (-1, 1) or not all(math.isfinite(v) for v in
                                      (phase_from, phase_to))):
        raise ValueError("invalid source crank phases")
    delta_x = side * BASE_RADIUS * (
        math.cos(math.radians(phase_to)) - math.cos(math.radians(phase_from)))
    delta_z = side * BASE_RADIUS * (
        math.sin(math.radians(phase_to)) - math.sin(math.radians(phase_from)))
    out = np.asarray(points, dtype=np.float64).copy()
    if out.ndim != 2 or out.shape[1:] != (3,) or not np.isfinite(out).all():
        raise ValueError("invalid source platform coordinates")
    out[:, 0] += delta_x
    out[:, 2] += delta_z
    return out


def rigid_crank_cloud(points: np.ndarray, phase_delta: float) -> np.ndarray:
    """Source-Y negative rotation, only a comparator for faceted rods."""
    if not math.isfinite(phase_delta):
        raise ValueError("invalid source crank angle")
    points = np.asarray(points, dtype=np.float64)
    if (points.ndim != 2 or points.shape[1:] != (3,)
            or not np.isfinite(points).all()):
        raise ValueError("invalid source rod coordinates")
    d = math.radians(phase_delta)
    c, s = math.cos(d), math.sin(d)
    out = points.copy()
    out[:, 0] = c * points[:, 0] - s * points[:, 2]
    out[:, 2] = s * points[:, 0] + c * points[:, 2]
    return out


def verify_source_pedalling(canonical_source: Path, pose_exports_root: Path) -> dict:
    raw = canonical_source.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    if source_sha != BASELINE_SOURCE_SHA256:
        raise ValueError("only canonical source-locked 2026 rig is accepted")
    source = raw.decode("utf-8")
    poses = {}
    for name in POSES:
        phase, saddle_lean, root = pose_recipe(source, name)
        scene, digest = read_original_export(pose_exports_root, name)
        assert_sixteen_material_scene(scene)
        # A static GLB child mesh is in its own wheel-local coordinates.
        # Root pose transformations are properly rigid and common to tire
        # and pedals; compare in this 2026 authoring frame, not world/stunt.
        relative, _ = rigid_relative_pose(
            scene.graph.get("tire")[0], scene.graph.get("pedals")[0],
            np.eye(4))
        if not np.allclose(relative, np.eye(4), atol=1e-8, rtol=0):
            raise ValueError("source pedal/tire parent transforms unexpectedly differ")
        for material in (*PLATFORM_NAMES, CRANK_NAME):
            geom = scene.geometry[material]
            if not geom.is_watertight or scene.graph.transforms.parents.get(material) != "pedals":
                raise ValueError("real GLB pedal material detached, or no closed source mesh")
        poses[name] = {"scene": scene, "glb_sha256": digest, "phase": phase,
                       "saddle_lean": saddle_lean}
    base = poses["upright"]
    base_colors = {
        material: np.unique(base["scene"].geometry[material].visual.vertex_colors,
                            axis=0) for material in (*PLATFORM_NAMES, CRANK_NAME)
    }
    per_pose = {}
    for name, item in poses.items():
        scene = item["scene"]
        platforms = {}
        for material in PLATFORM_NAMES:
            original = base["scene"].geometry[material]
            actual = scene.geometry[material]
            if (len(actual.faces) != len(original.faces)
                    or len(actual.vertices) != len(original.vertices)
                    or not np.array_equal(
                        np.unique(actual.visual.vertex_colors, axis=0),
                        base_colors[material])):
                raise ValueError("pad/tread topology or material identity changed")
            parts = {}
            for side in (1, -1):
                left = sided_cloud(original, side)
                right = sided_cloud(actual, side)
                compare = bidirectional_nearest(
                    translated_platform(left, base["phase"], item["phase"], side),
                    right)
                if compare["maximum_nearest_vertex_distance"] > FULL_CLOUD_MAX_DISTANCE:
                    raise ValueError("actual GLB footpad changes shape or orientation: "
                                     + name + "/" + material + "/" + str(side))
                parts[str(side)] = compare
            platforms[material] = parts
        original_crank = base["scene"].geometry[CRANK_NAME]
        actual_crank = scene.geometry[CRANK_NAME]
        if not np.array_equal(
                np.unique(actual_crank.visual.vertex_colors, axis=0),
                base_colors[CRANK_NAME]):
            raise ValueError("crank material paint identity changed")
        crank = bidirectional_nearest(
            rigid_crank_cloud(original_crank.vertices,
                              item["phase"] - base["phase"]),
            actual_crank.vertices)
        crank["source_triangle_count"] = len(original_crank.faces)
        crank["pose_triangle_count"] = len(actual_crank.faces)
        crank["source_angle_dependent_retriangulation_observed"] = (
            len(actual_crank.faces) != len(original_crank.faces))
        per_pose[name] = {
            "actual_original_source_glb_sha256": item["glb_sha256"],
            "source_authored_crank_phase_degrees": item["phase"],
            "source_authored_saddle_lean_degrees": item["saddle_lean"],
            "pedal_to_tire_frame_identity": True,
            "black_pad_and_orange_tread_source_translation": platforms,
            "crank_rod_rotated_mesh_vs_2026_resampled_hull": crank,
        }
    return {
        "schema": "UR-ART4K-FIVE-REAL-GLB-LEVEL-PEDAL-POSE-CENSUS/1",
        "canonical_scad_sha256": source_sha,
        "source_pose_receipts": per_pose,
        "black_pad_and_orange_tread_real_glb_translation_match": True,
        "platform_face_and_vertex_counts_preserved": True,
        "rigid_crank_preview_matches_independently_retriangulated_source_exactly": False,
        "crank_retriangulation_is_source_2026_faceting_not_original_1994_evidence": True,
        "source_1994_frame_timing_or_character_acting_recovered": False,
        "source_1994_mesh_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-source", type=Path, required=True)
    parser.add_argument("--source-pose-exports-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    report = verify_source_pedalling(a.canonical_source,
                                     a.source_pose_exports_root)
    with a.out.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({
        "schema": report["schema"],
        "five_authenticated_source_glbs": len(report["source_pose_receipts"]),
        "all_platform_translations_within": FULL_CLOUD_MAX_DISTANCE,
        "original_1994_kinematics_recovered": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
