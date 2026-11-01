#!/usr/bin/env python3
"""Original-ROM full-silhouette interaction of two separately supported 2026 shape axes.

Two ACTUAL source-owned SHA-frozen upright GLBs (fork1.0/fork1.4) and one
in-memory source-owned wheel-X span (1.0/1.1); original ROM PNGs are reverified.
All choices were previously examined on these same 35 2D source shapes: this
is an exploratory crossed interaction, not independent original 1994 3D fit.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.ablate_original_racer_wheel_width import ablated_world_mesh
    from tools.art.evaluate_original_racer_wheel_holdout import (
        ROM_SHA, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.render_racer_glb_projection import camera_config, render_mask, PARTS
    from tools.art.score_racer_candidate import score
    from tools.art.study_original_racer_root_lean_grid import CAMERA_SHA
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from ablate_original_racer_wheel_width import ablated_world_mesh
    from evaluate_original_racer_wheel_holdout import (
        ROM_SHA, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from render_racer_glb_projection import camera_config, render_mask, PARTS
    from score_racer_candidate import score
    from study_original_racer_root_lean_grid import CAMERA_SHA
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-REAL-SOURCE-WHEEL-AND-FORK-CROSSED-ORIGINAL-2D-FAMILIES/1"
GLBS = {
    1.0:"ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04",
    1.4:"5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53",
}
WIDTHS=(1.0,1.1)
LABELS=("fork1.0_wheel1.0","fork1.0_wheel1.1",
        "fork1.4_wheel1.0","fork1.4_wheel1.1")
FIRST="fork1.0_wheel1.0"
WHEEL="fork1.0_wheel1.1"
FORK="fork1.4_wheel1.0"
BOTH="fork1.4_wheel1.1"


def sha(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def summarizes(scores:dict[str,dict],partition:dict)->dict:
    if not isinstance(scores,dict) or len(scores)!=35:
        raise ValueError("requires 35 original SHA-unique binary masks")
    fit=set(partition.get("fit_binary_shas",[]))
    withheld=set(partition.get("withheld_binary_shas",[]))
    if (not fit or not withheld or len(withheld)!=19 or fit&withheld
            or fit|withheld!=set(scores)):
        raise ValueError("invalid binary-mask-disjoint original source partition")
    def one(hashes):
        names=sorted(hashes)
        per={}
        for label in LABELS:
            vals=[]
            for h in names:
                row=scores[h]
                if (not isinstance(h,str) or len(h)!=64 or
                        any(v not in "0123456789abcdef" for v in h) or
                        set(row)!=set(LABELS)):
                    raise ValueError("unregistered original mask or incomplete crossed source study")
                item=row[label]
                val=item.get("mask_iou")
                edge=item.get("boundary_chamfer_mean_physical_px")
                if (type(val) not in (int,float) or not math.isfinite(val) or
                        not 0<=val<=1 or
                        type(edge) not in (int,float) or not math.isfinite(edge) or
                        not 0<=edge<=100):
                    raise ValueError("invalid original whole-source silhouette metric")
                vals.append(item)
            per[label]={
                "mean_IoU":round(sum(x["mask_iou"] for x in vals)/len(vals),8),
                "mean_boundary_chamfer_physical_px":round(
                    sum(x["boundary_chamfer_mean_physical_px"] for x in vals)/len(vals),8),
                "wins_vs_unmodified":sum(scores[h][label]["mask_iou"]>
                                        scores[h][FIRST]["mask_iou"] for h in names),
                "losses_vs_unmodified":sum(scores[h][label]["mask_iou"]<
                                          scores[h][FIRST]["mask_iou"] for h in names),
                "mean_IoU_delta_vs_unmodified":round(
                    sum(scores[h][label]["mask_iou"]-scores[h][FIRST]["mask_iou"]
                        for h in names)/len(names),8),
            }
        per[BOTH]["wins_vs_wheel_only"]=sum(
            scores[h][BOTH]["mask_iou"]>scores[h][WHEEL]["mask_iou"] for h in names)
        per[BOTH]["losses_vs_wheel_only"]=sum(
            scores[h][BOTH]["mask_iou"]<scores[h][WHEEL]["mask_iou"] for h in names)
        per[BOTH]["mean_IoU_delta_vs_wheel_only"]=round(
            sum(scores[h][BOTH]["mask_iou"]-scores[h][WHEEL]["mask_iou"]
                for h in names)/len(names),8)
        return {"independent_original_binary_mask_count":len(names),
                "source_original_shapes_have_equal_one_vote_each":True,
                "candidates":per}
    return {
        "source_first_fit_connected_component":one(fit),
        "previously_SHA_disconnected_original_2D_mask_family":one(withheld),
        "entire_known_original_2D_shape_set":one(set(scores)),
        "withheld_source_masks_are_not_proven_independent_1994_3D_views":True,
    }


def evaluate(corpus_file:Path,camera_file:Path,GLB_default:Path,GLB_fork:Path)->dict:
    import trimesh
    receipt,verified=validate_corpus(corpus_file)
    if receipt["source_rom_sha256"]!=ROM_SHA:
        raise ValueError("not the existing canonical original USA ROM")
    shapes=originals_from_corpus(corpus_file,receipt)
    if set(shapes)!=verified["all_masks"] or len(shapes)!=35:
        raise ValueError("registered source original shapes diverged")
    partition=split_family_components(verified["per_window_masks"])
    camera_raw=camera_file.read_bytes()
    if sha(camera_raw)!=CAMERA_SHA:
        raise ValueError("existing exact provisional source camera changed")
    camera=json.loads(camera_raw)
    camera_config(camera)
    records={}
    for mass,path in ((1.0,GLB_default),(1.4,GLB_fork)):
        data=path.read_bytes()
        if sha(data)!=GLBS[mass] or data[:4]!=b"glTF":
            raise ValueError("not the pinned actual source-owned fork-mass GLB")
        scene=trimesh.load(file_obj=io.BytesIO(data),file_type="glb",
                           force="scene",process=False)
        if (not isinstance(scene,trimesh.Scene) or
                not set(PARTS).issubset(scene.graph.nodes) or
                len(scene.graph.nodes_geometry)!=16):
            raise ValueError("actual source GLB five-part hierarchy changed")
        for width in WIDTHS:
            vertices,faces=ablated_world_mesh(scene,float(width))
            raster=render_mask(vertices,faces,camera)
            label=f"fork{mass:.1f}_wheel{width:.1f}"
            records[label]={
                "source_fork_frame_mass":mass,
                "source_wheel_rim_x_width":width,
                "source_actual_GLb_sha256":sha(data),
                "full_model_triangle_count":int(len(faces)),
                "source_fixed_camera_4x_binary_mask":raster,
            }
    per={}
    for mask_sha,shape in sorted(shapes.items()):
        result={}
        for label in LABELS:
            rendered=records[label]
            candidate=translated_4x_source_mask(
                rendered["source_fixed_camera_4x_binary_mask"],
                shape["source_alpha_anchor_x2_y2"])
            measured=score(shape["mask"],candidate)
            result[label]={k:measured[k] for k in
                ("mask_iou","mask_xor_pixels",
                 "boundary_chamfer_mean_physical_px",
                 "lowest_alpha_delta_x2_y2")}
        per[mask_sha]=result
    summary=summarizes(per,partition)
    # Verify three independently measured source controls (not a guessed
    # new optimum). These source scores are SHA-bound historical evidence.
    hold=summary["previously_SHA_disconnected_original_2D_mask_family"]["candidates"]
    expected={FIRST:0.38192089,WHEEL:0.41491323,FORK:0.38824958}
    for label,mean in expected.items():
        if abs(hold[label]["mean_IoU"]-mean)>1e-7:
            raise ValueError("prior real original source control no longer reproduces: "+label)
    return {
        "schema":SCHEMA,
        "original_USA_ROM_sha256":ROM_SHA,
        "original_corpus_sha256":sha(corpus_file.read_bytes()),
        "fixed_provisional_7_6_source_camera_sha256":sha(camera_raw),
        "actual_2026_source_GLb_SHA_by_mass":{str(k):v for k,v in GLBS.items()},
        "actual_source_original_mask_count":len(per),
        "original_frame_observations":len(receipt["source_temporal_frame_observations"]),
        "source_model_fork_and_wheel_factor_grid":[
            {k:v for k,v in records[label].items()
             if k!="source_fixed_camera_4x_binary_mask"}
            for label in LABELS],
        "original_per_independent_binary_mask_scores":per,
        "source_partition_interaction":summary,
        "both_candidate_axes_selected_after_inspecting_2D_source_masks":True,
        "independent_original_1994_3D_camera_family_held_out":False,
        "source_character_true_1994_3D_mesh_or_camera_recovered":False,
        "original_1994_to_2026_pose_pairing":False,
        "original_physical_ground_contact_recovered":False,
        "rig_source_geometry_or_runtime_art_modified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus",required=True,type=Path)
    ap.add_argument("--camera",required=True,type=Path)
    ap.add_argument("--unchanged-glb",required=True,type=Path)
    ap.add_argument("--fork-1p4-glb",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    text=json.dumps(evaluate(args.corpus,args.camera,
          args.unchanged_glb,args.fork_1p4_glb),indent=2,sort_keys=True)+"\n"
    if args.out:publish_text_once(args.out,text)
    else:print(text,end="")


if __name__=="__main__":
    main()
