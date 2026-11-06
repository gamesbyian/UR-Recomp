#!/usr/bin/env python3
"""Exact-source, no-render, 24-frame/23-edge model-motion sensitivity audit.

Original USA Mesen24 source images are *2D*. This does not discover original
3D geometry, camera, material ownership, drive speed or physically true joints.
Only compare two fully predeclared 2026 GLB projection arms from the same run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.rank_real_glb_mesen24_pareto import SOURCE_SCHEMA, SOURCE_PINS

SCHEMA="UR-ART4K-ORIGINAL-MESEN24-EDGE-SENSITIVITY/1"
ROLES=("blue","red")
TICKS=tuple(range(1601,1625))
COUNT_KEYS=("tp","fp","fn")


def tally(row:dict)->tuple[int,int,int]:
    if not isinstance(row,dict):
        raise ValueError("authentic source change pixel census required")
    values=tuple(row.get(k) for k in COUNT_KEYS)
    if any(type(v) is not int or v<0 for v in values):
        raise ValueError("nonnegative exact original source TP/FP/FN required")
    return values


def pooled(rows)->float:
    tp,fp,fn=(sum(r[k] for r in rows) for k in COUNT_KEYS)
    return round(tp/(tp+fp+fn),8) if tp+fp+fn else 1.


def validate_edges(entries:dict,arm:str)->list[dict]:
    row=entries["arms"].get(arm)
    if not isinstance(row,dict) or row.get("original_chronological_source_frame_count")!=24 or row.get("source_actual_timeline_edge_count")!=23:
        raise ValueError("all 24 original source frames and 23 actual edges required")
    seq=row.get("per_original_chronological_edge")
    if not isinstance(seq,list) or len(seq)!=23:
        raise ValueError("all 23 chronological original Mesen24 transitions required")
    totals={k:0 for k in COUNT_KEYS}
    for i,edge in enumerate(seq):
        if edge.get("source_ticks")!=[TICKS[i],TICKS[i+1]]:
            raise ValueError("only genuinely adjacent source Mesen ticks accepted")
        t=tally(edge)
        for k,v in zip(COUNT_KEYS,t):
            totals[k]+=v
        if (type(edge.get("iou")) not in (float,int) or
                not math.isfinite(edge["iou"]) or
                abs(edge["iou"]-(round(t[0]/sum(t),8) if sum(t) else 1.))>1e-8):
            raise ValueError("source chronological edge IoU disagrees with original changed pixels")
    if totals!=row.get("source_actual_23_consecutive_edge_change_tp_fp_fn"):
        raise ValueError("23 original temporal edge confusion totals not conserved")
    if pooled(seq)!=row.get("source_actual_23_consecutive_edge_change_pooled_iou"):
        raise ValueError("pooled actual original Mesen24 edge IoU drifted")
    return seq


def analyze(raw:bytes,expected_sha:str,pairs:tuple[tuple[str,str],...])->dict:
    if (not isinstance(raw,bytes) or type(expected_sha) is not str
            or len(expected_sha)!=64 or
            hashlib.sha256(raw).hexdigest()!=expected_sha):
        raise ValueError("exact immutable source report SHA256 required")
    if (not isinstance(pairs,tuple) or not pairs or
            any(type(p) is not tuple or len(p)!=2 or
                any(type(n) is not str or not n.startswith("axle_root_")
                    for n in p) or p[0]==p[1] for p in pairs) or
            len(set(pairs))!=len(pairs)):
        raise ValueError("frozen, unique pair of genuine GLB model controls required")
    report=json.loads(raw)
    if (report.get("schema")!=SOURCE_SCHEMA or
            any(report.get(k)!=v for k,v in SOURCE_PINS.items()) or
            report.get("source_original_timeline_ticks")!=[1601,1624] or
            report.get("source_each_player_has_all_24_consecutive_original_PPU_images") is not True or
            report.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False or
            report.get("owner_2026_character_art_likeness_approved") is not False or
            set(report.get("original_source_per_role",{}))!=set(ROLES)):
        raise ValueError("same verified original-USA Mesen24 source, provisional camera and 2026 GLB required")
    observed={}
    for role in ROLES:
        record=report["original_source_per_role"][role]
        frames=record.get("original_24_tick_samples",{})
        if set(frames)!={str(t) for t in TICKS}:
            raise ValueError("all 24 original source PPU frames required for static audit")
        for i,tick in enumerate(TICKS):
            item=frames[str(tick)]
            if (item.get("source_true_original_Mesen_tick")!=tick or
                    type(item.get("source_opaque_64px_pixels")) is not int or
                    not 0<item["source_opaque_64px_pixels"]<=4096 or
                    type(item.get("source_2D_alpha_sha256")) is not str or
                    len(item["source_2D_alpha_sha256"])!=64):
                raise ValueError("original no-skip source frame identity or area altered")
        role_pairs={}
        for candidate,control in pairs:
            left=validate_edges(record,candidate)
            right=validate_edges(record,control)
            per_edge=[]
            for i,(a,b) in enumerate(zip(left,right)):
                ap=tally(a);bp=tally(b)
                if ap[0]+ap[2]!=bp[0]+bp[2]:
                    raise ValueError("same original changed pixels required for paired model arms")
                without_left=left[:i]+left[i+1:]
                without_right=right[:i]+right[i+1:]
                delta=round(pooled(left)-pooled(right),8)
                delta_without=round(pooled(without_left)-pooled(without_right),8)
                per_edge.append({
                    "original_source_ticks":[TICKS[i],TICKS[i+1]],
                    "original_source_changed_binary_pixels":ap[0]+ap[2],
                    "candidate_2026_tp_fp_fn":dict(zip(COUNT_KEYS,ap)),
                    "control_2026_tp_fp_fn":dict(zip(COUNT_KEYS,bp)),
                    "candidate_minus_control_tp_fp_fn":dict(zip(COUNT_KEYS,(x-y for x,y in zip(ap,bp)))),
                    "per_edge_iou_delta":round(a["iou"]-b["iou"],8),
                    "leave_this_original_edge_out_pooled_delta":delta_without,
                    "this_edge_influence_on_pooled_delta":round(delta-delta_without,8),
                })
            per_tick=[]
            for tick in TICKS:
                item=frames[str(tick)]
                comps=item.get("source_actual_and_candidate_full_alpha",{})
                if not isinstance(comps,dict) or any(n not in comps for n in (candidate,control)):
                    raise ValueError("same two model controls required for all original static frames")
                a,b=comps[candidate],comps[control]
                for entry in (a,b):
                    tp,fp,fn=tally(entry)
                    expected=round(tp/(tp+fp+fn),8) if tp+fp+fn else 1.
                    if (tp+fn!=item["source_opaque_64px_pixels"] or
                            type(entry.get("iou")) not in (float,int) or
                            abs(entry["iou"]-expected)>1e-8):
                        raise ValueError("original static source pixel census mismatch")
                per_tick.append({
                    "original_source_tick":tick,
                    "candidate_minus_control_static_iou":round(a["iou"]-b["iou"],8),
                    "candidate_minus_control_opaque_tp":a["tp"]-b["tp"],
                    "candidate_minus_control_opaque_fp":a["fp"]-b["fp"],
                })
            per_edge_sorted=sorted(per_edge,key=lambda x:(x["this_edge_influence_on_pooled_delta"],x["original_source_ticks"][0]))
            role_pairs[candidate+"::"+control]={
                "candidate":candidate,"control":control,
                "original_static_frame_count":24,
                "true_source_chronological_edge_count":23,
                "candidate_pooled_actual_original_motion_iou":pooled(left),
                "control_pooled_actual_original_motion_iou":pooled(right),
                "pooled_motion_iou_candidate_minus_control":round(pooled(left)-pooled(right),8),
                "per_original_frame_static_iou_wins":sum(x["candidate_minus_control_static_iou"]>0 for x in per_tick),
                "per_original_frame_static_iou_losses":sum(x["candidate_minus_control_static_iou"]<0 for x in per_tick),
                "per_original_frame_static_iou_ties":sum(x["candidate_minus_control_static_iou"]==0 for x in per_tick),
                "per_actual_original_temporal_edge_iou_wins":sum(x["per_edge_iou_delta"]>0 for x in per_edge),
                "per_actual_original_temporal_edge_iou_losses":sum(x["per_edge_iou_delta"]<0 for x in per_edge),
                "per_actual_original_temporal_edge_iou_ties":sum(x["per_edge_iou_delta"]==0 for x in per_edge),
                "largest_negative_influence_original_edges":per_edge_sorted[:3],
                "largest_positive_influence_original_edges":per_edge_sorted[-3:][::-1],
                "all_23_original_consecutive_edge_deltas":per_edge,
                "all_24_original_static_frame_deltas":per_tick,
            }
        observed[role]=role_pairs
    return {
        "schema":SCHEMA,
        "real_authenticated_source_report_sha256":expected_sha,
        "source_USA_ROM_Mesen24_provisional_camera_and_2026_SCAD_hashes":SOURCE_PINS,
        "original_1994_3D_mesh_camera_or_joint_recovered":False,
        "owner_2026_character_likeness_approved":False,
        "source_image_rows_are_not_1994_anatomical_parts":True,
        "retrospective_original_source_not_prospective_blind_holdout":True,
        "pooled_motion_sensitivity_is_diagnostic_not_permission_to_drop_difficult_frames":True,
        "two_original_racers":list(ROLES),
        "role_matched_source_edge_diagnostics":observed,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-report",type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--pair",nargs=2,action="append",metavar=("CANDIDATE","CONTROL"),
                   required=True,help="exact same-source 2026 GLB model arms")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    raw=args.source_report.read_bytes()
    result=analyze(raw,args.expected_sha256,tuple(tuple(p) for p in args.pair))
    publish_text_once(args.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ART4K_ORIGINAL_MESEN24_EDGE_SENSITIVITY",
          json.dumps({role:{name:{
              "edge_delta":pair["pooled_motion_iou_candidate_minus_control"],
              "static_wins":pair["per_original_frame_static_iou_wins"],
              "motion_edge_losses":pair["per_actual_original_temporal_edge_iou_losses"]}
              for name,pair in rows.items()}
              for role,rows in result["role_matched_source_edge_diagnostics"].items()},
                     sort_keys=True))


if __name__=="__main__":
    main()
