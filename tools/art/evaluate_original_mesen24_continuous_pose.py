"""One bounded true-source 24-tick illustration, NOT original 3D inference."""
import hashlib,io,json,math,statistics,sys,time,zipfile
from pathlib import Path
import numpy as np
import trimesh
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
# Reuse the immutable incoming #3103 source identity without importing
# unmerged source-auditor code from another branch.
ZIP_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
TICKS=tuple(range(1601,1625))
from tools.art.experimental_continuous_five_parent_pose import (
    apply_scene,SOURCE_GLB_SHA256)
from tools.art.render_racer_glb_projection import model_mesh,render_mask,camera_config

archive,model,camera_file,output=map(Path,sys.argv[1:])
if output.exists(): raise FileExistsError(output)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==ZIP_SHA
assert hashlib.sha256(model.read_bytes()).hexdigest()==SOURCE_GLB_SHA256
camera_raw=camera_file.read_bytes()
camera=json.loads(camera_raw)
assert hashlib.sha256(camera_raw).hexdigest()=="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
camera_config(camera)

original={"blue":[],"red":[]}
with zipfile.ZipFile(archive) as z:
    assert json.loads(z.read("manifest.json"))["source_requested_capture_ticks"]==list(TICKS)
    for tick in TICKS:
        oam=decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))
        vram=z.read(f"frame-{tick:06d}-vram.bin")
        cgram=z.read(f"frame-{tick:06d}-cgram.bin")
        for name,slot in (("blue",96),("red",97)):
            obj=decode_source_obj(oam[slot],vram,cgram,
                     oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
            assert obj["size"]==64 and obj["slot"]==slot
            original[name].append(np.frombuffer(obj["alpha_mask"],dtype=np.uint8)
                                  .reshape(64,64).astype(bool).copy())

def lower_anchor(mask):
    y=max(np.flatnonzero(mask.any(axis=1)))
    xs=np.flatnonzero(mask[y,:])
    return (int(xs[0]+xs[-1]),int(2*y))

raw=trimesh.load(io.BytesIO(model.read_bytes()),
                 file_type="glb",force="scene",process=False)
original_v,original_f,_,_=model_mesh(model,SOURCE_GLB_SHA256)
baseline4=render_mask(original_v,original_f,camera).astype(bool)
rest64=baseline4[2::4,2::4]
model_x2,model_y2=lower_anchor(rest64)

def shift4_and_sample(mask,px2):
    dx=2*(px2[0]-model_x2)
    dy=2*(px2[1]-model_y2)
    yy,xx=np.nonzero(mask)
    xx2,yy2=xx+dx,yy+dy
    if min(xx2)<0 or max(xx2)>=256 or min(yy2)<0 or max(yy2)>=256:
        raise ValueError("source-fixed candidate placement clips model; cannot auto-fit")
    translated=np.zeros_like(mask)
    translated[yy2,xx2]=True
    return translated[2::4,2::4]

anchors={name:lower_anchor(rows[0]) for name,rows in original.items()}
start=time.perf_counter()
trajectories={
 "static_neutral":[(0.0,0.0) for _ in TICKS],
 "direct_drive_24deg_per_tick":[(float((step*24+180)%360-180),0.0) for step in range(24)],
 "same_drive_plus_sinusoidal_frame_pitch_10deg":[(
    float((step*24+180)%360-180),float(10*math.sin(2*math.pi*step/24)))
    for step in range(24)],
}
output_arms={}
for arm,params in trajectories.items():
    predicted=[]
    for step,(phase,pitch) in enumerate(params):
        if arm=="static_neutral":
            mask4=baseline4
        else:
            apply_scene(raw,phase,pitch)
            mesh=(raw.to_geometry() if callable(getattr(raw,"to_geometry",None))
                  else raw.dump(concatenate=True))
            mask4=render_mask(np.asarray(mesh.vertices),np.asarray(mesh.faces),camera).astype(bool)
        predicted.append(mask4)
    trial={"samples":len(predicted),"parameters":{"initial_drive_deg":0,"per_tick_drive_deg":0 if arm=="static_neutral" else 24,
        "pitch_amplitude_deg":10 if "sinusoidal" in arm else 0,
        "pitch_period_ticks":24 if "sinusoidal" in arm else None},
        "per_player":{}}
    for name in ("blue","red"):
        a=anchors[name]
        models=[shift4_and_sample(mask,a) for mask in predicted]
        sources=original[name]
        means=[]
        for model64,source64 in zip(models,sources):
            union=np.logical_or(model64,source64).sum()
            means.append(float(np.logical_and(model64,source64).sum()/union))
        s_deltas=[np.logical_xor(sources[i],sources[i+1]) for i in range(23)]
        m_deltas=[np.logical_xor(models[i],models[i+1]) for i in range(23)]
        s_pixels=sum(int(a.sum()) for a in s_deltas)
        m_pixels=sum(int(a.sum()) for a in m_deltas)
        true_pixels=sum(int(np.logical_and(a,b).sum()) for a,b in zip(s_deltas,m_deltas))
        union=s_pixels+m_pixels-true_pixels
        counts=[int(a.sum()) for a in m_deltas]
        trial["per_player"][name]={
          "source_tick1601_fixed_alpha_anchor_x2y2":list(a),
          "mean_24_source_silhouette_iou":round(statistics.mean(means),8),
          "model_changed_edges":sum(c>0 for c in counts),
          "model_held_edges":sum(c==0 for c in counts),
          "original_changed_edges":23,
          "mean_model_changed_pixels_per_edge":round(statistics.mean(counts),4),
          "median_model_changed_pixels_per_edge":statistics.median(counts),
          "original_changed_pixels_sum":s_pixels,
          "model_changed_pixels_sum":m_pixels,
          "change_pixel_intersection":true_pixels,
          "change_pixel_recall":round(true_pixels/s_pixels,8),
          "change_pixel_precision":round(true_pixels/m_pixels,8) if m_pixels else 0.0,
          "change_pixel_iou":round(true_pixels/union,8),
        }
    output_arms[arm]=trial
result={
 "schema":"UR-ART4K-AUTHENTIC-MESEN24-VS-2026-FIVE-PARENT-MOTION-CONTROLS/1",
 "original_consecutive_source_24_zip_sha256":ZIP_SHA,
 "source_original_ticks":list(TICKS),
 "candidate_actual_upright_glb_sha256":SOURCE_GLB_SHA256,
 "provisional_fixed_camera_sha256":hashlib.sha256(camera_raw).hexdigest(),
 "fixed_source_anchor_selected_once_at_tick1601":True,
 "no_fitted_phase_camera_geometry_or_frame_translation":True,
 "original_observed_source_per_player_orientation":"held OAM source; no completed-screen reflection applied",
 "original_1994_3d_animation_or_art_approved":False,
 "computer_seconds":round(time.perf_counter()-start,2),
 "arms":output_arms,
}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({
 "status":"PASS",
 "source_original_frames":24,
 "model_original_source_sha256":SOURCE_GLB_SHA256,
 "elapsed_seconds":result["computer_seconds"],
 "arms":{arm:{p:{key:v[key] for key in
   ("mean_24_source_silhouette_iou","model_changed_edges",
    "mean_model_changed_pixels_per_edge","change_pixel_recall",
    "change_pixel_precision","change_pixel_iou")}
   for p,v in data["per_player"].items()} for arm,data in output_arms.items()},
 "report_sha256":hashlib.sha256(output.read_bytes()).hexdigest()
},indent=2))
