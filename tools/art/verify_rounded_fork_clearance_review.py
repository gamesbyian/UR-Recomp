#!/usr/bin/env python3
"""Compare real straight-collar and rounded-fork GLBs, conservatively.

No assertion of original 1994 geometry, all-pose clearance, likeness, or
shipping-art acceptance. No duplicate source rig or scoring framework.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from tools.art.glb_roundtrip_guard import geometry_signature
from tools.art.rounded_fork_clearance_review import (
    STRAIGHT_SOURCE_SHA256, PROPOSED_SOURCE_SHA256, rounded_fork_source
)
from tools.art.verify_collar_transition_review import (
    EXPECTED, PART_COUNTS, lateral_reflection_error,
    silver_post_cross_section_centers,
)

BLUE_FRAME_NODE="fork_and_frame__material_0"


def tire_torus_clearance_samples(scene):
    """Sample actual blue-frame surface against source-owned circular tire.

    The 2026 tire is a torus of major radius 0.85 and tube radius 0.15
    around its Y-axis. This checks vertices, face centroids, all face-edge
    midpoints; it is NOT an exact continuous-Boolean intersection theorem.
    """
    tf, name=scene.graph.get(BLUE_FRAME_NODE)
    m=scene.geometry[name]
    p=np.asarray(m.vertices)
    faces=p[np.asarray(m.faces)]
    sampled=np.vstack((p,faces.mean(axis=1),
                       (faces[:,0]+faces[:,1])/2,
                       (faces[:,1]+faces[:,2])/2,
                       (faces[:,2]+faces[:,0])/2))
    from trimesh.transformations import transform_points
    world=transform_points(sampled,tf)
    wheel_tf, _=scene.graph.get("tire")
    # Tire part parent pivot is the original source wheel axle.
    wheel_xyz=wheel_tf[:3,3]
    relative=world-wheel_xyz
    axis_distance=np.hypot(relative[:,0],relative[:,2])
    signed=np.hypot(axis_distance-.85,relative[:,1])-.15
    return {"sample_count":int(len(signed)),
            "minimum_sampled_signed_clearance":float(signed.min()),
            "sampled_points_inside_tire_tube":int(np.count_nonzero(signed<0)),
            "continuous_surface_cleared":False,
            "all_poses_cleared":False}


def verify(baseline_source:Path, rounded_scad:Path, straight_glb:Path,
           rounded_glb:Path):
    source=rounded_fork_source(baseline_source.read_bytes())
    if rounded_scad.read_bytes()!=source:
        raise ValueError("rounded SCAD does not match source-locked proposal")
    originals=(straight_glb.read_bytes(),rounded_glb.read_bytes())
    scenes=[trimesh.load(path,force="scene",process=False)
            for path in (straight_glb,rounded_glb)]
    a,b=scenes
    for scene in scenes:
        if (not isinstance(scene,trimesh.Scene)
            or set(scene.geometry)!=EXPECTED
            or set(scene.graph.nodes_geometry)!=EXPECTED
            or scene.graph.base_frame!="world"):
            raise ValueError("unexpected GLB five-part material graph")
    changed=[]
    for name in sorted(EXPECTED):
        m1,m2=a.geometry[name],b.geometry[name]
        if (not m1.is_watertight or not m2.is_watertight
            or not np.array_equal(np.unique(m1.visual.vertex_colors,axis=0),
                                  np.unique(m2.visual.vertex_colors,axis=0))):
            raise ValueError("changed material identity / watertight source: "+name)
        if geometry_signature(m1)!=geometry_signature(m2):
            changed.append(name)
    if changed!=[BLUE_FRAME_NODE]:
        raise ValueError("rounded fork changed more than the blue fork material: "+repr(changed))
    for part in PART_COUNTS:
        if not np.array_equal(a.graph.get(part)[0],b.graph.get(part)[0]):
            raise ValueError("changed parent transformation: "+part)
    for label,scene in (("old",a),("rounded",b)):
        for part in ("fork_and_frame","saddle"):
            if lateral_reflection_error(scene,part)["max_nearest_vertex_error"]>1e-4:
                raise ValueError(label+" lost lateral symmetry in "+part)
        silver_post_cross_section_centers(scene)
    before=tire_torus_clearance_samples(a)
    after=tire_torus_clearance_samples(b)
    if before["minimum_sampled_signed_clearance"]>=-.003:
        raise ValueError("baseline fork/tire overlap control unexpectedly absent")
    if (after["sampled_points_inside_tire_tube"] or
        after["minimum_sampled_signed_clearance"]<=.005):
        raise ValueError("rounded fork did not clear sampled tire tube")
    return {"schema":"UR-ART4K-ROUNDED-FORK-REAL-GLB-REVIEW/1",
            "source_straight_scad_sha256":STRAIGHT_SOURCE_SHA256,
            "rounded_candidate_scad_sha256":PROPOSED_SOURCE_SHA256,
            "source_straight_glb_sha256":hashlib.sha256(originals[0]).hexdigest(),
            "rounded_glb_sha256":hashlib.sha256(originals[1]).hexdigest(),
            "only_changed_material_node":changed[0],
            "unchanged_other_material_nodes":15,
            "five_parent_transforms_unchanged":True,
            "saddle_and_frame_y_mirror_preserved":True,
            "straight_silver_post_retained":True,
            "existing_fork_sampled_tire_clearance":before,
            "rounded_fork_sampled_tire_clearance":after,
            "source_1994_mesh_recovered":False,
            "owner_likeness_approved":False,
            "shipping_art_approved":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ("baseline_scad","rounded_scad","straight_glb","rounded_glb","out"):
        ap.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    args=ap.parse_args()
    result=verify(args.baseline_scad,args.rounded_scad,args.straight_glb,args.rounded_glb)
    with args.out.open("x",encoding="utf8") as f:
        json.dump(result,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
