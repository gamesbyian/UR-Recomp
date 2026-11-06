#!/usr/bin/env python3
"""Optional 2026 rounded fork/collar and tire-clearance study on ONE source rig.

Applies only to the established *straight-seatpost* review geometry, never
the default 2026 SCAD, source 1994 models, ROM, gameplay or approved art.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.collar_transition_review import sculpt, assert_seatpost_aligned
except ModuleNotFoundError:
    from collar_transition_review import sculpt, assert_seatpost_aligned

STRAIGHT_SOURCE_SHA256 = "8bd8571efadf2bc8da0f1690bda99ac1f2f5a50bea00535ac57598401eaa0f9d"
PROPOSED_SOURCE_SHA256 = "f59f45679ef51fea3371a087ddf4cf3bde589554d1c57e5a3c62d2395d45f2be"
OLD_LOOP = "for(y=[-0.225,0.225])"
NEW_LOOP = "for(y=[-0.28,0.28])"
OLD_SHOULDER = "color(rig_color)frame_member([-0.10,y,0.83],[-0.17,y*0.63,1.42],0.105,0.14);"
NEW_SHOULDER = "color(rig_color)frame_member([-0.10,y,0.83],[-0.17,y*0.50,1.42],0.105,0.16);"


def rounded_fork_source(baseline: bytes) -> bytes:
    """Fail closed on changes to the single canonical rig or joined seatpost."""
    source = sculpt(baseline).decode("utf-8")
    if hashlib.sha256(source.encode()).hexdigest() != STRAIGHT_SOURCE_SHA256:
        raise ValueError("original straight-seatpost variant has drifted")
    if source.count(OLD_LOOP) != 1 or source.count(OLD_SHOULDER) != 1:
        raise ValueError("unexpected original twin-fork geometry")
    result = source.replace(OLD_LOOP,NEW_LOOP).replace(OLD_SHOULDER,NEW_SHOULDER)
    assert_seatpost_aligned(result)
    if hashlib.sha256(result.encode()).hexdigest() != PROPOSED_SOURCE_SHA256:
        raise ValueError("rounded fork proposal differs from the reviewed physical geometry")
    return result.encode()


def make_candidate(baseline: Path, output: Path) -> dict:
    if baseline.resolve()==output.resolve():
        raise ValueError("cannot replace the canonical 2026 authoring source")
    data=rounded_fork_source(baseline.read_bytes())
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as stream:
        stream.write(data)
    return {"schema":"UR-ART4K-ROUNDED-FORK-REVIEW/1",
            "derived_from_sha256":STRAIGHT_SOURCE_SHA256,
            "candidate_scad_sha256":PROPOSED_SOURCE_SHA256,
            "front_plane_y_mirror_by_source":True,
            "metal_post_aligned":True,
            "unchanged_saddle_wheel_spokes_pedals":True,
            "original_1994_mesh_recovered":False,
            "owner_likeness_approved":False,
            "output":str(output)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_scad",type=Path)
    parser.add_argument("new_candidate_scad",type=Path)
    args=parser.parse_args()
    print(json.dumps(make_candidate(args.baseline_scad,args.new_candidate_scad),
                     sort_keys=True,indent=2))

if __name__=="__main__":
    main()
