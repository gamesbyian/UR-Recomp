#!/usr/bin/env python3
"""Unweighted multi-objective diagnostics for actual original Mesen24 vs one GLB.

No image/mesh fitting or per-player choice. Every 2026 candidate is scored
jointly on two real source racers, 24 shapes, distinct shape votes and their
23 genuinely consecutive original change edges. The source-only rigid 2D
rotation is a separate comparator and never misidentified as a GLB.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-REAL-GLB-TWO-PLAYER-SIX-OBJECTIVE-PARETO/1"
SOURCE_SCHEMA="UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/3"
ROLES=("blue","red")
METRICS=(
    "source_frame_pooled_alpha_iou",
    "source_unique_shape_equal_vote_mean_alpha_iou",
    "source_actual_23_consecutive_edge_change_pooled_iou",
)
OBJECTIVES=tuple(f"{role}:{metric}" for role in ROLES for metric in METRICS)
ORIGINAL_2D_NULL="original_source_2d_rotation"
SOURCE_PINS={
    "source_exact_original_USA_ROM_sha256":
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
    "source_exact_original_Mesen24_archive_sha256":
        "28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6",
    "source_unchanged_7_6_camera_sha256":
        "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028",
    "current_source_authored_2026_SCAD_sha256":
        "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984",
}
BANDS=("upper_y0_14","middle_y15_26","lower_y27_63")


def score_row(entry:dict)->tuple[float,float,float]:
    if (not isinstance(entry,dict) or
            entry.get("original_chronological_source_frame_count")!=24 or
            entry.get("source_actual_timeline_edge_count")!=23 or
            type(entry.get("original_unique_64px_binary_shape_count")) is not int or
            not 1<=entry["original_unique_64px_binary_shape_count"]<=24):
        raise ValueError("exact original 24-frame/23-edge source GLB row required")
    vals=[]
    for key in METRICS:
        value=entry.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError("all original 2026 shape and motion scores must be finite 0..1")
        vals.append(float(value))
    counts=entry.get("source_actual_23_consecutive_edge_change_tp_fp_fn")
    if (not isinstance(counts,dict) or set(counts)!={"tp","fp","fn"} or
            any(type(v) is not int or v<0 for v in counts.values())):
        raise ValueError("conserved original source motion TP/FP/FN required")
    d=sum(counts.values())
    expected=round(counts["tp"]/d,8) if d else 1.
    if abs(expected-vals[-1])>0.000000011:
        raise ValueError("original 23-edge motion IoU disagrees with genuine pixel census")
    bands=entry.get("source_actual_23_consecutive_edge_change_fixed_y_bands")
    if not isinstance(bands,dict) or set(bands)!=set(BANDS):
        raise ValueError("all three fixed original 64px source-motion bands required")
    sums={key:0 for key in ("tp","fp","fn")}
    for key in BANDS:
        row=bands[key]
        v=row.get("tp_fp_fn") if isinstance(row,dict) else None
        if (not isinstance(v,dict) or set(v)!=set(sums)
                or any(type(v[k]) is not int or v[k]<0 for k in sums)
                or row.get("source_chronological_edge_count")!=23):
            raise ValueError("original per-band source chronological counts invalid")
        for k in sums:
            sums[k]+=v[k]
    if sums!=counts:
        raise ValueError("source-image bands must exactly partition original changing pixels")
    return tuple(vals)


def dominates(a:tuple[float,...],b:tuple[float,...])->bool:
    """Strict Pareto dominance, without weights, role-switching or tolerance."""
    if len(a)!=len(OBJECTIVES) or len(b)!=len(OBJECTIVES):
        raise ValueError("two racers × three source metrics required")
    return all(x>=y for x,y in zip(a,b)) and any(x>y for x,y in zip(a,b))


def analyze(report:dict)->dict:
    if (not isinstance(report,dict) or report.get("schema")!=SOURCE_SCHEMA or
            set(report.get("original_source_per_role",{}))!=set(ROLES) or
            report.get("source_original_timeline_ticks")!=[1601,1624] or
            report.get("source_each_player_has_all_24_consecutive_original_PPU_images") is not True or
            report.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False or
            report.get("owner_2026_character_art_likeness_approved") is not False or
            any(report.get(k)!=v for k,v in SOURCE_PINS.items())):
        raise ValueError("unchanged exact original ROM/Mesen24/camera/2026 GLB source provenance required")
    source=report["original_source_per_role"]
    arm_sets=[]
    for role in ROLES:
        role_data=source[role]
        if (not isinstance(role_data,dict) or
                set(role_data.get("original_24_tick_samples",{}))!={str(t) for t in range(1601,1625)} or
                not isinstance(role_data.get("arms"),dict)):
            raise ValueError("one complete authentic 24-tick source role required")
        arm_sets.append(set(role_data["arms"]))
    if arm_sets[0]!=arm_sets[1] or ORIGINAL_2D_NULL not in arm_sets[0]:
        raise ValueError("same original image controls must be scored for both players")
    glb_arms=sorted(arm_sets[0]-{ORIGINAL_2D_NULL})
    if not glb_arms or any(not name.startswith("axle_root_") for name in glb_arms):
        raise ValueError("real 2026 GLB experiment arms must be named and complete")
    scores={}
    for arm in sorted(arm_sets[0]):
        scores[arm]=tuple(v for role in ROLES for v in score_row(source[role]["arms"][arm]))
    dominance={}
    for arm in glb_arms:
        dominance[arm]=sorted(x for x in glb_arms if x!=arm and dominates(scores[x],scores[arm]))
    nondominated=[arm for arm in glb_arms if not dominance[arm]]
    # A numerical gain in static silhouette cannot erase temporal regressions:
    # the complete six-coordinate vector is always preserved with every arm.
    return {
        "schema":SCHEMA,
        "authentic_original_source_pins":SOURCE_PINS,
        "original_image_player_roles":list(ROLES),
        "objectives_all_maximize":list(OBJECTIVES),
        "retrospective_source_no_prospective_holdout":True,
        "source_image_2D_null_excluded_from_real_GLB_pareto_but_reported":True,
        "original_1994_3D_camera_mesh_or_joint_recovered":False,
        "owner_art_likeness_approved":False,
        "candidate_2026_GLB_arm_count":len(glb_arms),
        "pareto_nondominated_2026_GLB_arms":nondominated,
        "per_2026_GLB_arm":{
            arm:{
                "source_six_objective_values":list(scores[arm]),
                "strictly_dominated_by_2026_GLB_arms":dominance[arm],
                "is_nondominated":not bool(dominance[arm]),
            }
            for arm in glb_arms
        },
        "separate_original_source_2D_rotation_null_six_objective_values":
            list(scores[ORIGINAL_2D_NULL]),
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--real-glb-source-report",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=analyze(json.loads(a.real_glb_source_report.read_bytes()))
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ART4K_REAL_GLB_SOURCE_SIX_OBJECTIVE_PARETO",
          json.dumps({"nondominated":result["pareto_nondominated_2026_GLB_arms"],
                      "candidates":result["candidate_2026_GLB_arm_count"]},sort_keys=True))


if __name__=="__main__":
    main()
