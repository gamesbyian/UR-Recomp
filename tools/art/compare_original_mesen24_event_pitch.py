"""Two predeclared authentic upper-band events; three fixed control arms."""
import hashlib,io,json,sys,zipfile
from pathlib import Path
from tools.art.no_replace_report import publish_text_once
import numpy as np
import trimesh
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.experimental_continuous_five_parent_pose import apply_scene, SOURCE_GLB_SHA256
from tools.art.render_racer_glb_projection import model_mesh,render_mask
zip_path,model_path,camera_path,out_path=map(Path,sys.argv[1:])
assert not out_path.exists()
assert hashlib.sha256(zip_path.read_bytes()).hexdigest()=="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
assert hashlib.sha256(model_path.read_bytes()).hexdigest()==SOURCE_GLB_SHA256
camera_raw=camera_path.read_bytes()
assert hashlib.sha256(camera_raw).hexdigest()=="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
camera=json.loads(camera_raw)
with zipfile.ZipFile(zip_path) as z:
    def original(tick,slot):
        obj=decode_source_obj(decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot],
                z.read(f"frame-{tick:06d}-vram.bin"),z.read(f"frame-{tick:06d}-cgram.bin"),
                oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
        return np.frombuffer(obj["alpha_mask"],dtype=np.uint8).reshape(64,64).astype(bool)
    originals={name: {t:original(t,slot) for t in (1601,before,after)}
               for name,slot,before,after in
               (("blue",96,1602,1603),("red",97,1605,1606))}
def anchor(mask):
    y=int(np.flatnonzero(mask.any(axis=1))[-1])
    x=np.flatnonzero(mask[y,:])
    return int(x[0]+x[-1]), 2*y
vertices,faces,_,_=model_mesh(model_path,SOURCE_GLB_SHA256)
base=render_mask(vertices,faces,camera).astype(bool)
model_anchor=anchor(base[2::4,2::4])
scene=trimesh.load(io.BytesIO(model_path.read_bytes()),force="scene",file_type="glb",process=False)
def render(phase,pitch):
    apply_scene(scene,phase,pitch)
    merged=scene.to_geometry() if hasattr(scene,"to_geometry") else scene.dump(concatenate=True)
    return render_mask(np.asarray(merged.vertices),np.asarray(merged.faces),camera).astype(bool)
def sample_fixed(mask,source_anchor):
    dx=2*(source_anchor[0]-model_anchor[0]);dy=2*(source_anchor[1]-model_anchor[1])
    ys,xs=np.nonzero(mask);nx,ny=xs+dx,ys+dy
    if min(nx)<0 or max(nx)>=256 or min(ny)<0 or max(ny)>=256:raise ValueError("model clips")
    shifted=np.zeros_like(mask);shifted[ny,nx]=True
    return shifted[2::4,2::4]
events={"blue":(1602,1603,[(4,14),(15,26),(27,38)]),
        "red":(1605,1606,[(5,15),(16,26),(27,37)])}
out={}
for name,(before,after,bands) in events.items():
    src=originals[name]
    source_delta=np.logical_xor(src[before],src[after])
    fixed_anchor=anchor(src[1601])
    def phase(t):return float(((t-1601)*24+180)%360-180)
    predicted_before=sample_fixed(render(phase(before),0),fixed_anchor)
    controls={}
    for pitch in (0,10,-10):
        after_mask=sample_fixed(render(phase(after),pitch),fixed_anchor)
        change=np.logical_xor(predicted_before,after_mask)
        details=[]
        for lo,hi in bands:
            s=source_delta[lo:hi+1,:]
            m=change[lo:hi+1,:]
            details.append({"y_band":[lo,hi],
                  "source_changed_pixels":int(s.sum()),
                  "model_changed_pixels":int(m.sum()),
                  "intersect_changed_pixels":int(np.logical_and(s,m).sum())})
        source_total=int(source_delta.sum());model_total=int(change.sum());match=int(np.logical_and(source_delta,change).sum())
        controls[str(pitch)]={"model_delta_pixels":model_total,
                  "source_delta_pixels":source_total,
                  "change_pixel_intersection":match,
                  "change_precision":round(match/model_total,8) if model_total else 0.,
                  "change_recall":round(match/source_total,8),
                  "change_iou":round(match/(source_total+model_total-match),8),
                  "source_y_band_details":details}
    out[name]={"actual_source_edge":[before,after],
               "original_source_visible_anchor_from_tick1601":fixed_anchor,
               "part_motion_before_frame_pitch_deg":0,
               "before_and_after_wheel_phase_deg":[phase(before),phase(after)],
               "all_controls":controls}
report={"schema":"UR-ART4K-MESEN24-PREDECLARED-TWO-UPPER-EDGES-FRAME-STEP-CONTROL/1",
        "original_source_archive_sha256":"28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6",
        "original_upright_2026_glb_sha256":SOURCE_GLB_SHA256,
        "fixed_provisional_camera_sha256":hashlib.sha256(camera_raw).hexdigest(),
        "source_model_registration_fixed_at_tick1601":True,
        "source_event_edges_seen_in_advance_and_not_blind":True,
        "only_predeclared_after_pitches_degrees":[0,10,-10],
        "original_1994_camera_pose_or_bone_mapping_recovered":False,
        "per_source_player":out}
publish_text_once(out_path,json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps(report,sort_keys=True,indent=2))
