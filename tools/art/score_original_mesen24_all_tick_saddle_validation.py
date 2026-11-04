#!/usr/bin/env python3
"""Full original 24 consecutive PPU ticks, 2 racers, one real 2026 GLB.

A retrospective temporal stress test of previously frozen 2026 saddle mount
hypotheses, not a source-1994 pose or joint reconstruction. Original PPU/OAM
planes and 24x64 phase/orientation exact ROM IDs are verified by the SAME
existing source readers; no new emulator or separate graphics rig.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.score_original_mesen24_fixed_pivot_glb import (
    check_receipts,read_original_roles,source_center,rotate_source_2d,
    anchor,registered_mask4,metric,fixed_source_y_band_metrics,SELECTED,
    SOURCE_Y_BANDS,SCAD_SHA,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-MESEN24-ALL-TICKS-REAL-GLB-SADDLE-TEMPORAL/1"
TICKS=tuple(range(1601,1625))
ARMS=("static_original_2d","source_original_2d_rotation",
      "static_2026_3d","wheel_axle_root_only",
      "wheel_axle_root_saddle_lean_minus15",
      "wheel_axle_root_saddle_lean_plus15",
      "historical_midbody_root_only")
SOURCE_FIRST_REGISTRATION_TICK=1601
# Exact earlier eight-event source/2026 all-arm run #41871437114 is an
# independent numerical guard: the extended scorer must first reproduce the
# already authenticated exact 8-source event subset, with no silent new camera.
PRIOR_EIGHT_TICK_POOLED={
    "blue":{
        "static_original_2d":0.77513966,
        "source_original_2d_rotation":0.83754513,
        "static_2026_3d":0.49047014,
        "wheel_axle_root_only":0.52846054,
        "wheel_axle_root_saddle_lean_minus15":0.50574713,
        "wheel_axle_root_saddle_lean_plus15":0.56812169,
        "historical_midbody_root_only":0.51254019,
    },
    "red":{
        "static_original_2d":0.74206897,
        "source_original_2d_rotation":0.82731214,
        "static_2026_3d":0.36390017,
        "wheel_axle_root_only":0.55107352,
        "wheel_axle_root_saddle_lean_minus15":0.53058596,
        "wheel_axle_root_saddle_lean_plus15":0.58201058,
        "historical_midbody_root_only":0.28563744,
    },
}


def change_plane(a:bytes,b:bytes)->bytes:
    if (type(a) is not bytes or type(b) is not bytes or
            len(a)!=4096 or len(b)!=4096 or set(a)-{0,1} or set(b)-{0,1}):
        raise ValueError("exact two original 64x64 source binary sprites required")
    return bytes(int(x!=y) for x,y in zip(a,b))


def pooled_binary_metrics(source:dict[int,bytes],candidate:dict[int,bytes],
                          ticks:tuple[int,...])->dict:
    if (not ticks or len(set(ticks))!=len(ticks) or
            any(t not in source or t not in candidate for t in ticks)):
        raise ValueError("complete chronological source and 2026 image predictions required")
    metrics=[metric(source[t],candidate[t]) for t in ticks]
    totals={k:sum(m[k] for m in metrics) for k in ("tp","fp","fn")}
    den=sum(totals.values())
    if not den:raise ValueError("empty source/model silhouette comparison")
    region={}
    for name,_,_ in SOURCE_Y_BANDS:
        slices=[fixed_source_y_band_metrics(source[t],candidate[t])[name]
                for t in ticks]
        c={k:sum(m[k] for m in slices) for k in ("tp","fp","fn")}
        n=sum(c.values())
        region[name]={**c,"pooled_iou":round(c["tp"]/n,8) if n else 1.}
    if any(sum(v[k] for v in region.values())!=totals[k] for k in totals):
        raise ValueError("source 64px region counts do not partition original")
    return {"source_frames":len(ticks),"tp_fp_fn":totals,
            "mean_iou":round(sum(m["iou"] for m in metrics)/len(ticks),8),
            "pooled_iou":round(totals["tp"]/den,8),
            "fixed_source_y_bands":region}


def audit(source_zip:bytes,pose_raw:bytes,axis_raw:bytes,camera_raw:bytes,
          exports:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.experimental_fixed_root_orbit import apply_root_scene
    from tools.art.experimental_temporary_saddle_lean import temporary_saddle_pitch
    from tools.art.render_racer_glb_projection import render_mask

    pose,axis,camera=check_receipts(source_zip,pose_raw,axis_raw,camera_raw)
    original=read_original_roles(source_zip,pose,all_24_ticks=True)
    if set(original)!={"blue","red"} or any(set(ticks)!=set(TICKS)
                                            for ticks in original.values()):
        raise ValueError("all 48 exact consecutive original two-player frames required")
    centre=source_center(axis)
    validate=runpy.run_path(str(Path(__file__).resolve().parent/
                                  "model-review/stage_pages.py"))["validate"]
    ptr,outputs=validate(exports,"upright")
    glb=outputs["glb"].read_bytes()
    if ptr["source_sha256"]!=SCAD_SHA or ptr["glb_sha256"]!=hashlib.sha256(glb).hexdigest():
        raise ValueError("source-authenticated 2026 current-success GLB changed")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)
    def render(index:int,pivot:str,local_saddle_deg:float=0.):
        apply_root_scene(scene,index,pivot,0.,0.)
        def exact_alpha():
            whole=(scene.to_geometry() if callable(getattr(scene,"to_geometry",None))
                   else scene.dump(concatenate=True))
            return render_mask(np.asarray(whole.vertices),
                               np.asarray(whole.faces),camera).astype(bool)
        if local_saddle_deg:
            with temporary_saddle_pitch(scene,local_saddle_deg):
                return exact_alpha()
        return exact_alpha()
    neutral=render(0,"wheel_axle")
    model_anchor=anchor(bytes(neutral[2::4,2::4].astype(np.uint8).ravel()))
    cached={("static_2026_3d",0):neutral}
    by_role={}
    for role,frames in original.items():
        reference=frames[SOURCE_FIRST_REGISTRATION_TICK]
        position=anchor(reference["alpha"])
        predictions={arm:{} for arm in ARMS}
        source={tick:frames[tick]["alpha"] for tick in TICKS}
        for tick in TICKS:
            original_angle=frames[tick]["angle"]
            planes={
                "static_original_2d":reference["alpha"],
                "source_original_2d_rotation":rotate_source_2d(
                    reference["alpha"],original_angle-reference["angle"],centre),
            }
            for name,pivot,lean in (
                    ("static_2026_3d","wheel_axle",0.),
                    ("wheel_axle_root_only","wheel_axle",0.),
                    ("wheel_axle_root_saddle_lean_minus15","wheel_axle",-15.),
                    ("wheel_axle_root_saddle_lean_plus15","wheel_axle",15.),
                    ("historical_midbody_root_only","historical_midbody",0.)):
                angle=0 if name=="static_2026_3d" else original_angle
                key=(name,angle)
                if key not in cached:
                    cached[key]=render(angle,pivot,lean)
                planes[name]=registered_mask4(cached[key],position,model_anchor)
            if set(planes)!=set(ARMS):
                raise ValueError("full original 24 tick model arm missing")
            for arm,image in planes.items():
                predictions[arm][tick]=image
        rows={}
        for name in ARMS:
            row=pooled_binary_metrics(source,predictions[name],TICKS)
            checked=pooled_binary_metrics(source,predictions[name],
                                          tuple(SELECTED[role]))
            if checked["pooled_iou"]!=PRIOR_EIGHT_TICK_POOLED[role][name]:
                raise ValueError("full 24-tick source replay fails frozen earlier eight-frame baseline")
            edges=[]
            change_source={}
            change_model={}
            for left,right in zip(TICKS,TICKS[1:]):
                orig=change_plane(source[left],source[right])
                pred=change_plane(predictions[name][left],predictions[name][right])
                change_source[left]=orig
                change_model[left]=pred
                m=metric(orig,pred)
                edges.append({
                    "real_original_Mesen_tick_edge":[left,right],
                    "source_changed_alpha_pixels":sum(orig),
                    "candidate_changed_alpha_pixels":sum(pred),
                    **m,
                })
            chronological=pooled_binary_metrics(
                change_source,change_model,TICKS[:-1])
            row["authentic_all_consecutive_edges"]={
                "source_observed_edge_count":len(edges),
                "original_source_edges_with_alpha_change":
                    sum(bool(x["source_changed_alpha_pixels"]) for x in edges),
                "candidate_edges_with_alpha_change":
                    sum(bool(x["candidate_changed_alpha_pixels"]) for x in edges),
                "actual_ordered_edge_metrics":edges,
                "pooled_change_support":chronological,
            }
            row["prior_eight_selected_original_source_frame_pooled_iou_verified"]={
                "actual_pooled_iou":checked["pooled_iou"],
                "expected_pooled_iou":PRIOR_EIGHT_TICK_POOLED[role][name]}
            rows[name]=row
        by_role[role]={
            "original_source_player":role,
            "source_original_tick1601_anchor_x2_y2":list(position),
            "source_original_first_tick_ROM_orientation_phase":[
                reference["angle"],reference["phase"]],
            "original_authentic_timeline_tick_range":[TICKS[0],TICKS[-1]],
            "all_original_exact_ROM_phase_orientation_by_tick":{
                str(tick):[frames[tick]["phase"],frames[tick]["angle"]]
                for tick in TICKS},
            "arms":rows,
        }
    return {
        "schema":SCHEMA,
        "original_ROM_SHA256":pose["original_usa_ROM_sha256"],
        "original_Mesen24_zip_SHA256":pose["original_Mesen24_source_archive_sha256"],
        "original_exact_phase_orientation_SHA256":hashlib.sha256(pose_raw).hexdigest(),
        "original_full_24x64_axis_SHA256":hashlib.sha256(axis_raw).hexdigest(),
        "provisional_original_7_6_camera_SHA256":hashlib.sha256(camera_raw).hexdigest(),
        "actual_source_authored_2026_GLb_SHA256":ptr["glb_sha256"],
        "source_authored_2026_SCAD_SHA256":SCAD_SHA,
        "original_24_no_skip_ticks_and_two_player_OAM_source":True,
        "original_source_held_OAM_local_not_red_completed_screen_reflection":True,
        "source_first_anchor_once_per_player_not_original_ground_contact":True,
        "original_1994_source_3D_saddle_angle_camera_mesh_recovered":False,
        "2026_owner_character_likeness_approved":False,
        "source_timeline_previously_examined_no_prospective_blind_holdout":True,
        "single_frozen_saddle_angle_per_arm_both_players_no_per_tick_fit":True,
        "all_48_original_source_observations":48,
        "model_actual_render_cache_entries":len(cached),
        "source_player_results":by_role,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--pose-report",type=Path,required=True)
    p.add_argument("--axis-report",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--verified-exports",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    record=audit(a.source_zip.read_bytes(),a.pose_report.read_bytes(),
                 a.axis_report.read_bytes(),a.camera.read_bytes(),
                 a.verified_exports)
    publish_text_once(a.out,json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("ART4K_REAL_GLB_ALL_ORIGINAL_MESEN24_SADDLE_TEMPORAL",
          json.dumps({role:{arm:{
              "silhouette":a["pooled_iou"],
              "upper":a["fixed_source_y_bands"]["upper_y0_14"]["pooled_iou"],
              "changed_pixels":a["authentic_all_consecutive_edges"]
                 ["pooled_change_support"]["pooled_iou"]}
              for arm,a in details["arms"].items()}
              for role,details in record["source_player_results"].items()},
              sort_keys=True))


if __name__=="__main__":
    main()
