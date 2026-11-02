#!/usr/bin/env python3
"""Source-pinned, nonshipping wheel/crank phase correction for the ONE 2026 rig.

The authored GLBs bake pedal phase but leave the eight-spoke wheel stationary.
Move the tire and rim *parents* about the posed axle, preserving all 16 meshes.
Neither original-game source pose, camera nor animation timing is recovered.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

SOURCE_GLBS = {
    "upright": "efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5",
    "pedal": "f692277bb9bf215ccc97bc89f44d28378a43ddc9aa45843c4f0ab30e8747db53",
    "wheelie": "859b985d8fc51f994e5e42fd64bc871d493249285454ec833f33c27",
    "stunt": "d3375cf4d44d973ca7b4308bfff5b3646087a37d206a2746792c8083483f3212",
    "bank": "50d56b4f702ad655929c17e5cbc4e281386cf6b2fb2cd80e71d0a2e6b672fd59",
}
# Exact pose-specific shared_rig pedal arguments from the original source.
SOURCE_PHASE = {"upright":18.0,"pedal":88.0,"wheelie":44.0,"stunt":120.0,"bank":150.0}
PARTS = ("tire","rim_and_hub","fork_and_frame","pedals","saddle")
MOVING = ("tire","rim_and_hub")
STATIONARY = ("fork_and_frame","pedals","saddle")
CHILD_COUNTS = {"tire":2,"rim_and_hub":5,"fork_and_frame":4,"pedals":3,"saddle":2}
SCHEMA = "UR-ART4K-SOURCE-LOCKED-DIRECT-DRIVE-WHEEL-PHASE/1"


def delta_for_pose(pose):
    if type(pose) is not str or pose not in SOURCE_PHASE:
        raise ValueError("unknown source-owned named pose")
    return SOURCE_PHASE[pose]-18.0


def rotation(delta):
    """Row-major source Z-up OpenSCAD rotate([0,-delta,0])."""
    if (type(delta) not in (int,float) or not math.isfinite(delta)
            or not -720 <= delta <= 720):
        raise ValueError("finite bounded wheel phase required")
    c,s=math.cos(math.radians(delta)),math.sin(math.radians(delta))
    return ((c,0.,-s,0.),(0.,1.,0.,0.),(s,0.,c,0.),(0.,0.,0.,1.))


def synchronize(scene, delta):
    import numpy as np
    import trimesh
    r=np.asarray(rotation(delta),dtype=float)
    if not isinstance(scene,trimesh.Scene) or not set(PARTS).issubset(scene.graph.nodes):
        raise ValueError("missing canonical five source parts")
    original_nodes,original_geometry=set(scene.graph.nodes),set(scene.geometry)
    if len(scene.graph.nodes_geometry)!=16:
        raise ValueError("requires sixteen source-owned material meshes")
    root=scene.graph.base_frame
    if any(scene.graph.transforms.parents.get(p)!=root for p in PARTS):
        raise ValueError("source parents must share one world root")
    for name,n in CHILD_COUNTS.items():
        children=[x for x in scene.graph.nodes_geometry if scene.graph.transforms.parents.get(x)==name]
        if len(children)!=n:
            raise ValueError("source part material hierarchy changed")
    before={p:np.array(scene.graph.get(p)[0],copy=True) for p in PARTS}
    axle=before["tire"]
    if (not np.allclose(axle[:3,:3].T@axle[:3,:3],np.eye(3),atol=1e-6,rtol=0)
            or not np.isclose(np.linalg.det(axle[:3,:3]),1,atol=1e-6,rtol=0)
            or not np.allclose(before["rim_and_hub"],axle,atol=1e-6,rtol=0)
            or not np.allclose(before["pedals"],axle,atol=1e-6,rtol=0)):
        raise ValueError("wheel/rim/pedal pivot is not a common rigid axle")
    # This conjugation rotates around the actual axle even in bank/wheelie poses.
    motion=axle@r@np.linalg.inv(axle)
    if delta!=0:
        for p in MOVING:
            scene.graph.update(frame_to=p,frame_from=root,matrix=motion@before[p])
    if original_nodes!=set(scene.graph.nodes) or original_geometry!=set(scene.geometry):
        raise ValueError("material or node identities changed")
    for p in PARTS:
        expected=motion@before[p] if p in MOVING and delta!=0 else before[p]
        if not np.allclose(scene.graph.get(p)[0],expected,atol=1e-8,rtol=0):
            raise ValueError("unexpected parent motion")
    return {
        "source_owned_relative_wheel_phase_degrees":float(delta),
        "original_source_axle_world_xyz":list(map(float,axle[:3,3])),
        "rotated_parts":list(MOVING),"unchanged_parts":list(STATIONARY),
        "original_game_animation_or_physics_recovered":False
    }


def build(source:bytes,pose:str):
    import numpy as np
    import trimesh
    source_sha=hashlib.sha256(source).hexdigest()
    if SOURCE_GLBS.get(pose)!=source_sha or source[:4]!=b"glTF":
        raise ValueError("only SHA-pinned original 2026 experimental GLB accepted")
    scene=trimesh.load(io.BytesIO(source),file_type="glb",force="scene",process=False)
    nodes,meshnodes=set(scene.graph.nodes),set(scene.graph.nodes_geometry)
    original={k:(np.array(v.vertices,copy=True),np.array(v.faces,copy=True))
              for k,v in scene.geometry.items()}
    fixed={p:np.array(scene.graph.get(p)[0],copy=True) for p in STATIONARY}
    meta=synchronize(scene,delta_for_pose(pose))
    output=scene.export(file_type="glb")
    if not isinstance(output,bytes) or output[:4]!=b"glTF":
        raise ValueError("actual GLB serialization failed")
    roundtrip=trimesh.load(io.BytesIO(output),file_type="glb",force="scene",process=False)
    if (set(roundtrip.graph.nodes)!=nodes
            or set(roundtrip.graph.nodes_geometry)!=meshnodes
            or set(roundtrip.geometry)!=set(original)):
        raise ValueError("roundtrip changed source part/material identity")
    for k,(vertices,faces) in original.items():
        found=roundtrip.geometry[k]
        if not np.array_equal(found.vertices,vertices) or not np.array_equal(found.faces,faces):
            raise ValueError("roundtrip changed source mesh geometry")
    for p,T in fixed.items():
        if not np.allclose(roundtrip.graph.get(p)[0],T,atol=1e-7,rtol=0):
            raise ValueError("roundtrip moved original pedals/frame/saddle")
    meta.update({
        "schema":SCHEMA,"source_named_pose":pose,
        "source_pedal_phase_degrees":SOURCE_PHASE[pose],
        "upright_wheel_phase_reference_degrees":18.0,
        "historical_source_glb_sha256":source_sha,
        "derived_glb_sha256":hashlib.sha256(output).hexdigest(),
        "derived_glb_bytes":len(output),
        "source_meshes_and_materials_preserved":True,
        "original_3d_model_recovered":False,
        "owner_likeness_approved":False,"shipping_art_approved":False
    })
    return output,meta


def process(source:Path,pose:str,out:Path,receipt:Path):
    if len({source.resolve(),out.resolve(),receipt.resolve()})!=3:
        raise ValueError("source/output/receipt must differ")
    if any(p.exists() or p.is_symlink() for p in (out,receipt)):
        raise FileExistsError("do not replace experimental GLBs or receipts")
    payload,meta=build(source.read_bytes(),pose)
    out.parent.mkdir(parents=True,exist_ok=True)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".art4k-wheel-",dir=out.parent) as a, \
         tempfile.TemporaryDirectory(prefix=".art4k-wheel-receipt-",dir=receipt.parent) as b:
        staged,stagedreceipt=Path(a)/"complete.glb",Path(b)/"complete.json"
        staged.write_bytes(payload)
        stagedreceipt.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.link(staged,out)
        # A collision here leaves an unreceipted orphan. Never unlink possible
        # foreign replacement data during rollback. Receipt signals completion.
        os.link(stagedreceipt,receipt)
    return meta


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pose",choices=tuple(SOURCE_PHASE),required=True)
    p.add_argument("--source-glb",type=Path,required=True)
    p.add_argument("--out-glb",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(process(a.source_glb,a.pose,a.out_glb,a.receipt),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
