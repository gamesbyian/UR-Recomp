"""2026 unapproved five-part static visibility versus genuine source 4bpp interior changes.

No 1994 part label, pose, camera or colour assignment is inferred.
"""
import hashlib,json,sys,zipfile
from pathlib import Path
import numpy as np
import trimesh
from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.glb_parent_part_id_raster import (
    raster_part_ids,PARTS,PART_IDS,validated_camera
)
from tools.art.audit_real_glb_material_identity import MESH_NAMES
from tools.art.render_racer_glb_projection import model_mesh,render_mask
from tools.art.no_replace_report import publish_text_once

zip_path,model_path,camera_path,out_path=map(Path,sys.argv[1:])
# The shared no-replace publisher enforces safe, atomic output publication.
source_sha="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
model_sha="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
camera_sha="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
raw=zip_path.read_bytes()
if hashlib.sha256(raw).hexdigest()!=source_sha:raise ValueError("wrong source archive")
verified=audit_mesen(raw)
if verified["source_canonical_archive_sha256"]!=source_sha: raise ValueError("source audit contract")
if hashlib.sha256(model_path.read_bytes()).hexdigest()!=model_sha:raise ValueError("wrong GLB")
cam_raw=camera_path.read_bytes()
if hashlib.sha256(cam_raw).hexdigest()!=camera_sha:raise ValueError("wrong camera")
camera=json.loads(cam_raw)
validated_camera(camera)
scene=trimesh.load(model_path,file_type="glb",force="scene",process=False)
if not isinstance(scene,trimesh.Scene) or set(scene.graph.nodes_geometry)!=MESH_NAMES:
    raise ValueError("genuine GLB scene identity failed")
meshes=[]
for node in sorted(scene.graph.nodes_geometry):
    parent=node.split("__material_",1)[0]
    if parent not in PARTS or scene.graph.transforms.parents.get(node)!=parent:
        raise ValueError("GLB scene parent/material identity invalid")
    transform,geom_name=scene.graph.get(node)
    mesh=scene.geometry[geom_name].copy()
    mesh.apply_transform(transform)
    meshes.append({"part":parent,"vertices":mesh.vertices.tolist(),
                   "faces":[tuple(map(int,f)) for f in mesh.faces]})
planes=raster_part_ids(meshes,camera)
raw256=np.frombuffer(planes["id_plane_256"],dtype=np.uint8).reshape(256,256)
raw64=raw256[2::4,2::4]
all_v,all_f,_,_=model_mesh(model_path,model_sha)
ref=render_mask(all_v,all_f,camera).astype(bool)
if not np.array_equal(ref,raw256!=0):raise ValueError("part-ID masks disagree with original whole source 2026 GLB silhouette")
def anchor(mask):
    ys=np.flatnonzero(mask.any(axis=1))
    if not len(ys):raise ValueError("empty source alpha")
    y=int(ys[-1]);xs=np.flatnonzero(mask[y,:])
    return int(xs[0]+xs[-1]),2*y
model_anchor=anchor(raw64!=0)
def registered_id(alpha_anchor):
    dx,dy=(2*(a-b) for a,b in zip(alpha_anchor,model_anchor))
    ys,xs=np.nonzero(raw256)
    nx,ny=xs+dx,ys+dy
    if min(nx)<0 or max(nx)>=256 or min(ny)<0 or max(ny)>=256:
        raise ValueError("fixed registered model clips source")
    canvas=np.zeros_like(raw256)
    canvas[ny,nx]=raw256[ys,xs]
    return canvas[2::4,2::4]
def shift_noclip(array,dx,dy):
    out=np.zeros_like(array)
    sx0=max(0,-dx);sx1=min(64,64-dx)
    sy0=max(0,-dy);sy1=min(64,64-dy)
    out[sy0+dy:sy1+dy,sx0+dx:sx1+dx]=array[sy0:sy1,sx0:sx1]
    return out
with zipfile.ZipFile(zip_path) as archive:
    per={}
    for name,slot in (("blue",96),("red",97)):
        original=[]
        for tick in range(1601,1625):
            obj=decode_source_obj(
                decode_oam(archive.read(f"frame-{tick:06d}-oam.bin"))[slot],
                archive.read(f"frame-{tick:06d}-vram.bin"),
                archive.read(f"frame-{tick:06d}-cgram.bin"),
                oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
            original.append(np.frombuffer(obj["plane"],dtype=np.uint8).reshape(64,64))
        fixed_anchor=anchor(original[0]!=0)
        registered=registered_id(fixed_anchor)
        changed=np.zeros((64,64),dtype=np.int64)
        boundary=np.zeros((64,64),dtype=np.int64)
        for before,after in zip(original,original[1:]):
            changed+=(before!=after)&(before>0)&(after>0)
            boundary+=(before>0)!=(after>0)
        total_interior=int(changed.sum())
        actual_original_mask=(original[0]!=0)
        stats={}
        for label,(dx,dy) in {
            "registered":[0,0],"null_x_plus8":[8,0],"null_x_minus8":[-8,0],
            "null_y_plus8":[0,8],"null_y_minus8":[0,-8]}.items():
            model64=shift_noclip(registered,dx,dy)
            part_interior={part:int(changed[model64==idx].sum())
                            for part,idx in PART_IDS.items()}
            part_boundary={part:int(boundary[model64==idx].sum())
                            for part,idx in PART_IDS.items()}
            inside=sum(part_interior.values())
            opaque_model=int(np.count_nonzero(model64))
            stats[label]={"offset_source_logical_pixels":[dx,dy],
                "model_visible_pixels":opaque_model,
                "original_tick1601_alpha_iou":round(float(np.logical_and(model64!=0,actual_original_mask).sum()/np.logical_or(model64!=0,actual_original_mask).sum()),8),
                "original_interior_change_pixel_instances_on_candidate_model":inside,
                "interior_change_model_footprint_fraction":round(inside/total_interior,8),
                "original_interior_change_outside_candidate_model":total_interior-inside,
                "per_candidate_2026_part_interior_change_instances":part_interior,
                "per_candidate_2026_part_alpha_boundary_change_instances":part_boundary}
        per[name]={"source_OAM_slot":slot,
            "source_frame_1601_bottom_alpha_anchor_x2y2":list(fixed_anchor),
            "actual_original_interior_change_instances":total_interior,
            "actual_original_alpha_change_instances":int(boundary.sum()),
            "registered_2026_model_part_names":list(PARTS),
            "comparison":stats}
result={
    "schema":"UR-ART4K-MESEN24-STATIC-2026-VISIBLE-PART-ID-SUPPORT/1",
    "original_authentic_source_zip_sha256":source_sha,
    "original_2026_real_upright_glb_sha256":model_sha,
    "fixed_7_6_provisional_camera_sha256":camera_sha,
    "original_1994_part_to_GLB_identity_proven":False,
    "original_3d_motion_or_source_painted_material_recovered":False,
    "one_static_candidate_projection_no_fitted_motion":True,
    "one_lower_alpha_registration_at_tick1601_per_player":True,
    "candidate_GLB_part_id_raster_source64_sha256":hashlib.sha256(planes["id_plane_64"]).hexdigest(),
    "candidate_GLB_part_id_raster_full256_sha256":hashlib.sha256(planes["id_plane_256"]).hexdigest(),
    "whole_glb_256_silhouette_matches_depth_ID_raster_exactly":True,
    "per_source_player":per
}
publish_text_once(out_path,json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"schema":result["schema"],"part_sha":result["candidate_GLB_part_id_raster_source64_sha256"],
    "player":{name:{"source_interior":d["actual_original_interior_change_instances"],
    "source_alpha":d["actual_original_alpha_change_instances"],
    "coverage_by_control":{key:{k:row[k] for k in
    ("interior_change_model_footprint_fraction","original_tick1601_alpha_iou")}
                            for key,row in d["comparison"].items()},
    "registered_parts":d["comparison"]["registered"]["per_candidate_2026_part_interior_change_instances"]}
    for name,d in per.items()}}))
