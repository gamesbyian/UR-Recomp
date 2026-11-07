#!/usr/bin/env python3
"""Real-GLB audit of optional outboard crank/axle repair, no art approval.

Require exactly four changed source material nodes; 12 other material meshes,
color identities and five part pivots stay untouched. Prove whole-volume
clearance against the original 2026 BLUE FORK for every crank angle, using
its actual GLB vertex Y extent and source-owned parametric envelopes.
Axle/crank attachment is deliberate contact, not yet CSG-qualified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

try:
    from tools.art.glb_roundtrip_guard import geometry_signature
    from tools.art.rounded_fork_clearance_review import REPAIRED_SOURCE_SHA256
    from tools.art.pedal_axle_clearance_review import (
        OUTBOARD_SOURCE_SHA256, continuous_clearance_bounds,
        outboard_pedal_source,
    )
    from tools.art.fork_tire_surface_certificate import certify_upright_review_fork
    from tools.art.verify_collar_transition_review import (
        EXPECTED, PART_COUNTS, lateral_reflection_error,
        silver_post_cross_section_centers,
    )
except ModuleNotFoundError:
    from glb_roundtrip_guard import geometry_signature
    from rounded_fork_clearance_review import REPAIRED_SOURCE_SHA256
    from pedal_axle_clearance_review import (
        OUTBOARD_SOURCE_SHA256, continuous_clearance_bounds,
        outboard_pedal_source,
    )
    from fork_tire_surface_certificate import certify_upright_review_fork
    from verify_collar_transition_review import (
        EXPECTED, PART_COUNTS, lateral_reflection_error,
        silver_post_cross_section_centers,
    )

BLUE = "fork_and_frame__material_0"
CHANGED = frozenset({
    "fork_and_frame__material_3",
    "pedals__material_0", "pedals__material_1", "pedals__material_2",
})


def pedal_body_fork_vertex_probe(fork_vertices, center_y, *, step_degrees=5):
    """Discriminator from real fork vertices into authored rounded boxes.

    Signed negative means an actual fork-surface GLB vertex is inside the
    source 2026 Minkowski cube+sphere pedal body. It says nothing about all
    surfaces if nonnegative; that job belongs to the Y-volume certificate.
    """
    if step_degrees < 1 or 360 % step_degrees:
        raise ValueError("phase increment must divide 360")
    vertices = np.asarray(fork_vertices, dtype=float)
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices)
            or not np.isfinite(vertices).all()):
        raise ValueError("finite world fork vertices required")
    best = (float("inf"), None, None, None)
    for angle in range(0, 360, step_degrees):
        radians = np.deg2rad(angle)
        for side in (-1, 1):
            center = np.array([side * .31 * np.cos(radians),
                               side * center_y,
                               1 + side * .31 * np.sin(radians)])
            q = np.abs(vertices - center) - np.array([.195, .085, .0575])
            # Exact SDF of axis-aligned cube Minkowski-summed with r=.036.
            signed = (np.linalg.norm(np.maximum(q, 0), axis=1)
                      + np.minimum(q.max(axis=1), 0) - .036)
            idx = int(signed.argmin())
            if signed[idx] < best[0]:
                best = (float(signed[idx]), angle, side, idx)
    return {
        "phase_step_degrees": step_degrees,
        "minimum_source_rounded_body_signed_distance_at_actual_fork_vertex": best[0],
        "worst_source_phase_degrees": best[1],
        "worst_opposing_pedal_side": best[2],
        "actual_fork_vertex_index": best[3],
        "full_continuous_surface_clearance_proved_by_this_sample": False,
    }


def verify(canonical_source: Path, repaired_source: Path,
           baseline_rounded_glb: Path, candidate_glb: Path) -> dict:
    expected = outboard_pedal_source(canonical_source.read_bytes())
    if repaired_source.read_bytes() != expected:
        raise ValueError("pedal/axle source does not match exact source patch")
    raw = (baseline_rounded_glb.read_bytes(), candidate_glb.read_bytes())
    scenes = [trimesh.load(p, force="scene", process=False)
              for p in (baseline_rounded_glb, candidate_glb)]
    for scene in scenes:
        if (not isinstance(scene, trimesh.Scene)
                or scene.graph.base_frame != "world"
                or set(scene.geometry) != EXPECTED
                or set(scene.graph.nodes_geometry) != EXPECTED):
            raise ValueError("missing canonical five-parent sixteen-material scene")
    before, after = scenes
    changed = set()
    for node in sorted(EXPECTED):
        one, two = before.geometry[node], after.geometry[node]
        if (not one.is_watertight or not two.is_watertight
                or not np.array_equal(
                    np.unique(one.visual.vertex_colors, axis=0),
                    np.unique(two.visual.vertex_colors, axis=0))):
            raise ValueError("material identity or closed surface changed: " + node)
        for scene in scenes:
            if scene.graph.transforms.parents.get(node) != node.split("__")[0]:
                raise ValueError("source material parent changed: " + node)
        if geometry_signature(one) != geometry_signature(two):
            changed.add(node)
    if changed != CHANGED:
        raise ValueError("wrong changed material set: " + repr(sorted(changed)))
    for parent in PART_COUNTS:
        if not np.array_equal(before.graph.get(parent)[0],
                              after.graph.get(parent)[0]):
            raise ValueError("source part transform changed: " + parent)
    for label, scene in (("baseline", before), ("candidate", after)):
        for part in ("saddle", "fork_and_frame"):
            if lateral_reflection_error(scene, part)[
                    "max_nearest_vertex_error"] > 1e-4:
                raise ValueError(label + " lost source lateral symmetry in " + part)
        silver_post_cross_section_centers(scene)
    tube = certify_upright_review_fork(after)
    if tube["status"] != "certified":
        raise ValueError("source fork lost its whole-triangle ideal tire clearance")
    transform, geom_name = after.graph.get(BLUE)
    vertices = trimesh.transform_points(after.geometry[geom_name].vertices, transform)
    max_y = float(np.abs(vertices[:, 1]).max())
    bounds = continuous_clearance_bounds(max_y)
    if (bounds["continuous_fork_vs_all_pedal_material_y_gap_lower_bound"] < .01
            or bounds["continuous_tire_radial_gap_lower_bound"] < .1
            or bounds["continuous_nearside_stripe_radial_gap_lower_bound"] < .1
            or bounds["continuous_outer_rim_radial_gap_lower_bound"] < .05
            or bounds["continuous_inner_rim_radial_gap_lower_bound"] < .02
            or not bounds["symmetric_crank_base_overlaps_axle_extension"]):
        raise ValueError("outboard candidate does not preserve intended margins")
    original = pedal_body_fork_vertex_probe(vertices, center_y=.39)
    improved = pedal_body_fork_vertex_probe(vertices, center_y=.56)
    if (original["minimum_source_rounded_body_signed_distance_at_actual_fork_vertex"] >= -.01
            or improved["minimum_source_rounded_body_signed_distance_at_actual_fork_vertex"] <= .01):
        raise ValueError("actual GLB vertex collision regression controls failed")
    return {
        "schema": "UR-ART4K-OUTBOARD-PEDAL-AXLE-REAL-GLB/1",
        "historical_rounded_scad_sha256": REPAIRED_SOURCE_SHA256,
        "candidate_scad_sha256": OUTBOARD_SOURCE_SHA256,
        "historical_rounded_glb_sha256": hashlib.sha256(raw[0]).hexdigest(),
        "candidate_glb_sha256": hashlib.sha256(raw[1]).hexdigest(),
        "changed_material_nodes": sorted(changed),
        "unchanged_material_nodes": 12,
        "all_five_parent_pivots_identical": True,
        "saddle_frame_mirror_and_silver_post_preserved": True,
        "preexisting_fork_ideal_torus_certificate_preserved": True,
        "whole_rotation_authored_source_volume_clearance": bounds,
        "historical_actual_fork_vertex_body_overlap_probe": original,
        "outboard_actual_fork_vertex_body_overlap_probe": improved,
        "through_axle_is_intended_mating_not_boolean_joint_certification": True,
        "independent_animated_pedal_meshes_per_phase_exported": False,
        "source_1994_mechanics_or_appearance_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("canonical_source", "candidate_source", "baseline_rounded_glb",
                 "candidate_glb", "out"):
        ap.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    a = ap.parse_args()
    report = verify(a.canonical_source, a.candidate_source,
                    a.baseline_rounded_glb, a.candidate_glb)
    with a.out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
