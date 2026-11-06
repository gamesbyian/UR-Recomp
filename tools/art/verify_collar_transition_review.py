#!/usr/bin/env python3
"""Independently compare real 2026 baseline/collar GLBs without art approval.

Uses canonical oriented-triangle fingerprints so harmless OpenSCAD triangulation
order changes are not mistaken for a changed physical part.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.glb_roundtrip_guard import geometry_signature
    from tools.art.collar_transition_review import BASELINE_SOURCE_SHA256, sculpt
except ModuleNotFoundError:
    from glb_roundtrip_guard import geometry_signature
    from collar_transition_review import BASELINE_SOURCE_SHA256, sculpt

PART_COUNTS = {"tire": 2, "rim_and_hub": 5, "fork_and_frame": 4,
               "pedals": 3, "saddle": 2}
EXPECTED = {f"{name}__material_{i}" for name,count in PART_COUNTS.items()
            for i in range(count)}



def lateral_reflection_error(scene, part: str) -> dict:
    """Real GLB world-space Y=0 mirror check, *excluding* opposing pedals.

    Surface-vertex nearest neighbours are an exact positive certificate for
    truly mirror-paired triangulations. A nonzero distance is an inspection
    warning, not an exact Hausdorff bound on continuous triangles.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    import trimesh

    if part not in PART_COUNTS or part == "pedals":
        raise ValueError("mirror audit applies to non-pedal 2026 parts only")
    positions = []
    for i in range(PART_COUNTS[part]):
        node = f"{part}__material_{i}"
        transform, mesh_name = scene.graph.get(node)
        vertices = trimesh.transform_points(scene.geometry[mesh_name].vertices, transform)
        if not np.isfinite(vertices).all():
            raise ValueError("nonfinite 2026 GLB mirror input")
        positions.append(vertices)
    points = np.concatenate(positions, axis=0)
    reflected = points.copy()
    reflected[:, 1] *= -1
    errors, _ = cKDTree(points).query(reflected, k=1)
    return {"sampled_world_vertices": int(len(points)),
            "max_nearest_vertex_error": float(np.max(errors)),
            "p99_nearest_vertex_error": float(np.percentile(errors, 99)),
            "fraction_error_over_0p04": float(np.mean(errors > .04)),
            "exact_surface_mirror_recovered_1994": False}



def silver_post_cross_section_centers(candidate_scene):
    """Prove upright 3D metal post is straight from blue collar, after export.

    Independently section the actual silver material mesh at two heights.
    The section's signed polygon AREA CENTROID, not a source-text coordinate,
    must lie on the shared coloured-collar X/Y axis. The previous candidate
    drifts measurably between the slices and is a negative test.
    """
    import numpy as np
    node = "fork_and_frame__material_1"
    geometry = candidate_scene.geometry[node]
    if not geometry.is_watertight:
        raise ValueError("silver post surface is not watertight")
    centers = []
    for height in (1.90, 2.10):
        cross = geometry.section(
            plane_origin=[0, 0, height], plane_normal=[0, 0, 1])
        if cross is None or len(cross.discrete) != 1:
            raise ValueError("one exposed silver post cross-section required")
        ring = np.asarray(cross.discrete[0], dtype=float)
        if (ring.ndim != 2 or ring.shape[1] != 3 or len(ring) < 5
                or not np.isfinite(ring).all()
                or not np.allclose(ring[0], ring[-1], rtol=0, atol=1e-7)):
            raise ValueError("invalid closed cross-section of 2026 silver post")
        x, y = ring[:,0], ring[:,1]
        signed = x[:-1] * y[1:] - x[1:] * y[:-1]
        area6 = 3 * signed.sum()
        if abs(area6) < 1e-8:
            raise ValueError("degenerate silver post cross-section")
        center = [float(np.sum((x[:-1] + x[1:]) * signed) / area6),
                  float(np.sum((y[:-1] + y[1:]) * signed) / area6)]
        if not np.allclose(center, [-.22, 0], atol=.001, rtol=0):
            raise ValueError("actual exported silver seatpost is angled or off-centre")
        centers.append(center)
    if not np.allclose(centers[0], centers[1], atol=.001, rtol=0):
        raise ValueError("actual exported silver rod is not straight between heights")
    return {"source_heights": [1.90, 2.10],
            "xy_centerline_at_each_height": centers,
            "strict_coaxial_tolerance_source_units": .001,
            "source_1994_camera_or_rod_geometry_recovered": False}


def inspect(base_glb: Path, candidate_glb: Path, baseline_scad: Path,
            candidate_scad: Path) -> dict:
    import numpy as np
    import trimesh

    expected_bytes = sculpt(baseline_scad.read_bytes())
    if candidate_scad.read_bytes() != expected_bytes:
        raise ValueError("candidate SCAD does not match source-locked collar sculpt")
    originals = (base_glb.read_bytes(), candidate_glb.read_bytes())
    if originals[0] == originals[1]:
        raise ValueError("collar did not alter the actual serialized GLB")
    scenes = [trimesh.load(path, force="scene", process=False)
              for path in (base_glb, candidate_glb)]
    for scene in scenes:
        if (not isinstance(scene, trimesh.Scene) or
                scene.graph.base_frame != "world" or
                set(scene.geometry) != EXPECTED or
                set(scene.graph.nodes_geometry) != EXPECTED):
            raise ValueError("not canonical five-parent sixteen-material GLB")
    a,b=scenes
    changed=[]
    for node in sorted(EXPECTED):
        m,n=a.geometry[node],b.geometry[node]
        if (not np.array_equal(np.unique(m.visual.vertex_colors,axis=0),
                               np.unique(n.visual.vertex_colors,axis=0))
                or not m.is_watertight or not n.is_watertight):
            raise ValueError("material identity or part watertightness changed: "+node)
        for scene in scenes:
            if scene.graph.transforms.parents.get(node) != node.split("__material_")[0]:
                raise ValueError("material child was detached from parent: "+node)
        if geometry_signature(m)!=geometry_signature(n):
            changed.append(node)
    if not changed or any(not node.startswith("fork_and_frame__") for node in changed):
        raise ValueError("changed geometry must be confined to existing frame/collar")
    if "fork_and_frame__material_0" not in changed:
        raise ValueError("coloured collar was not actually changed")
    for part in PART_COUNTS:
        if not np.array_equal(a.graph.get(part)[0],b.graph.get(part)[0]):
            raise ValueError("source-authored part pivot changed: "+part)
    silver_post_sections = silver_post_cross_section_centers(b)
    # The owner explicitly expects a laterally symmetric coloured frame/seat.
    # Pedals are intentionally opposite, and tire/rim asymmetry remains a
    # nonblocking documented design question rather than an invented fix.
    symmetry = {label: {part: lateral_reflection_error(scene, part)
                        for part in ("fork_and_frame", "saddle", "tire", "rim_and_hub")}
                for label,scene in (("baseline",a),("candidate",b))}
    for label in ("baseline","candidate"):
        for part in ("fork_and_frame","saddle"):
            if symmetry[label][part]["max_nearest_vertex_error"] > 1e-4:
                raise ValueError(f"{label} {part} violates owner front-view Y mirror")
    return {
        "schema":"UR-ART4K-OWNER-COLLAR-REAL-GLB/1",
        "baseline_scad_sha256":BASELINE_SOURCE_SHA256,
        "candidate_scad_sha256":hashlib.sha256(expected_bytes).hexdigest(),
        "baseline_glb_sha256":hashlib.sha256(originals[0]).hexdigest(),
        "candidate_glb_sha256":hashlib.sha256(originals[1]).hexdigest(),
        "part_parent_transforms_unchanged":True,
        "source_material_roles_unchanged":True,
        "unchanged_nonframe_material_nodes":12,
        "changed_frame_material_nodes":changed,
        "actual_exported_silver_post_sections":silver_post_sections,
        "lateral_y_mirror_vertex_audit":symmetry,
        "saddle_and_coloured_frame_y_mirror_certified":True,
        "wheel_rim_mirror_deviations_are_unreviewed":True,
        "source_1994_3d_geometry_recovered":False,
        "source_sprite_pose_registration_verified":False,
        "owner_approved":False,
        "shipping_art_approved":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-glb",type=Path,required=True)
    parser.add_argument("--candidate-glb",type=Path,required=True)
    parser.add_argument("--baseline-scad",type=Path,required=True)
    parser.add_argument("--candidate-scad",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    report=inspect(args.baseline_glb,args.candidate_glb,
                   args.baseline_scad,args.candidate_scad)
    with args.out.open("x",encoding="utf-8") as target:
        json.dump(report,target,sort_keys=True,indent=2)
        target.write("\n")
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
