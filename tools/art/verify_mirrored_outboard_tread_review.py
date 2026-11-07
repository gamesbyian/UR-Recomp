#!/usr/bin/env python3
"""Independent real-GLB audit of owner-selected mirrored orange pedal markings.

Original 2026 canonical GLB and old qualified 2026 outboard candidate stay
unchanged. Only the tread material is allowed to differ; all other fifteen
source material meshes, their colors and five part pivots must be identical.
The Y-opposed orange tread vertices must be centrally symmetric around the
axle in the *local pedal material frame*. No visual release approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

try:
    from tools.art.glb_roundtrip_guard import geometry_signature
    from tools.art.verify_collar_transition_review import EXPECTED, PART_COUNTS
    from tools.art.mirrored_outboard_tread_review import (
        MIRRORED_OUTBOARD_SOURCE_SHA256,mirrored_tread_source,
    )
    from tools.art.pedal_axle_clearance_review import OUTBOARD_SOURCE_SHA256
except ModuleNotFoundError:
    from glb_roundtrip_guard import geometry_signature
    from verify_collar_transition_review import EXPECTED, PART_COUNTS
    from mirrored_outboard_tread_review import (
        MIRRORED_OUTBOARD_SOURCE_SHA256,mirrored_tread_source,
    )
    from pedal_axle_clearance_review import OUTBOARD_SOURCE_SHA256

TREAD = "pedals__material_2"


def bilateral_tread_report(scene) -> dict:
    """Compare entire +/-Y actual GLB vertex clouds after central inversion.

    Local pedal frame is axle-centered; full (X,Y,Z) inversion includes the
    180-degree opposing crank phase. Nearest *vertex* distances are measured;
    do not claim watertight whole-surface coincidence from this alone.
    """
    points = np.asarray(scene.geometry[TREAD].vertices,dtype=np.float64)
    faces = np.asarray(scene.geometry[TREAD].faces,dtype=np.int64)
    if (points.ndim != 2 or points.shape[1:] != (3,)
            or not np.isfinite(points).all() or not len(faces)
            or (np.abs(points[:,1]) <= .1).any()):
        raise ValueError("real GLB tread has invalid or axle crossing vertices")
    sign = np.sign(points[:,1])
    if (faces.min() < 0 or faces.max() >= len(points)
            or (sign[faces] != sign[faces[:,0]][:,None]).any()):
        raise ValueError("tread material crosses axle")
    a,b=points[sign>0],points[sign<0]
    if len(a)!=len(b) or len(a)<8:
        raise ValueError("two opposite 2026 tread pieces required")
    distances=cKDTree(b).query(-a)[0]
    reverse=cKDTree(-a).query(b)[0]
    return {
        "positive_tread_vertices": len(a),
        "negative_tread_vertices": len(b),
        "maximum_opposed_inverse_vertex_error":
            float(max(distances.max(),reverse.max())),
        "mean_opposed_inverse_vertex_error":
            float((distances.mean()+reverse.mean())/2),
        "continuous_surface_equality_proved": False,
    }


def verify(canonical_source:Path,old_source:Path,mirrored_source:Path,
           old_glb:Path,mirrored_glb:Path)->dict:
    raw=canonical_source.read_bytes()
    if (hashlib.sha256(old_source.read_bytes()).hexdigest()
            !=OUTBOARD_SOURCE_SHA256
            or mirrored_source.read_bytes()!=mirrored_tread_source(raw)
            or hashlib.sha256(mirrored_source.read_bytes()).hexdigest()
            !=MIRRORED_OUTBOARD_SOURCE_SHA256):
        raise ValueError("source candidate is not exact owner-selected revision")
    a,b=(trimesh.load(p,force="scene",process=False)
         for p in (old_glb,mirrored_glb))
    for scene in (a,b):
        if (not isinstance(scene,trimesh.Scene) or
                scene.graph.base_frame!="world" or
                set(scene.geometry)!=EXPECTED or
                set(scene.graph.nodes_geometry)!=EXPECTED):
            raise ValueError("incorrect full 2026 five-part sixteen-material GLB")
    changed=[]
    for name in sorted(EXPECTED):
        before,after=a.geometry[name],b.geometry[name]
        if (not before.is_watertight or not after.is_watertight or
                not np.array_equal(np.unique(before.visual.vertex_colors,axis=0),
                                   np.unique(after.visual.vertex_colors,axis=0))):
            raise ValueError("source material color or closed surface changed: "+name)
        for scene in (a,b):
            if scene.graph.transforms.parents.get(name)!=name.split("__")[0]:
                raise ValueError("material parent changed: "+name)
            if not np.array_equal(a.graph.get(name)[0],b.graph.get(name)[0]):
                raise ValueError("material transform changed: "+name)
        if geometry_signature(before)!=geometry_signature(after):
            changed.append(name)
    if changed!=[TREAD]:
        raise ValueError("only orange tread geometry may differ, got "+str(changed))
    for part in PART_COUNTS:
        if not np.array_equal(a.graph.get(part)[0],b.graph.get(part)[0]):
            raise ValueError("2026 parent pivot changed: "+part)
    old=bilateral_tread_report(a)
    revised=bilateral_tread_report(b)
    if (old["maximum_opposed_inverse_vertex_error"] <= .20 or
            revised["maximum_opposed_inverse_vertex_error"] >= 1e-4):
        raise ValueError("owner tread-mirror repair not demonstrated on GLB")
    return {
        "schema":"UR-ART4K-OWNER-MIRRORED-OUTBOARD-TREAD-REAL-GLB/1",
        "old_outboard_scad_sha256":OUTBOARD_SOURCE_SHA256,
        "owner_mirrored_scad_sha256":MIRRORED_OUTBOARD_SOURCE_SHA256,
        "old_outboard_glb_sha256":hashlib.sha256(old_glb.read_bytes()).hexdigest(),
        "owner_mirrored_glb_sha256":hashlib.sha256(mirrored_glb.read_bytes()).hexdigest(),
        "sole_changed_material":TREAD,
        "other_fifteen_materials_geometry_colors_and_transforms_preserved":True,
        "all_five_part_pivots_preserved":True,
        "original_tread_opposed_error":old,
        "owner_mirrored_tread_opposed_error":revised,
        "owner_preferred_wider_mechanical_candidate_retained":True,
        "owner_requested_tread_mirroring_satisfied":True,
        "original_1994_motion_geometry_or_likeness_proved":False,
        "shipping_art_approved":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("canonical_source","old_source","mirrored_source",
                 "old_glb","mirrored_glb","out"):
        ap.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    args=ap.parse_args()
    report=verify(args.canonical_source,args.old_source,args.mirrored_source,
                  args.old_glb,args.mirrored_glb)
    with args.out.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
