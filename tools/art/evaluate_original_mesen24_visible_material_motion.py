"""Bounded original Mesen 4bpp interior-change vs moving REAL 2026 material IDs.

Only change-location support, not original 1994 palette/material/joint mapping.
"""
import hashlib,io,json,math,sys,zipfile
from pathlib import Path
import numpy as np
import trimesh
from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.audit_real_glb_material_identity import MESH_NAMES
from tools.art.experimental_continuous_five_parent_pose import apply_scene
from tools.art.glb_parent_part_id_raster import (
    validated_camera,raster_part_ids,PARTS,PART_IDS
)
from tools.art.render_racer_glb_projection import model_mesh,render_mask
from tools.art.no_replace_report import publish_text_once

source_zip,model_path,camera_path,out_path=map(Path,sys.argv[1:])
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
MODEL_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
EVENTS=((1602,1603),(1605,1606),(1609,1610))
FRAMES=tuple(sorted(set(t for e in EVENTS for t in e)))
raw=source_zip.read_bytes()
if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError("wrong original 24 Mesen source archive")
if audit_mesen(raw)["source_canonical_archive_sha256"]!=SOURCE_SHA:raise ValueError("original source audit failed")
model_bytes=model_path.read_bytes()
if hashlib.sha256(model_bytes).hexdigest()!=MODEL_SHA:raise ValueError("wrong 2026 GLB")
cam_bytes=camera_path.read_bytes()
if hashlib.sha256(cam_bytes).hexdigest()!=CAMERA_SHA:raise ValueError("wrong provisional camera")
camera=json.loads(cam_bytes)
right,up,origin,scale,anchor,front=validated_camera(camera)
right,up,origin,front=(np.asarray(x,dtype=float) for x in (right,up,origin,front))

scene=trimesh.load(io.BytesIO(model_bytes),file_type="glb",force="scene",process=False)
if not isinstance(scene,trimesh.Scene) or set(scene.graph.nodes_geometry)!=MESH_NAMES:
    raise ValueError("original real model sixteen-material graph changed")
nodes=tuple(sorted(scene.graph.nodes_geometry))
if len(nodes)!=16 or any(node.split("__material_",1)[0] not in PARTS for node in nodes):
    raise ValueError("unexpected 2026 material partitions")
material_to_part=np.array([0]+[PART_IDS[node.split("__material_",1)[0]] for node in nodes],dtype=np.uint8)
coord=np.arange(256,dtype=float)

def material_ids():
    """Independent depth-assembled, source-centre-rastered 16 material labels."""
    depth=np.full((len(nodes),256,256),-np.inf,dtype=np.float64)
    for idx,node in enumerate(nodes):
        part=node.split("__material_",1)[0]
        if scene.graph.transforms.parents.get(node)!=part:
            raise ValueError("material no longer child of named original 2026 parent")
        transform,geom=scene.graph.get(node)
        mesh=scene.geometry[geom]
        v=np.asarray(mesh.vertices,dtype=float)
        faces=np.asarray(mesh.faces,dtype=int)
        if not len(v) or not np.isfinite(v).all() or np.min(faces)<0 or np.max(faces)>=len(v):
            raise ValueError("invalid original material geometry")
        v4=np.column_stack((v,np.ones(len(v))))
        world=(v4@np.asarray(transform,dtype=float).T)[:,:3]
        points=world-origin
        projected=np.column_stack((points@right*(scale*4*6/7)+2*anchor[0]+2,
                   -(points@up)*(scale*4)+2*anchor[1]+2,points@front))
        if np.any(projected[:,:2]<0) or np.any(projected[:,:2]>255):
            raise ValueError("candidate camera clips 2026 material mesh")
        for face in faces:
            a,b,c=projected[face]
            det=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if abs(det)<1e-11:continue
            x0=max(0,math.floor(min(a[0],b[0],c[0])))
            x1=min(255,math.ceil(max(a[0],b[0],c[0])))
            y0=max(0,math.floor(min(a[1],b[1],c[1])))
            y1=min(255,math.ceil(max(a[1],b[1],c[1])))
            if x1<x0 or y1<y0:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
            dx,dy=xx-a[0],yy-a[1]
            u=(dx*(c[1]-a[1])-dy*(c[0]-a[0]))/det
            v=(dy*(b[0]-a[0])-dx*(b[1]-a[1]))/det
            inside=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)
            z=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2])
            dst=depth[idx,y0:y1+1,x0:x1+1]
            np.maximum(dst,np.where(inside,z,-np.inf),out=dst)
    nearest=np.max(depth,axis=0)
    anypart=np.isfinite(nearest)
    tied=(np.isfinite(depth)&(depth>=nearest[None,:,:]-1e-7)).sum(axis=0)
    tie_count=int(((tied>1)&anypart).sum())
    if tie_count:raise ValueError(f"{tie_count} material depth ownership ties: unresolved")
    result=np.zeros((256,256),dtype=np.uint8)
    result[anypart]=np.argmax(depth,axis=0)[anypart].astype(np.uint8)+1
    return result

def anchor_from_alpha(alpha):
    ys=np.flatnonzero(alpha.any(axis=1))
    if not len(ys):raise ValueError("empty source alpha")
    y=int(ys[-1]);xs=np.flatnonzero(alpha[y,:])
    return int(xs[0]+xs[-1]),2*y

def source_registered(mat256,anchor_at_tick1601,neutral_anchor):
    dx=2*(anchor_at_tick1601[0]-neutral_anchor[0])
    dy=2*(anchor_at_tick1601[1]-neutral_anchor[1])
    y,x=np.nonzero(mat256)
    xx,yy=x+dx,y+dy
    if min(xx)<0 or max(xx)>=256 or min(yy)<0 or max(yy)>=256:
        raise ValueError("frozen source-anchor placement would clip model")
    out=np.zeros_like(mat256);out[yy,xx]=mat256[y,x]
    return out[2::4,2::4]

def shifted64(mask,dx,dy):
    out=np.zeros_like(mask)
    sx0=max(0,-dx);sx1=min(64,64-dx)
    sy0=max(0,-dy);sy1=min(64,64-dy)
    out[sy0+dy:sy1+dy,sx0+dx:sx1+dx]=mask[sy0:sy1,sx0:sx1]
    return out

def support(original,model):
    s=int(original.sum());m=int(model.sum())
    hit=int(np.logical_and(original,model).sum())
    if s<1:raise ValueError("empty actual source transition")
    return {"original_opaque_interior_index_changes":s,
       "model_label_change_pixels":m,
       "spatial_intersection":hit,
       "source_recall":round(hit/s,8),
       "model_precision":round(hit/m,8) if m else 0,
       "change_support_iou":round(hit/(s+m-hit),8) if s+m-hit else 0}

with zipfile.ZipFile(source_zip) as z:
    orig={}
    for who,slot in (("blue",96),("red",97)):
        orig[who]={}
        for tick in (1601,)+FRAMES:
            obj=decode_source_obj(decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot],
                 z.read(f"frame-{tick:06d}-vram.bin"),z.read(f"frame-{tick:06d}-cgram.bin"),
                 oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
            orig[who][tick]=np.frombuffer(obj["plane"],dtype=np.uint8).reshape(64,64)

neutral256=material_ids()
all_v,all_f,_,_=model_mesh(model_path,MODEL_SHA)
neutral_full=render_mask(all_v,all_f,camera).astype(bool)
if not np.array_equal(neutral256!=0,neutral_full):
    raise ValueError("16-material depth renderer does not equal independent whole-model silhouette")
neutral_anchor=anchor_from_alpha(neutral256[2::4,2::4]!=0)
# Fully independent existing five-part scene-depth renderer from original meshes.
parts=[]
for node in nodes:
    matrix,geom=scene.graph.get(node)
    mesh=scene.geometry[geom].copy()
    mesh.apply_transform(matrix)
    parts.append({"part":node.split("__material_",1)[0],
                  "vertices":mesh.vertices.tolist(),
                  "faces":[tuple(map(int,face)) for face in mesh.faces]})
previous=raster_part_ids(parts,camera)
reference=np.frombuffer(previous["id_plane_256"],dtype=np.uint8).reshape(256,256)
actual=material_to_part[neutral256]
if not np.array_equal(actual,reference):
    raise ValueError("material depth raster disagrees with established original 2026 five-part ID renderer")

by_tick={}
for tick in FRAMES:
    phase=float((((tick-1601)*24+180)%360)-180)
    apply_scene(scene,phase,0.)
    mat=material_ids()
    # Cross-verify opacity against independent whole-model raster at every posed tick.
    merged=scene.to_geometry() if callable(getattr(scene,"to_geometry",None)) else scene.dump(concatenate=True)
    image=render_mask(np.asarray(merged.vertices),np.asarray(merged.faces),camera)
    if not np.array_equal(mat!=0,image!=0):
        raise ValueError("posed material IDs disagree with independent model alpha")
    by_tick[tick]=mat

per={}
for who in ("blue","red"):
    fixed=anchor_from_alpha(orig[who][1601]!=0)
    poses={tick:source_registered(mat,fixed,neutral_anchor) for tick,mat in by_tick.items()}
    events=[]
    for before,after in EVENTS:
        source_before=orig[who][before]
        source_after=orig[who][after]
        source_changed=(source_before!=source_after)&(source_before>0)&(source_after>0)
        a,b=poses[before],poses[after]
        mat_changed=(a!=b)&(a>0)&(b>0)
        p1,p2=material_to_part[a],material_to_part[b]
        part_changed=(p1!=p2)&(p1>0)&(p2>0)
        variants={"registered":(0,0),"null_x_plus8":(8,0),
           "null_x_minus8":(-8,0),"null_y_plus8":(0,8),"null_y_minus8":(0,-8)}
        events.append({"actual_original_source_edge":[before,after],
           "source_changed_alpha_boundary":int(np.logical_xor(source_before>0,source_after>0).sum()),
           "source_original_index_change_in_opaque_intersection":int(source_changed.sum()),
           "visible_material_id_support":{
              label:support(source_changed,shifted64(mat_changed,*shift))
              for label,shift in variants.items()},
           "visible_five_parent_id_support":{
              label:support(source_changed,shifted64(part_changed,*shift))
              for label,shift in variants.items()},
           "pose_delta_deg_from_canonical_upright_2026":[
               float((((before-1601)*24+180)%360)-180),
               float((((after-1601)*24+180)%360)-180)]})
    per[who]={"source_OAM_slot":{"blue":96,"red":97}[who],
       "fixed_source_tick1601_alpha_anchor_x2y2":list(fixed),
       "event_controls":events}

report={"schema":"UR-ART4K-MESEN24-REAL-GLB-MOVING-MATERIAL-VS-ORIGINAL-INTERIOR/1",
    "source_original_24tick_zip_sha256":SOURCE_SHA,
    "model_single_real_2026_upright_glb_sha256":MODEL_SHA,
    "one_provisional_7_6_camera_sha256":CAMERA_SHA,
    "model_original_sixteen_material_nodes":list(nodes),
    "candidate_material_id_to_five_parent":material_to_part.tolist(),
    "exact_256px_neutral_material_silhouette_and_five_part_renderer_agreement":True,
    "all_six_poses_pixel_identical_alpha_to_independent_renderer":True,
    "original_selected_source_edges":[list(e) for e in EVENTS],
    "illustrative_2026_direct_drive_step_deg_per_original_tick":24,
    "frame_pitch_deg":0,
    "no_per_frame_source_fit":True,
    "no_original_1994_palette_to_model_material_mapping":True,
    "source_original_camera_parts_and_3D_pose_recovered":False,
    "source_original_replay_24tick_is_already_inspected_not_blind":True,
    "per_original_OAM_source_player":per}
publish_text_once(out_path,json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps({"schema":report["schema"],"result_by_source_player":{
    name:[{"edge":e["actual_original_source_edge"],
       "original_interior":e["source_original_index_change_in_opaque_intersection"],
       "material":e["visible_material_id_support"]["registered"],
       "parent":e["visible_five_parent_id_support"]["registered"]}
       for e in rows["event_controls"]]
    for name,rows in per.items()}}))
