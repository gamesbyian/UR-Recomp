#!/usr/bin/env python3
"""Attribute real 2026 GLB parts in four authentic upper-motion ROM sprites.

One current-success 16-material GLB, frozen 7:6 camera, two existing root
controls, no per-frame alignment/geometry search, no 1994 anatomy claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.count_real_glb_parent_source_y_bands import (
    PARTS, SOURCE_SCAD_SHA, CAMERA_SHA, SOURCE_Y_BANDS,
    CANONICAL_TOTAL, CANONICAL_PARTS, count_parts, scene_part_source_masks,
)
from tools.art.score_original_mesen24_fixed_pivot_glb import (
    check_receipts, read_original_roles, reference_relative_index,
    source_center, rotate_source_2d, anchor, registered_mask4, metric, sha,
)
from tools.art.experimental_fixed_root_orbit import apply_root_scene
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-MESEN-UPPER-MOTION-REAL-2026-PARENT-ATTRIBUTION/1"
# Even-orientation (0,2,...,62) source bbox centre; the full 64-state
# vertical centre is 19.5859375 and is deliberately NOT interchangeable.
FROZEN_EVEN_SOURCE_CENTRE=(31.515625,19.578125)
UPPER_EVENTS={"blue":(1602,1603),"red":(1605,1606)}
ARMS=("absolute_wheel_axle_root","reference_relative_midbody_root")


def union_planes(part_masks:dict[str,bytes])->bytes:
    """Every 2026 projected parent is credited to the same full alpha union."""
    if (not isinstance(part_masks,dict) or set(part_masks)!=set(PARTS) or
            any(type(m) is not bytes or len(m)!=4096 or set(m)-{0,1}
                for m in part_masks.values())):
        raise ValueError("five aligned binary original-64px model-part masks required")
    return bytes(int(any(part_masks[p][k] for p in PARTS)) for k in range(4096))


def attribute_bands(source:bytes,part_masks:dict[str,bytes])->dict:
    """Exclusive/overlap source-image evidence, never invented part ownership.

    Source positives missed by all parts are *unassigned*. A source pixel
    covered by two different 2026 parent projections is ambiguous, not
    automatically attributed to whichever part a particular material names.
    """
    if type(source) is not bytes or len(source)!=4096 or set(source)-{0,1}:
        raise ValueError("genuine binary 64px original source alpha required")
    union=union_planes(part_masks)
    out={}
    for name,low,high in SOURCE_Y_BANDS:
        indices=range(low*64,(high+1)*64)
        baseline=metric(source[low*64:(high+1)*64].ljust(4096,b"\0"),
                        union[low*64:(high+1)*64].ljust(4096,b"\0"))
        source_xy=[(k%64,k//64) for k in indices if source[k]]
        candidate_xy=[(k%64,k//64) for k in indices if union[k]]
        def cx(coords):
            return round(sum(x for x,_ in coords)/len(coords),6) if coords else None
        part_metrics={}
        for part in PARTS:
            occupied=[k for k in indices if part_masks[part][k]]
            exclusive=[k for k in occupied if sum(
                part_masks[p][k] for p in PARTS)==1]
            part_metrics[part]={
                "projected_pixels":len(occupied),
                "projected_centroid_source_x":cx([(k%64,k//64) for k in occupied]),
                "exclusive_union_pixels":len(exclusive),
                "exclusive_true_positive_source_pixels":sum(source[k] for k in exclusive),
                "exclusive_false_positive_source_pixels":sum(not source[k] for k in exclusive),
                "ambiguous_2d_overlapping_parent_pixels":len(occupied)-len(exclusive),
                "possible_true_positive_with_overlaps":sum(source[k] for k in occupied),
            }
        seen=[sum(part_masks[p][k] for p in PARTS) for k in indices]
        ambiguous=sum(v>1 for v in seen)
        out[name]={
            "source_opaque_pixels":len(source_xy),
            "source_opaque_centroid_x":cx(source_xy),
            "candidate_opaque_centroid_x":cx(candidate_xy),
            "model_union_pixels":len(candidate_xy),
            "model_union_alpha_tp_fp_fn":{k:baseline[k] for k in ("tp","fp","fn")},
            "model_union_iou":baseline["iou"],
            "model_ambiguous_overlapping_parent_pixels":ambiguous,
            "source_opaque_pixels_missing_all_2026_parts":
                sum(source[k] and not union[k] for k in indices),
            "per_2026_parent":part_metrics,
        }
        assert sum(x["exclusive_union_pixels"] for x in part_metrics.values())+ambiguous==len(candidate_xy)
        assert baseline["tp"]+baseline["fp"]==len(candidate_xy)
        assert baseline["tp"]+baseline["fn"]==len(source_xy)
    return out


def analyze(source_zip:bytes,pose_raw:bytes,axis_raw:bytes,
            camera_raw:bytes,verified_exports:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.render_racer_glb_projection import render_mask
    from tools.art.count_real_glb_parent_source_y_bands import sha as checksum
    pose,axis,camera=check_receipts(source_zip,pose_raw,axis_raw,camera_raw)
    if sha(camera_raw)!=CAMERA_SHA:
        raise ValueError("frozen 7:6 source camera provenance mismatch")
    src=read_original_roles(source_zip,pose)
    validate=runpy.run_path(str(Path(__file__).resolve().parent /
                              "model-review/stage_pages.py"))["validate"]
    pointer,files=validate(verified_exports,"upright")
    model=files["glb"].read_bytes()
    if (pointer["source_sha256"]!=SOURCE_SCAD_SHA or
            pointer["glb_sha256"]!=checksum(model) or model[:4]!=b"glTF"):
        raise ValueError("original 2026 authored model export not authenticated")
    scene=trimesh.load(files["glb"],file_type="glb",force="scene",process=False)
    neutral=scene_part_source_masks(scene,camera)
    census=count_parts(neutral)
    if (census["full_2026_model_union_64px_pixels"]!=CANONICAL_TOTAL or
            census["full_2026_model_part_occupancy_before_union"]!=CANONICAL_PARTS):
        raise ValueError("neutral exact 2026 model geometry changed")
    neutral_anchor=anchor(union_planes(neutral))
    source_reference={role:rows[1601] for role,rows in src.items()}
    sources_anchors={role:anchor(ref["alpha"]) for role,ref in source_reference.items()}
    source_pivot=source_center(axis)
    if tuple(source_pivot)!=FROZEN_EVEN_SOURCE_CENTRE:
        raise ValueError("original ROM even-orientation source pivot changed")

    def one_real_pose(model_angle:int,pivot:str)->dict[str,bytes]:
        apply_root_scene(scene,model_angle,pivot,0.,0.)
        part_4x=scene_part_source_masks(scene,camera,full_256=True)
        full=scene.to_geometry() if callable(getattr(scene,"to_geometry",None)) else scene.dump(concatenate=True)
        alpha=render_mask(np.asarray(full.vertices),np.asarray(full.faces),camera).astype(bool)
        part_union=np.logical_or.reduce(tuple(part_4x[p] for p in PARTS))
        if not np.array_equal(alpha,part_union):
            raise ValueError("2026 part-by-part raster differs from exact real GLB union")
        return part_4x

    render_cache={}
    rows={}
    for role,times in UPPER_EVENTS.items():
        rows[role]={}
        reference=source_reference[role]
        for tick in times:
            target=src[role][tick]
            source=target["alpha"]
            source_null=rotate_source_2d(source_reference[role]["alpha"],
                target["angle"]-reference["angle"],source_pivot)
            arm_rows={}
            for arm in ARMS:
                if arm=="absolute_wheel_axle_root":
                    index=target["angle"];pivot="wheel_axle"
                else:
                    index=reference_relative_index(target["angle"],reference["angle"],64)
                    pivot="historical_midbody"
                key=(index,pivot)
                if key not in render_cache:
                    render_cache[key]=one_real_pose(index,pivot)
                aligned={part:registered_mask4(render_cache[key][part],
                    sources_anchors[role],neutral_anchor) for part in PARTS}
                full=union_planes(aligned)
                source_bands=attribute_bands(source,aligned)
                # Correct 256px once-only alignment must commute with logical
                # union; no part may quietly acquire a new source registration.
                registered_whole=registered_mask4(
                    np.logical_or.reduce(tuple(render_cache[key][p] for p in PARTS)),
                    sources_anchors[role],neutral_anchor)
                if full!=registered_whole:
                    raise ValueError("component registration changed whole-model alpha")
                arm_rows[arm]={
                    "2026_candidate_root_mode":pivot,
                    "hypothetical_2026_root_source_orientation_index":index,
                    "full_original_64px_iou":metric(source,full)["iou"],
                    "per_source_image_y_band":source_bands,
                }
            rows[role][str(tick)]={
                "original_Mesen_tick":tick,
                "original_ROM_phase_index":target["phase"],
                "original_ROM_orientation_index":target["angle"],
                "original_true_2d_rotation_iou":metric(source,source_null)["iou"],
                "fixed_original_first_tick_source_alpha_anchor_x2y2":
                    list(sources_anchors[role]),
                "arms":arm_rows,
            }
    aggregates={}
    for arm in ARMS:
        aggregates[arm]={}
        for role in UPPER_EVENTS:
            pts=[rows[role][str(t)]["arms"][arm]["per_source_image_y_band"]["upper_y0_14"]
                 for t in UPPER_EVENTS[role]]
            sums={k:sum(point["model_union_alpha_tp_fp_fn"][k] for point in pts)
                  for k in ("tp","fp","fn")}
            parts={part:{
                k:sum(point["per_2026_parent"][part][k] for point in pts)
                for k in ("projected_pixels","exclusive_union_pixels",
                          "exclusive_true_positive_source_pixels",
                          "exclusive_false_positive_source_pixels",
                          "ambiguous_2d_overlapping_parent_pixels")}
                for part in PARTS}
            aggregates[arm][role]={
                "source_upper_y0_14_pooled_tp_fp_fn":sums,
                "source_upper_y0_14_pooled_iou":round(
                    sums["tp"]/sum(sums.values()),8),
                "source_upper_pixel_instances_missing_all_2026_parts":
                    sum(point["source_opaque_pixels_missing_all_2026_parts"] for point in pts),
                "source_upper_part_projection_attribution":parts,
            }
    return {
        "schema":SCHEMA,
        "source_original_Mesen24_zip_SHA256":sha(source_zip),
        "source_original_exact_ROM_pose_report_sha256":sha(pose_raw),
        "source_original_24x64_orientation_report_sha256":sha(axis_raw),
        "source_even_orientation_calibration_pivot_xy":list(FROZEN_EVEN_SOURCE_CENTRE),
        "source_provisional_7_6_camera_sha256":sha(camera_raw),
        "source_existing_2026_SCAD_sha256":SOURCE_SCAD_SHA,
        "source_attempt_verified_2026_upright_GLB_sha256":sha(model),
        "model_neutral_five_parent_64px_source_census":census,
        "real_2026_model_parent_support_not_proven_original_1994_anatomy":True,
        "projected_shared_parent_pixels_not_assigned_to_one_part":True,
        "source_roles_held_OAM_local_not_final_screen_red_reflected":True,
        "same_original_source_registration_for_all_2026_parts_and_poses":True,
        "candidate_2026_mesh_camera_materials_unchanged":True,
        "original_1994_3D_mesh_camera_bones_source_angles_recovered":False,
        "owner_likeness_approved":False,
        "source_selected_real_upper_events":{
            role:list(times) for role,times in UPPER_EVENTS.items()},
        "already_examined_original_source_samples_not_prospective_blind":True,
        "rows":rows,"aggregates":aggregates,
        "cached_real_2026_model_part_pose_count":len(render_cache),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--pose-report",required=True,type=Path)
    p.add_argument("--axis-report",required=True,type=Path)
    p.add_argument("--camera",required=True,type=Path)
    p.add_argument("--verified-exports",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=analyze(a.source_zip.read_bytes(),a.pose_report.read_bytes(),
        a.axis_report.read_bytes(),a.camera.read_bytes(),a.verified_exports)
    publish_text_once(a.out,json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("OK ART4K_REAL_2026_DYNAMIC_PARENT_SOURCE_UPPER",
          json.dumps(report["aggregates"],sort_keys=True))


if __name__=="__main__":
    main()
