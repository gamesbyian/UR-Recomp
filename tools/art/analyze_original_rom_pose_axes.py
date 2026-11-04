#!/usr/bin/env python3
"""ROM-exact two-axis source-pose causal counterfactual; not a 3D reconstruction.

A 24x64 source frame is composed by a source phase and an orientation/angle
index. Compare both 2x2 path orders at two *already observed* Mesen source
events without fitting a camera, geometry or continuous 3D joint angles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.recover_original_mesen24_rom_pose_ids import (
    source_frame_tiles,render_original_primary_sprite64,ROM_SHA
)

SCHEMA="UR-ART4K-ORIGINAL-ROM-24PHASE-64ANGLE-AXIS-COUNTERFACTUAL/1"
SOURCE_POSE_REPORT_SHA="6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20"
# Exact original source events discovered in *already inspected* 24-tick Mesen
# observations. Do not promote them to prospective holdout experiments.
EVENTS={"blue":(1602,1603,4,14),"red":(1605,1606,5,15)}
LIVE_ANGLES=(57,58,60,61)


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def changed(source:bytes,candidate:bytes,lo:int,hi:int)->dict:
    if (len(source)!=4096 or len(candidate)!=4096 or
            not 0<=lo<=hi<64):
        raise ValueError("exact original 64x64 4bpp planes and inclusive Y band required")
    i=range(lo*64,(hi+1)*64)
    colour=sum(source[n]!=candidate[n] for n in i)
    alpha=sum(bool(source[n])!=bool(candidate[n]) for n in i)
    opaque=sum(source[n]!=candidate[n] and source[n]!=0 and candidate[n]!=0 for n in i)
    if colour!=alpha+opaque:
        raise ValueError("source original index/alpha partition does not add up")
    return {"index4bpp_changed_pixels":colour,
            "alpha_xor_pixels":alpha,
            "shared_opaque_index_changed_pixels":opaque}


def score(source:bytes,target:bytes,top_lo:int,top_hi:int)->dict:
    # Source-observed envelope is in source-local 64px coordinates.
    # Outside the original envelope may still contain an authored candidate
    # at unusual original angle states, hence include full range too.
    return {
        "whole_64px":changed(source,target,0,63),
        "observed_source_upper_third":changed(source,target,top_lo,top_hi),
        "source_y_0_15":changed(source,target,0,15),
    }


def bbox(index_pixels:set[int])->list[int]|None:
    if not index_pixels:
        return None
    return [min(i%64 for i in index_pixels),min(i//64 for i in index_pixels),
            max(i%64 for i in index_pixels),max(i//64 for i in index_pixels)]


def audit(rom:bytes,pose_report_raw:bytes)->dict:
    if len(rom)!=2*1024*1024 or sha(rom)!=ROM_SHA:
        raise ValueError("wrong authenticated original USA ROM")
    if sha(pose_report_raw)!=SOURCE_POSE_REPORT_SHA:
        raise ValueError("wrong authenticated actual Mesen24/ROM frame-ID report")
    source=json.loads(pose_report_raw)
    if not source["all_48_original_64x64_source_index_images_pixel_exact_from_ROM"]:
        raise ValueError("independent original source sprite oracle absent")
    candidates=source_frame_tiles(rom)
    sprites=tuple(render_original_primary_sprite64(row) for row in candidates)
    def sprite(p:int,a:int)->bytes:
        if not(0<=p<24 and 0<=a<64):
            raise ValueError("outside original 24x64 source presentation manifold")
        return sprites[p*64+a]
    angle_variation={}
    for a in LIVE_ANGLES:
        fixed=sprite(0,a)
        variation={n for p in range(1,24) for n,(x,y) in
                   enumerate(zip(fixed,sprite(p,a))) if x!=y}
        variation_alpha={n for p in range(1,24) for n,(x,y) in
                   enumerate(zip(fixed,sprite(p,a))) if bool(x)!=bool(y)}
        angle_variation[str(a)]={
            "distinct_source_index_positions_across_24_phase_states":len(variation),
            "distinct_source_alpha_positions_across_24_phase_states":len(variation_alpha),
            "source_index_variant_region_bbox_xyxy":bbox(variation),
            "index_pixels_in_y_0_15_change_as_phase_varies":
                sum(n//64<=15 for n in variation),
        }
        if angle_variation[str(a)]["index_pixels_in_y_0_15_change_as_phase_varies"]!=0:
            raise ValueError("source upper invariance differs at live angle")
    events={}
    for who,(tick0,tick1,top_lo,top_hi) in EVENTS.items():
        frames={r["authentic_original_bridge_tick"]:r
                for r in source["per_original_source_racer"][who][
                    "source_24_unique_per_tick_ROM_primary_frame_IDs"]}
        row0,row1=frames[tick0],frames[tick1]
        p0,a0=row0["source_primary_phase_index"],row0["source_primary_angle_index"]
        p1,a1=row1["source_primary_phase_index"],row1["source_primary_angle_index"]
        before=sprite(p0,a0)
        after=sprite(p1,a1)
        if (sha(before)!=row0["source_held_OAM_local_index_plane_sha256"] or
                sha(after)!=row1["source_held_OAM_local_index_plane_sha256"]):
            raise ValueError("not exact original observed PPU index plane at event")
        phase_then=sprite(p1,a0)
        angle_then=sprite(p0,a1)
        actual=score(before,after,top_lo,top_hi)
        a_phase=score(before,phase_then,top_lo,top_hi)
        a_angle=score(phase_then,after,top_lo,top_hi)
        b_angle=score(before,angle_then,top_lo,top_hi)
        b_phase=score(angle_then,after,top_lo,top_hi)
        def upper(record):return record["observed_source_upper_third"]
        for phase_step in (a_phase,b_phase):
            if any(upper(phase_step).values()):
                raise ValueError("source upper phase-only event unexpectedly changes")
        for angle_step in (a_angle,b_angle):
            if upper(angle_step)!=upper(actual):
                raise ValueError("source upper original event is not angle-index-only")
        events[who]={
            "actual_original_ticks":[tick0,tick1],
            "original_24phase_64angle_before":[p0,a0],
            "original_24phase_64angle_after":[p1,a1],
            "original_source_upper_observed_y_inclusive":[top_lo,top_hi],
            "actual_original_index_delta":actual,
            "phase_first_then_angle":{
                "hold_angle_change_phase":a_phase,
                "hold_final_phase_change_angle":a_angle},
            "angle_first_then_phase":{
                "hold_phase_change_angle":b_angle,
                "hold_final_angle_change_phase":b_phase},
            "source_upper_change_independent_of_phase_order":True,
            "source_original_event_in_previously_inspected_series":True,
        }
    # Across all 64 angle states, the phase-controlled part may orbit high
    # in image Y; report this instead of falsely claiming global fixed upper.
    phase_variants=set()
    per_angle_bbox={}
    for a in range(64):
        fixed=sprite(0,a)
        changing={n for p in range(1,24) for n,(x,y) in
                  enumerate(zip(fixed,sprite(p,a))) if x!=y}
        phase_variants.update(changing)
        per_angle_bbox[str(a)]=bbox(changing)
    return {
        "schema":SCHEMA,
        "original_authenticated_USA_ROM_sha256":ROM_SHA,
        "exact_authenticated_original_48_frame_pose_report_sha256":SOURCE_POSE_REPORT_SHA,
        "original_ROM_24phase_64angle_exact_source_frame_count":1536,
        "original_observed_source_event_counterfactuals_are_retrospective":True,
        "original_source_2d_phase_axis_independent_of_3d_rig_physical_spin":True,
        "source_phase_variation_positions_any_angle_count":len(phase_variants),
        "source_phase_variation_all_angles_bbox_xyxy":bbox(phase_variants),
        "source_phase_variation_bbox_by_ROM_angle_index":per_angle_bbox,
        "source_phase_variation_by_actually_observed_ROM_angle":angle_variation,
        "two_original_upper_source_events":events,
        "original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered":False,
        "original_2026_rig_likeness_owner_approved":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",required=True,type=Path)
    p.add_argument("--exact-pose-report",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=audit(args.rom.read_bytes(),args.exact_pose_report.read_bytes())
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "actual_event_top_index":{
            who:ev["actual_original_index_delta"]["observed_source_upper_third"][
                "index4bpp_changed_pixels"]
            for who,ev in result["two_original_upper_source_events"].items()},
        "all_four_observed_angle_states_phase_invariant_y0_15":True,
        "phase_variation_all_angles_bbox_xyxy":
            result["source_phase_variation_all_angles_bbox_xyxy"]
    },sort_keys=True))


if __name__=="__main__":
    main()
