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

from tools.art.glb_roundtrip_guard import geometry_signature
from tools.art.collar_transition_review import BASELINE_SOURCE_SHA256, sculpt

PART_COUNTS = {"tire": 2, "rim_and_hub": 5, "fork_and_frame": 4,
               "pedals": 3, "saddle": 2}
EXPECTED = {f"{name}__material_{i}" for name,count in PART_COUNTS.items()
            for i in range(count)}


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
