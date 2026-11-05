#!/usr/bin/env python3
"""Reversible, source-mesh-local saddle *contour* experiment on the one 2026 GLB.

A uniform longitudinal scale cannot distinguish the 2026 saddle's cup from its
length. This frozen experiment varies only the central upper-surface hollow:
the outer X tips, lowest 20% of the saddle, mount, graph, other four parts,
faces and sixteen source-authored material groups remain intact. Neither
candidate is a recovered 1994 sculpt or approved original character likeness.
"""
from __future__ import annotations

from contextlib import contextmanager
import math

CUP_OFFSETS = (-0.08, 0.08)  # frozen authored 2026 GLB units; minus deepens hollow


def _validate_cup(cup):
    if type(cup) not in (float, int) or float(cup) not in CUP_OFFSETS:
        raise ValueError("only preregistered signed 0.08 saddle cup offsets permitted")


def cup_vertices(vertices, cup, bounds):
    """Shape-only, shared-bounds center-cup sculpt; no fitted role/frame input.

    bounds=(all-saddle xmin,xmax,zmin,zmax), shared by both color meshes.
    Displacement is zero at both X tips, and through the bottom 20% of Z.
    Smoothstep in Z and squared parabolic X taper keep the original mounting
    volume untouched and avoid a seam between the two saddle materials.
    """
    _validate_cup(cup)
    try:
        limits = tuple(float(x) for x in bounds)
        rows = tuple(tuple(float(x) for x in row) for row in vertices)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("finite source saddle vertices and shared bounds required") from exc
    if (len(limits) != 4 or any(not math.isfinite(v) for v in limits)
            or limits[1] - limits[0] <= 1e-9
            or limits[3] - limits[2] <= 1e-9
            or not rows or any(len(row) != 3 or
                                any(not math.isfinite(v) for v in row) for row in rows)):
        raise ValueError("nonempty finite 3D saddle and nondegenerate source bounds required")
    xmin, xmax, zmin, zmax = limits
    mid = (xmin + xmax) / 2
    radius = (xmax - xmin) / 2
    height = zmax - zmin
    result = []
    for x, y, z in rows:
        if not (xmin - 1e-8 <= x <= xmax + 1e-8 and
                zmin - 1e-8 <= z <= zmax + 1e-8):
            raise ValueError("saddle vertex outside common 2026 source bounds")
        normalized_x = max(-1., min(1., (x - mid) / radius))
        x_weight = (1 - normalized_x * normalized_x) ** 2
        fraction_z = (z - zmin) / height
        upper = max(0., min(1., (fraction_z - 0.2) / 0.8))
        z_weight = upper * upper * (3 - 2 * upper)
        result.append((x, y, z + float(cup) * x_weight * z_weight))
    return tuple(result)


@contextmanager
def temporary_saddle_cup(scene, cup):
    """Edit only the two existing saddle geometry buffers, then restore exactly.

    Used *inside* the existing source root/wheel/saddle articulation contexts,
    never as a second asset, model, camera, rig or re-exported default.
    """
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS, CHILD_COUNTS

    _validate_cup(cup)
    if not isinstance(scene, trimesh.Scene) or scene.graph.base_frame != "world":
        raise ValueError("single source-owned five-parent 2026 GLB required")
    root = scene.graph.base_frame
    parent = scene.graph.transforms.parents.get("saddle")
    if (parent is None or
            (parent != root and scene.graph.transforms.parents.get(parent) != root) or
            any(scene.graph.transforms.parents.get(p) != parent for p in PARTS) or
            set(scene.graph.nodes_geometry) != {
                f"{part}__material_{i}" for part, count in CHILD_COUNTS.items()
                for i in range(count)}):
        raise ValueError("source five-parent/16-material topology changed")

    original_nodes = set(scene.graph.nodes)
    original_geometries = set(scene.geometry)
    original_parent_matrices = {
        p: np.asarray(scene.graph.get(p)[0]).copy() for p in PARTS
    }
    if any(matrix.shape != (4, 4) or not np.isfinite(matrix).all()
           for matrix in original_parent_matrices.values()):
        raise ValueError("invalid 2026 parent transforms")

    saved = {}
    for i in range(CHILD_COUNTS["saddle"]):
        node = f"saddle__material_{i}"
        transform, name = scene.graph.get(node)
        if (not np.allclose(transform, original_parent_matrices["saddle"],
                            atol=1e-8, rtol=0)
                or name in saved or name not in scene.geometry):
            raise ValueError("ambiguous original saddle source/material child")
        mesh = scene.geometry[name]
        points = np.asarray(mesh.vertices).copy()
        faces = np.asarray(mesh.faces).copy()
        colors = np.asarray(mesh.visual.vertex_colors).copy()
        if (points.ndim != 2 or points.shape[1] != 3 or not len(points)
                or not np.isfinite(points).all()):
            raise ValueError("invalid original saddle triangle vertices")
        saved[name] = (points, faces, colors)

    union = np.concatenate([parts[0] for parts in saved.values()])
    bounds = (float(union[:, 0].min()), float(union[:, 0].max()),
              float(union[:, 2].min()), float(union[:, 2].max()))
    if bounds[1] - bounds[0] <= 1e-9 or bounds[3] - bounds[2] <= 1e-9:
        raise ValueError("degenerate original saddle material union")
    try:
        for name, (points, _, _) in saved.items():
            scene.geometry[name].vertices = np.asarray(
                cup_vertices(points, cup, bounds), dtype=float
            )
        if (set(scene.graph.nodes) != original_nodes or
                set(scene.geometry) != original_geometries or
                any(not np.array_equal(scene.graph.get(part)[0], matrix)
                    for part, matrix in original_parent_matrices.items()) or
                any(not np.array_equal(scene.geometry[name].faces, faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors, colors)
                        for name, (_, faces, colors) in saved.items())):
            raise ValueError("saddle cup modified another source material or parent")
        yield
    finally:
        for name, (points, _, _) in saved.items():
            scene.geometry[name].vertices = points
        if (set(scene.graph.nodes) != original_nodes or
                set(scene.geometry) != original_geometries or
                any(not np.array_equal(scene.graph.get(part)[0], matrix)
                    for part, matrix in original_parent_matrices.items()) or
                any(not np.array_equal(scene.geometry[name].vertices, points) or
                        not np.array_equal(scene.geometry[name].faces, faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors, colors)
                        for name, (points, faces, colors) in saved.items())):
            raise ValueError("source-owned saddle mesh failed exact rollback")
