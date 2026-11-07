#!/usr/bin/env python3
"""Independent real-GLB proof for the optional rotating 2026 through-axle.

Must compare two real upright, source-pinned five-part/sixteen-material GLBs.
A silver drive shaft moves from fixed fork to rotating crank; the source
fixed grey sleeve and blue fork gain explicit bores with a radial air gap.
This demonstrates source-2026 mesh clearance, not 1994 original design,
a Boolean-fused drive/hub key, or suitability for shipping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

try:
    from tools.art.rotating_axle_bearing_review import (
        rotating_axle_source, ROTATING_AXLE_SOURCE_SHA256, SHAFT_RADIUS,
        BORE_RADIUS, MIN_CLEARANCE,
    )
    from tools.art.mirrored_outboard_tread_review import (
        mirrored_tread_source, MIRRORED_OUTBOARD_SOURCE_SHA256,
    )
    from tools.art.glb_roundtrip_guard import geometry_signature
    from tools.art.verify_collar_transition_review import EXPECTED, PART_COUNTS
except ModuleNotFoundError:
    from rotating_axle_bearing_review import (
        rotating_axle_source, ROTATING_AXLE_SOURCE_SHA256, SHAFT_RADIUS,
        BORE_RADIUS, MIN_CLEARANCE,
    )
    from mirrored_outboard_tread_review import (
        mirrored_tread_source, MIRRORED_OUTBOARD_SOURCE_SHA256,
    )
    from glb_roundtrip_guard import geometry_signature
    from verify_collar_transition_review import EXPECTED, PART_COUNTS

FORK = "fork_and_frame__material_0"
SLEEVE = "fork_and_frame__material_3"
CRANK = "pedals__material_0"
CHANGED = frozenset((FORK, SLEEVE, CRANK))
# Blue lower fork and central sleeve must remain outside the rotating shaft
# radius. A conservative triangle-surface radial gap of 0.0005 is mandatory.
MIN_ACTUAL_GLB_TRIANGLE_GAP = 0.0005


def projected_triangle_origin_radius(vertices, faces):
    """Minimum XZ origin distance over *all* real triangles, not just vertices.

    Shaft spans entire actual fixed fork Y extent. Projecting each triangle
    on XZ and finding its closest point is conservative: it may flag triangles
    at different Y values but cannot miss a surface reaching the axle radius.
    Degenerate projected edges are explicitly supported; nonfinite surfaces
    are rejected.
    """
    points = np.asarray(vertices, dtype=np.float64)
    triangles = np.asarray(faces, dtype=np.int64)
    if (points.ndim != 2 or points.shape[1] != 3 or len(points) == 0
            or not np.isfinite(points).all() or triangles.ndim != 2
            or triangles.shape[1] != 3 or not len(triangles)
            or triangles.min() < 0 or triangles.max() >= len(points)):
        raise ValueError("actual source-owned finite indexed triangles required")
    xy = points[triangles][:, :, (0, 2)]
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    def cross(u, v):
        return u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    signed = np.stack((
        cross(b - a, -a),
        cross(c - b, -b),
        cross(a - c, -c),
    ), axis=1)
    contains_origin = ((signed >= -1e-12).all(axis=1)
                       | (signed <= 1e-12).all(axis=1))
    min_squared = np.full(len(triangles), np.inf, dtype=np.float64)
    for start, finish in ((a, b), (b, c), (c, a)):
        edge = finish - start
        denominator = (edge * edge).sum(axis=1)
        fraction = np.clip(np.divide(
            -(start * edge).sum(axis=1),
            denominator, out=np.zeros_like(denominator),
            where=denominator > 0), 0, 1)
        nearest = start + fraction[:, None] * edge
        min_squared = np.minimum(min_squared, (nearest * nearest).sum(axis=1))
    min_squared[contains_origin] = 0
    return float(np.sqrt(min_squared.min()))


def verify(canonical_source: Path, owner_source: Path, candidate_source: Path,
           owner_glb: Path, candidate_glb: Path) -> dict:
    original = canonical_source.read_bytes()
    expected_owner = mirrored_tread_source(original)
    if (owner_source.read_bytes() != expected_owner
            or hashlib.sha256(expected_owner).hexdigest()
                != MIRRORED_OUTBOARD_SOURCE_SHA256
            or candidate_source.read_bytes() != rotating_axle_source(original)):
        raise ValueError("source is not the exact owner-judged optional geometry")
    glb_bytes = (owner_glb.read_bytes(), candidate_glb.read_bytes())
    scenes = [trimesh.load(p, file_type="glb", force="scene", process=False)
              for p in (owner_glb, candidate_glb)]
    for scene in scenes:
        if (not isinstance(scene, trimesh.Scene) or scene.graph.base_frame != "world"
                or set(scene.geometry) != EXPECTED or
                set(scene.graph.nodes_geometry) != EXPECTED):
            raise ValueError("actual source GLBs must retain the five-part sixteen-material rig")
    owner, revised = scenes
    changed = set()
    for name in sorted(EXPECTED):
        one, two = owner.geometry[name], revised.geometry[name]
        if (not one.is_watertight or not two.is_watertight
                or not np.array_equal(np.unique(one.visual.vertex_colors, axis=0),
                                      np.unique(two.visual.vertex_colors, axis=0))):
            raise ValueError("authored material paint or triangle closure changed: " + name)
        for scene in scenes:
            if scene.graph.transforms.parents.get(name) != name.split("__")[0]:
                raise ValueError("material lost its source parent: " + name)
        if not np.array_equal(owner.graph.get(name)[0], revised.graph.get(name)[0]):
            raise ValueError("source material transform changed: " + name)
        if geometry_signature(one) != geometry_signature(two):
            changed.add(name)
    if changed != CHANGED:
        raise ValueError("only fixed fork, sleeve, and rotating crank may change: "+repr(changed))
    for parent in PART_COUNTS:
        if not np.array_equal(owner.graph.get(parent)[0], revised.graph.get(parent)[0]):
            raise ValueError("global five source part pivots changed: " + parent)
    if not 0.005 < MIN_CLEARANCE < 0.007:
        raise ValueError("source bored bearing gap incorrectly configured")
    old_fork_radial = projected_triangle_origin_radius(
        owner.geometry[FORK].vertices, owner.geometry[FORK].faces)
    old_sleeve_radial = projected_triangle_origin_radius(
        owner.geometry[SLEEVE].vertices, owner.geometry[SLEEVE].faces)
    radial = {}
    for name in (FORK, SLEEVE):
        g = revised.geometry[name]
        radius = projected_triangle_origin_radius(g.vertices, g.faces)
        radial[name] = {"minimum_all_triangle_XZ_origin_radius": radius,
                        "minimum_gap_to_rotating_shaft_radius": radius - SHAFT_RADIUS,
                        "certified_triangle_surface_excludes_axle_envelope":
                            radius >= SHAFT_RADIUS + MIN_ACTUAL_GLB_TRIANGLE_GAP}
        if not radial[name]["certified_triangle_surface_excludes_axle_envelope"]:
            raise ValueError("real fixed-fork material intersects rotating shaft: " + name)
    if old_fork_radial >= SHAFT_RADIUS or old_sleeve_radial >= SHAFT_RADIUS:
        raise ValueError("historical intersecting stationary candidate control missing")
    crank = revised.geometry[CRANK]
    p = np.asarray(crank.vertices)
    central = p[np.linalg.norm(p[:, (0, 2)], axis=1) < SHAFT_RADIUS + .002]
    if len(central) < 10 or np.min(central[:, 1]) > -.5 or np.max(central[:, 1]) < .5:
        raise ValueError("new rotating pedal parent missing connected-through-shaft vertices")
    return {
        "schema": "UR-ART4K-OWNER-ROTATING-AXLE-BEARING-REAL-GLB/1",
        "owner_mirrored_source_sha256": MIRRORED_OUTBOARD_SOURCE_SHA256,
        "rotating_bored_source_sha256": ROTATING_AXLE_SOURCE_SHA256,
        "owner_candidate_glb_sha256": hashlib.sha256(glb_bytes[0]).hexdigest(),
        "rotating_candidate_glb_sha256": hashlib.sha256(glb_bytes[1]).hexdigest(),
        "changed_materials": sorted(changed),
        "other_thirteen_materials_and_all_five_parent_pivots_preserved": True,
        "old_fixed_fork_radial_minimum": old_fork_radial,
        "old_fixed_sleeve_radial_minimum": old_sleeve_radial,
        "shaft_radius": SHAFT_RADIUS,
        "bore_radius_source": BORE_RADIUS,
        "minimum_ideal_bore_clearance": MIN_CLEARANCE,
        "minimum_required_real_GLb_triangle_surface_gap": MIN_ACTUAL_GLB_TRIANGLE_GAP,
        "source_real_fork_and_bearing_radial_clearance": radial,
        "rotating_axle_parent": "pedals",
        "stationary_bearing_parent": "fork_and_frame",
        "rotating_axle_and_crank_independently_boolean_fused": False,
        "wheel_and_crank_rotation_phase_mechanically_coupled": False,
        "original_1994_bearing_mechanics_recovered": False,
        "shipping_art_approved": False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("canonical_source","owner_source","candidate_source",
                 "owner_glb","candidate_glb","out"):
        parser.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.canonical_source,args.owner_source,args.candidate_source,
                  args.owner_glb,args.candidate_glb)
    with args.out.open("x",encoding="utf-8") as file:
        json.dump(result,file,sort_keys=True,indent=2)
        file.write("\n")
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
