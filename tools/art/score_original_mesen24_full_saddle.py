#!/usr/bin/env python3
"""Check real original 24-tick saddle-only 2026 rig against both racer sprites.

Original-source chronological and distinct 2D alpha groups are scored
separately. No inferred 1994 3D geometry, physical joint degrees or owner art.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.score_original_mesen24_fixed_pivot_glb import (
    check_receipts,read_original_roles,source_center,anchor,registered_mask4,
    rotate_source_2d,metric,fixed_source_y_band_metrics,sha,CAMERA_SHA,SCAD_SHA,
)
from tools.art.experimental_fixed_root_orbit import apply_root_scene
from tools.art.experimental_temporary_saddle_lean import temporary_saddle_pitch
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/1"
TICKS=tuple(range(1601,1625))
SADDLE_TRIALS=(("axle_root_saddle_neutral",0.),
               ("axle_root_saddle_plus15",15.),
               ("axle_root_saddle_minus15",-15.))
ARMS=("original_source_2d_rotation",)+tuple(x for x,_ in SADDLE_TRIALS)


def aggregate_original_timeline(rows:dict[int,dict],predictions:dict[int,dict[str,bytes]])->dict:
    """Keep temporal-frame and one-vote-per-unique-2D-source-shape distinct."""
    if (set(rows)!=set(TICKS) or set(predictions)!=set(TICKS) or
            any(set(predictions[t])!=set(ARMS) for t in TICKS)):
        raise ValueError("complete original 24-tick timeline and all candidate arms required")
    shapes={}
    for t in TICKS:
        original=rows[t]["alpha"]
        if type(original) is not bytes or len(original)!=4096 or set(original)-{0,1}:
            raise ValueError("original Mesen source alpha malformed")
        shapes.setdefault(sha(original),[]).append(t)
    outcome={}
    for arm in ARMS:
        scores={t:metric(rows[t]["alpha"],predictions[t][arm]) for t in TICKS}
        full={k:sum(score[k] for score in scores.values()) for k in ("tp","fp","fn")}
        unique_mean=[]
        for digest,times in shapes.items():
            unique_mean.append(sum(scores[t]["iou"] for t in times)/len(times))
        edge={}
        for previous,current in zip(TICKS[:-1],TICKS[1:]):
            source_edge=bytes(int(x!=y) for x,y in zip(
                rows[previous]["alpha"],rows[current]["alpha"]))
            candidate_edge=bytes(int(x!=y) for x,y in zip(
                predictions[previous][arm],predictions[current][arm]))
            edge[(previous,current)]=metric(source_edge,candidate_edge)
        sums={k:sum(v[k] for v in edge.values()) for k in ("tp","fp","fn")}
        outcome[arm]={
            "original_chronological_source_frame_count":len(TICKS),
            "original_unique_64px_binary_shape_count":len(shapes),
            "source_frame_pooled_alpha_iou":round(full["tp"]/sum(full.values()),8),
            "source_unique_shape_equal_vote_mean_alpha_iou":
                round(sum(unique_mean)/len(unique_mean),8),
            "source_actual_timeline_edge_count":len(edge),
            "source_actual_23_consecutive_edge_change_tp_fp_fn":sums,
            "source_actual_23_consecutive_edge_change_pooled_iou":
                round(sums["tp"]/sum(sums.values()),8)
                if sum(sums.values()) else 1.,
            "source_actual_23_consecutive_edge_change_mean_iou":
                round(sum(v["iou"] for v in edge.values())/len(edge),8),
            "source_chronological_full_alpha_tp_fp_fn":full,
            "per_original_chronological_edge":[
                {"source_ticks":[a,b],**edge[(a,b)]}
                for a,b in zip(TICKS[:-1],TICKS[1:])],
        }
    return {
        "original_unique_binary_source_alpha_shape_sha256_to_ticks":{
            key:values for key,values in sorted(shapes.items())},
        "arms":outcome,
    }


def analyze(zip_raw:bytes,pose_raw:bytes,axis_raw:bytes,
            camera_raw:bytes,verified_exports:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.render_racer_glb_projection import render_mask
    pose,axis,camera=check_receipts(zip_raw,pose_raw,axis_raw,camera_raw)
    if sha(camera_raw)!=CAMERA_SHA:
        raise ValueError("previous frozen original source camera SHA changed")
    originals=read_original_roles(zip_raw,pose,all_original_ticks=True)
    if any(set(rows)!=set(TICKS) for rows in originals.values()):
        raise ValueError("missing authentic 24 original PPU source snapshots")

    validate=runpy.run_path(str(Path(__file__).resolve().parent /
                               "model-review/stage_pages.py"))["validate"]
    pointer,outputs=validate(verified_exports,"upright")
    source=outputs["glb"].read_bytes()
    if (pointer["source_sha256"]!=SCAD_SHA or
            pointer["glb_sha256"]!=hashlib.sha256(source).hexdigest() or
            source[:4]!=b"glTF"):
        raise ValueError("same source-owned 2026 GLB success receipt changed")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)

    def model4(angle:int,lean:float):
        apply_root_scene(scene,angle,"wheel_axle",0.,0.)
        with temporary_saddle_pitch(scene,lean):
            world=(scene.to_geometry() if callable(
                getattr(scene,"to_geometry",None)) else scene.dump(concatenate=True))
            result=render_mask(np.asarray(world.vertices),np.asarray(world.faces),camera)
        return result.astype(bool)

    neutral=model4(0,0.)
    neutral_anchor=anchor(bytes(neutral[2::4,2::4].astype(np.uint8).ravel()))
    center=source_center(axis)
    if (center[0],center[1])!=(31.515625,19.578125):
        raise ValueError("the exact original even-only source 2D calibration changed")
    renders={}
    data={}
    for role,actual in originals.items():
        reference=actual[1601]
        original_anchor=anchor(reference["alpha"])
        predictions={}
        samples={}
        for t in TICKS:
            frame=actual[t]
            source_mask=frame["alpha"]
            arms={
                "original_source_2d_rotation":rotate_source_2d(
                    reference["alpha"],frame["angle"]-reference["angle"],center)
            }
            for name,lean in SADDLE_TRIALS:
                key=(frame["angle"],lean)
                if key not in renders:
                    renders[key]=model4(frame["angle"],lean)
                arms[name]=registered_mask4(renders[key],original_anchor,neutral_anchor)
            if set(arms)!=set(ARMS):
                raise ValueError("incomplete original 24-tick 2D/3D model controls")
            predictions[t]=arms
            samples[str(t)]={
                "source_true_original_Mesen_tick":t,
                "source_original_ROM_phase_index":frame["phase"],
                "source_original_ROM_orientation_index":frame["angle"],
                "source_opaque_64px_pixels":sum(source_mask),
                "source_2D_alpha_sha256":sha(source_mask),
                "source_actual_and_candidate_full_alpha":{
                    name:metric(source_mask,img) for name,img in arms.items()},
                "source_actual_and_candidate_fixed_y_bands":{
                    name:fixed_source_y_band_metrics(source_mask,img)
                    for name,img in arms.items()},
            }
        timeline=aggregate_original_timeline(actual,predictions)
        data[role]={
            "one_source_tick1601_lower_alpha_anchor_x2y2":list(original_anchor),
            "original_24_tick_samples":samples,
            **timeline,
        }
    return {
        "schema":SCHEMA,
        "source_exact_original_USA_ROM_sha256":pose["original_usa_ROM_sha256"],
        "source_exact_original_Mesen24_archive_sha256":sha(zip_raw),
        "source_exact_ROM_phase_orientation_report_sha256":sha(pose_raw),
        "source_exact_64_angle_report_sha256":sha(axis_raw),
        "source_unchanged_7_6_camera_sha256":sha(camera_raw),
        "current_source_authored_2026_SCAD_sha256":SCAD_SHA,
        "current_successful_2026_16_material_GLB_sha256":pointer["glb_sha256"],
        "source_original_timeline_ticks":[1601,1624],
        "source_each_player_has_all_24_consecutive_original_PPU_images":True,
        "source_orientation_to_root_angle_is_uncalibrated_2026_hypothesis":True,
        "2026_saddle_only_constant_degrees_both_players_all_ticks":[0.,15.,-15.],
        "2026_frame_fork_wheel_geometry_camera_and_mount_unchanged":True,
        "source_unique_binary_silhouettes_grouped_without_duplicate_vote_weight":True,
        "source_actual_timeline_motion_distinct_from_repeated_static_shapes":True,
        "source_viewpoint_families_are_known_NOT_prospective_blind":True,
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered":False,
        "owner_2026_character_art_likeness_approved":False,
        "real_2026_GLb_unique_model_pose_renders_cached":len(renders),
        "original_source_per_role":data,
    }


def summary_for_exact_original_source(record:dict)->dict:
    """Read-only original 48-frame results independent of variable GLB bytes."""
    if (not isinstance(record,dict) or record.get("schema")!=SCHEMA or
            set(record.get("original_source_per_role",{}))!={"blue","red"}):
        raise ValueError("complete real original Mesen source/model report required")
    result={}
    for role,entry in record["original_source_per_role"].items():
        if (set(entry.get("arms",{}))!=set(ARMS) or
                set(entry.get("original_24_tick_samples",{}))!={str(t) for t in TICKS}):
            raise ValueError("all 24 authentic original ticks and candidate arms required")
        result[role]={}
        for arm,entry in entry["arms"].items():
            if (entry.get("original_chronological_source_frame_count")!=24 or
                    entry.get("source_actual_timeline_edge_count")!=23):
                raise ValueError("genuine source 24-frame/23-edge chronology required")
            result[role][arm]={
                "unique_shapes":entry["original_unique_64px_binary_shape_count"],
                "chronological_pooled_iou":entry["source_frame_pooled_alpha_iou"],
                "unique_shape_equal_vote_mean_iou":
                    entry["source_unique_shape_equal_vote_mean_alpha_iou"],
                "real_23_tick_edge_change_pooled_iou":
                    entry["source_actual_23_consecutive_edge_change_pooled_iou"],
            }
    return result


def check_exact_source_evidence(record:dict,evidence:dict)->None:
    """Detect drift from one actual original ROM and authored-GLB run.

    The GLB file SHA may vary, but source OpenSCAD SHA and exact exporter
    receipt must remain verified by analyze() before calling this helper.
    """
    if (not isinstance(evidence,dict) or
            evidence.get("schema")!="UR-ART4K-EXACT-ORIGINAL-MESEN24-SADDLE-TEMPORAL-EVIDENCE/1"):
        raise ValueError("wrong original Mesen24 saddle temporal evidence schema")
    source=evidence.get("producer",{})
    checks={
        "original_Mesen24_archive_sha256":record.get("source_exact_original_Mesen24_archive_sha256"),
        "original_pose_report_sha256":record.get("source_exact_ROM_phase_orientation_report_sha256"),
        "original_axis_sha256":record.get("source_exact_64_angle_report_sha256"),
        "provisional_camera_sha256":record.get("source_unchanged_7_6_camera_sha256"),
        "current_2026_authored_SCAD_sha256":record.get("current_source_authored_2026_SCAD_sha256"),
    }
    if any(source.get(key)!=value or type(value) is not str or len(value)!=64
           for key,value in checks.items()):
        raise ValueError("original source/2026 model provenance changed")
    if (source.get("original_1994_physical_3d_model_or_camera_recovered") is not False or
            source.get("original_art_likeness_approved") is not False or
            record.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False or
            record.get("owner_2026_character_art_likeness_approved") is not False):
        raise ValueError("original 3D/art likeness cannot be awarded by this experiment")
    if summary_for_exact_original_source(record)!=evidence.get("reported_per_role"):
        raise ValueError("actual original 48-frame saddle shape/motion scores drifted")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--pose-report",required=True,type=Path)
    p.add_argument("--axis-report",required=True,type=Path)
    p.add_argument("--camera",required=True,type=Path)
    p.add_argument("--verified-exports",required=True,type=Path)
    p.add_argument("--expected-summary",type=Path,
                   help="SHA-bound prior executed original source/GLB baseline")
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=analyze(a.source_zip.read_bytes(),a.pose_report.read_bytes(),
                   a.axis_report.read_bytes(),a.camera.read_bytes(),a.verified_exports)
    if a.expected_summary is not None:
        check_exact_source_evidence(result,json.loads(a.expected_summary.read_text()))
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("OK ART4K_REAL_2026_SADDLE_ALL24_SOURCE_MOTION",
          json.dumps({role:{arm:{
                k:v for k,v in score.items() if k in (
                    "source_frame_pooled_alpha_iou",
                    "source_unique_shape_equal_vote_mean_alpha_iou",
                    "original_unique_64px_binary_shape_count",
                    "source_actual_23_consecutive_edge_change_pooled_iou")}
                    for arm,score in rec["arms"].items()}
                    for role,rec in result["original_source_per_role"].items()},
                     sort_keys=True))


if __name__=="__main__":
    main()
