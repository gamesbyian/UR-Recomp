#!/usr/bin/env python3
"""Bounded continuous fork-triangle clearance against 2026 authored ideal tori.

The signed distance to either ideal torus solid is 1-Lipschitz. For each
triangle, d(centroid) minus its maximum vertex radius bounds the signed
distance over its *entire* surface. Split unresolved triangles, never
pretend budget exhaustion proved clearance.

Not a continuous Boolean check against the faceted GLB tire, any stunt pose,
a recovered original 1994 geometry, or art approval.
"""
from __future__ import annotations

import numpy as np


def certify_triangles_against_source_tori(
    world_triangles, tire_to_world=None, *, max_depth=10,
    max_pending=500_000, margin=1e-7,
):
    triangles = np.asarray(world_triangles, dtype=np.float64)
    if (triangles.ndim != 3 or triangles.shape[1:] != (3, 3)
            or not len(triangles) or not np.isfinite(triangles).all()):
        raise ValueError("finite nonempty Nx3x3 fork triangles required")
    frame = (np.eye(4) if tire_to_world is None
             else np.asarray(tire_to_world, dtype=np.float64))
    rotation = frame[:3, :3] if frame.shape == (4, 4) else None
    if (rotation is None or not np.isfinite(frame).all()
            or not np.allclose(frame[3], [0, 0, 0, 1], rtol=0, atol=1e-8)
            or not np.allclose(rotation.T @ rotation, np.eye(3),
                               rtol=0, atol=1e-6)
            or abs(np.linalg.det(rotation) - 1) > 1e-6):
        raise ValueError("finite rigid right-handed tire-to-world transform required")
    if (not isinstance(max_depth, int) or not 0 <= max_depth <= 14
            or not isinstance(max_pending, int) or max_pending < 4
            or not np.isfinite(margin) or margin < 0):
        raise ValueError("invalid bounded triangle certification controls")

    # Row vectors: world = local @ R.T + translation.
    pending = (triangles - frame[:3, 3]) @ rotation
    seen, max_batch = 0, len(pending)
    best_probe = np.array([np.inf, np.inf])
    proven_bound = np.array([np.inf, np.inf])
    status, unresolved = "inconclusive", 0
    for depth in range(max_depth + 1):
        centers = pending.mean(axis=1)
        radii = np.linalg.norm(pending - centers[:, None, :], axis=2).max(axis=1)
        radial = np.hypot(centers[:, 0], centers[:, 2])
        distances = np.stack((
            np.hypot(radial - .85, centers[:, 1]) - .15,
            np.hypot(radial - .80, centers[:, 1] + .15) - .028,
        ), axis=1)
        if not np.isfinite(distances).all():
            raise ValueError("nonfinite computed torus clearance")
        seen += len(pending)
        best_probe = np.minimum(best_probe, distances.min(axis=0))
        if np.any(distances <= 0):
            status = "penetration"
            break
        bounds = distances - radii[:, None]
        safe = np.all(bounds > margin, axis=1)
        if np.any(safe):
            proven_bound = np.minimum(proven_bound, bounds[safe].min(axis=0))
        unresolved = int(np.count_nonzero(~safe))
        if not unresolved:
            status = "certified"
            break
        if depth == max_depth or 4 * unresolved > max_pending:
            break
        a, b, c = np.moveaxis(pending[~safe], 1, 0)
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        pending = np.concatenate((
            np.stack((a, ab, ca), axis=1),
            np.stack((ab, b, bc), axis=1),
            np.stack((ca, bc, c), axis=1),
            np.stack((ab, bc, ca), axis=1),
        ))
        max_batch = max(max_batch, len(pending))
    return {
        "schema": "UR-ART4K-FORK-IDEAL-TORUS-SURFACE/1",
        "status": status,
        "continuous_fork_surface_cleared_against_ideal_tori": status == "certified",
        "input_triangle_count": int(len(triangles)),
        "centroid_probes": int(seen),
        "max_pending_batch": int(max_batch),
        "depth_reached": int(depth),
        "unresolved_at_exit": unresolved if status == "inconclusive" else 0,
        "minimum_observed_center_signed_distance": {
            "main_tire": float(best_probe[0]),
            "near_sidewall_stripe": float(best_probe[1]),
        },
        "certified_minimum_signed_distance_lower_bound": (
            {"main_tire": float(proven_bound[0]),
             "near_sidewall_stripe": float(proven_bound[1])}
            if status == "certified" else None
        ),
        "continuous_actual_triangulated_tire_cleared": False,
        "stunt_pose_or_moving_clearance_proved": False,
        "original_1994_mesh_recovered": False,
        "owner_likeness_approved": False,
    }


def certify_upright_review_fork(scene):
    """Audit actual GLB fork triangles in the upright source tire frame."""
    import trimesh
    transform, mesh_name = scene.graph.get("fork_and_frame__material_0")
    mesh = scene.geometry[mesh_name]
    if mesh.faces.size == 0:
        raise ValueError("source fork has no triangles")
    world_vertices = trimesh.transform_points(mesh.vertices, transform)
    tire_transform, _ = scene.graph.get("tire")
    return certify_triangles_against_source_tori(
        world_vertices[np.asarray(mesh.faces, dtype=int)], tire_transform
    )
