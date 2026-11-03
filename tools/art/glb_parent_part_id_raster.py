#!/usr/bin/env python3
"""Research-only fixed-camera colour-independent GLB parent-part ID raster.

Existing authored five-GLB geometry remains immutable. Source-original camera,
pose pairing, part semantics and owner likeness remain unverified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

PARTS=("tire","rim_and_hub","fork_and_frame","pedals","saddle")
PART_IDS={name:i+1 for i,name in enumerate(PARTS)}
SCHEMA="UR-ART4K-GLB-PARENT-PART-ID-RASTER/1"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def validated_camera(c):
    if (not isinstance(c,dict) or c.get("schema")!="UR-RACER-FIXED-ORTHOGRAPHIC-CAMERA/1" or
            c.get("source_pixel_aspect")!="7:6" or
            c.get("camera_calibration_status")!="provisional"):
        raise ValueError("only the existing provisional fixed orthographic camera is admissible")
    vectors=[]
    for key in ("right_world","up_world","origin_world"):
        v=c.get(key)
        if (not isinstance(v,list) or len(v)!=3 or
                any(type(x) not in (int,float) or not math.isfinite(x) for x in v)):
            raise ValueError("invalid camera basis: "+key)
        vectors.append(v)
    right,up,origin=vectors
    if (abs(dot(right,right)-1)>1e-5 or abs(dot(up,up)-1)>1e-5 or
            abs(dot(right,up))>1e-5):
        raise ValueError("camera basis must be orthonormal")
    scale=c.get("logical_pixels_per_model_unit_vertical")
    anchor=c.get("source_anchor_x2_y2")
    if (type(scale) not in (int,float) or not math.isfinite(scale) or not 0<scale<=100 or
            not isinstance(anchor,list) or len(anchor)!=2 or
            any(type(x) is not int or not -256<=x<=256 for x in anchor)):
        raise ValueError("bad fixed camera anchor or scale")
    # Cross(right,up) is a *declared experimental front direction*.
    return right,up,origin,scale,anchor,cross(right,up)

def raster_part_ids(meshes:list,camera:dict)->dict:
    """CPU depth-buffer: 5 immutable parent names, no material RGB lookup."""
    right,up,origin,scale,anchor,front=validated_camera(camera)
    if not isinstance(meshes,list) or not meshes:
        raise ValueError("missing GLB part geometry")
    # Retain the true maximum depth for each parent before deciding ownership.
    # An epsilon-filtered running winner is order-dependent across triangles.
    depth_by_part={name:[float("-inf")]*(256*256) for name in PARTS}
    observed=set()
    for mesh in meshes:
        part=mesh.get("part") if isinstance(mesh,dict) else None
        if part not in PART_IDS:raise ValueError("unknown GLB parent part")
        vertices=mesh.get("vertices");faces=mesh.get("faces")
        if not isinstance(vertices,list) or not vertices or not isinstance(faces,list) or not faces:
            raise ValueError("empty GLB parent triangle geometry")
        observed.add(part);projected=[]
        for v in vertices:
            if (not isinstance(v,(list,tuple)) or len(v)!=3 or
                    any(type(n) not in (int,float) or not math.isfinite(n) for n in v)):
                raise ValueError("bad source GLB vertex")
            p=[v[i]-origin[i] for i in range(3)]
            x=dot(p,right)*(scale*4*6/7)+2*anchor[0]+2
            y=-dot(p,up)*(scale*4)+2*anchor[1]+2
            if x<0 or x>255 or y<0 or y>255:
                raise ValueError("fixed camera would clip the original geometry")
            projected.append((x,y,dot(p,front)))
        depths=depth_by_part[part]
        for face in faces:
            if (not isinstance(face,(list,tuple)) or len(face)!=3 or
                    any(type(i) is not int or i<0 or i>=len(projected) for i in face)):
                raise ValueError("bad original GLB face indices")
            a,b,c=(projected[i] for i in face)
            det=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if abs(det)<1e-11:continue
            x0=max(0,math.floor(min(a[0],b[0],c[0])));x1=min(255,math.ceil(max(a[0],b[0],c[0])))
            y0=max(0,math.floor(min(a[1],b[1],c[1])));y1=min(255,math.ceil(max(a[1],b[1],c[1])))
            for y in range(y0,y1+1):
                for x in range(x0,x1+1):
                    dx=x-a[0];dy=y-a[1]
                    u=(dx*(c[1]-a[1])-dy*(c[0]-a[0]))/det
                    v=(dy*(b[0]-a[0])-dx*(b[1]-a[1]))/det
                    if u < -1e-9 or v < -1e-9 or u+v > 1+1e-9:continue
                    d=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2]);q=y*256+x
                    if d>depths[q]:depths[q]=d
    if observed != set(PARTS):
        raise ValueError("all five real GLB parent components must be present")
    labels=bytearray(256*256)
    for q in range(256*256):
        nearest=max(depth_by_part[name][q] for name in PARTS)
        if nearest==float("-inf"):continue
        near=[name for name in PARTS if depth_by_part[name][q]>=nearest-1e-7]
        if len(near)!=1:
            raise ValueError("different GLB parents are indistinguishable in depth")
        labels[q]=PART_IDS[near[0]]
    source=bytes(labels[(4*y+2)*256+4*x+2] for y in range(64) for x in range(64))
    if not any(source):raise ValueError("no GLB pixels at 64px source centres")
    return {"id_plane_256":bytes(labels),"id_plane_64":source,
            "part_id_names":{i:part for part,i in PART_IDS.items()}}

def inspect_existing_glb(glb:Path,expected_sha:str,camera_path:Path)->dict:
    """Authenticate actual five-part/sixteen-material GLB, not surrogate triangles."""
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError("optional offline Trimesh required") from exc
    from tools.art.audit_real_glb_material_identity import MESH_NAMES
    raw=glb.read_bytes()
    if sha(raw)!=expected_sha or raw[:4]!=b"glTF":
        raise ValueError("published experimental GLB SHA mismatch")
    camera_raw=camera_path.read_bytes();camera=json.loads(camera_raw)
    validated_camera(camera)
    scene=trimesh.load(glb,file_type="glb",force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or set(scene.graph.nodes_geometry)!=MESH_NAMES:
        raise ValueError("wrong existing sixteen-material GLB scene graph")
    meshes=[]
    for node in sorted(scene.graph.nodes_geometry):
        parent=node.split("__material_",1)[0]
        if parent not in PARTS or scene.graph.transforms.parents.get(node)!=parent:
            raise ValueError("GLB material disconnected from original parent")
        transform,name=scene.graph.get(node)
        mesh=scene.geometry[name]
        if not isinstance(mesh,trimesh.Trimesh):raise ValueError("not a real GLB triangle mesh")
        world=mesh.copy();world.apply_transform(transform)
        meshes.append({"part":parent,"vertices":world.vertices.tolist(),
                       "faces":[tuple(int(i) for i in f) for f in world.faces]})
    planes=raster_part_ids(meshes,camera)
    return {"schema":SCHEMA,"real_experimental_glb_sha256":expected_sha,
            "provisional_camera_sha256":sha(camera_raw),
            "source64_part_id_sha256":sha(planes["id_plane_64"]),
            "full256_part_id_sha256":sha(planes["id_plane_256"]),
            "source64_visible_pixels":sum(bool(i) for i in planes["id_plane_64"]),
            "part_id_names":planes["part_id_names"],
            "original_1994_camera_verified":False,
            "source_sprite_to_GLb_pose_mapping_verified":False,
            "original_3d_part_identity_verified":False,
            "owner_likeness_approved":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glb",type=Path,required=True)
    ap.add_argument("--glb-sha256",required=True)
    ap.add_argument("--camera",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    from tools.art.no_replace_report import publish_text_once
    report=inspect_existing_glb(args.glb,args.glb_sha256,args.camera)
    publish_text_once(args.out,json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
