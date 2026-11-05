#!/usr/bin/env python3
"""Genuine original-family validation of the ONE source-authored frame-mass axis.

The original OpenSCAD rig has rig_frame_mass=[1,2]. The earlier frame-mass
ablation chose candidates on ten original source silhouettes. This program
freezes those choices at 1.0/1.4/2.0, renders actual SCAD module geometry and
measures the 19 exact SHA-distinct original ROM masks in disconnected windows.
Nothing modifies the canonical rig, GLB, viewer, or original ROM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

try:
    from tools.art.ablate_racer_frame_mass import (
        CANONICAL_SOURCE_SHA, PART_CALLS, export_part, source_prefix,
        validate_scores,
    )
    from tools.art.evaluate_original_racer_wheel_holdout import (
        BASE_ANCHOR, ROM_SHA, FIRST, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.render_racer_glb_projection import camera_config, render_mask
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from ablate_racer_frame_mass import (
        CANONICAL_SOURCE_SHA, PART_CALLS, export_part, source_prefix,
        validate_scores,
    )
    from evaluate_original_racer_wheel_holdout import (
        BASE_ANCHOR, ROM_SHA, FIRST, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from render_racer_glb_projection import camera_config, render_mask
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-REAL-SCAD-FRAME-MASS-DISCONNECTED-SOURCE-FAMILY/1"
MASS_TRIALS = (1.0, 1.4, 2.0)
UNMODIFIED_FIRST_FAMILY_MEAN = 0.57255469
SOURCE_PARTS = ("tire", "rim_and_hub", "pedals", "saddle")
EXPECTED_SCAD_SHA = CANONICAL_SOURCE_SHA


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def summaries_by_partition(per_mask: dict[str, dict], independent: dict) -> dict:
    if not isinstance(per_mask, dict) or len(per_mask) != 35:
        raise ValueError("expected exactly 35 authentic original binary silhouettes")
    fit = set(independent.get("fit_binary_shas", []))
    held = set(independent.get("withheld_binary_shas", []))
    if (not fit or not held or fit & held or fit | held != set(per_mask)
            or len(held) != 19):
        raise ValueError("leaky/changed original source family partition")
    def summary(hashes):
        ordered=[per_mask[h] for h in sorted(hashes)]
        for row in ordered:
            if set(row.get("scores",{})) != {"1.0","1.4","2.0"}:
                raise ValueError("source shape missing authentic SCAD mass trial")
        result={}
        for m in MASS_TRIALS:
            key=str(m)
            ious=[x["scores"][key]["mask_iou"] for x in ordered]
            contours=[x["scores"][key]["boundary_chamfer_mean_physical_px"]
                      for x in ordered]
            for value in ious:
                if type(value) not in (float,int) or not 0<=value<=1:
                    raise ValueError("bad whole-source silhouette overlap")
            for value in contours:
                if type(value) not in (float,int) or not 0<=value<=100:
                    raise ValueError("bad physical-pixel edge distance")
            result[key]={
                "mean_original_mask_iou":round(sum(ious)/len(ious),8),
                "mean_boundary_chamfer_physical_px":
                    round(sum(contours)/len(contours),8),
                "wins_over_unmodified_iou":sum(
                    x["scores"][key]["mask_iou"]>
                    x["scores"]["1.0"]["mask_iou"] for x in ordered),
                "losses_to_unmodified_iou":sum(
                    x["scores"][key]["mask_iou"]<
                    x["scores"]["1.0"]["mask_iou"] for x in ordered),
                "ties_with_unmodified_iou":sum(
                    x["scores"][key]["mask_iou"]==
                    x["scores"]["1.0"]["mask_iou"] for x in ordered),
                "mean_delta_iou_vs_unmodified":round(
                    sum(ious[i]-ordered[i]["scores"]["1.0"]["mask_iou"]
                        for i in range(len(ious)))/len(ious),8),
            }
        return {"source_independent_binary_mask_count":len(ordered),
                "mass_trials":result}
    return {
        "historical_first_family_fit_connected_windows": independent["fit_connected_windows"],
        "fit_connected_component":summary(fit),
        "previously_unseen_source_mask_holdout":summary(held),
        "entire_known_original_2D_mask_corpus":summary(set(per_mask)),
        "withheld_family_connected_components":independent[
            "withheld_connected_window_components"],
    }


def compute(source_scad:Path, corpus_path:Path, camera_path:Path) -> dict:
    import numpy as np
    import trimesh
    raw=source_scad.read_bytes()
    if sha(raw) != EXPECTED_SCAD_SHA:
        raise ValueError("not the frozen existing 2026 OpenSCAD rig source")
    prefix=source_prefix(raw,EXPECTED_SCAD_SHA)
    corpus,checked=validate_corpus(corpus_path)
    if corpus["source_rom_sha256"]!=ROM_SHA:
        raise ValueError("original USA-ROM SHA changed")
    groups=originals_from_corpus(corpus_path,corpus)
    split=split_family_components(checked["per_window_masks"])
    if len(groups)!=35 or set(groups)!=checked["all_masks"]:
        raise ValueError("actual original source family count changed")
    camera_raw=camera_path.read_bytes()
    camera=json.loads(camera_raw)
    camera_config(camera)
    if (camera.get("camera_calibration_status")!="provisional"
            or camera.get("source_anchor_x2_y2")!=list(BASE_ANCHOR)
            or camera.get("logical_pixels_per_model_unit_vertical")!=9.5
            or camera.get("right_world")!=[1,0,0]
            or camera.get("up_world")!=[0,0,1]):
        raise ValueError("original first-family provisional camera refit")
    openscad=shutil.which("openscad")
    if not openscad:
        raise RuntimeError("need actual OpenSCAD renderer, not synthetic mesh")
    per_mask={h:{
        "source_binary_mask_sha256":h,
        "source_players":sorted(x["players"]),
        "source_original_representations":sorted(x["source_representations"]),
        "original_source_visible_contact_x2_y2":
            list(x["source_alpha_anchor_x2_y2"]),
        "scores":{},
    } for h,x in sorted(groups.items())}
    trials=[]
    with tempfile.TemporaryDirectory(prefix="ur-art4k-frame-holdout-") as folder_name:
        folder=Path(folder_name)
        fixed={part:export_part(prefix,part,1.0,folder,openscad)
               for part in SOURCE_PARTS}
        for mass in MASS_TRIALS:
            fork=export_part(prefix,"fork_and_frame",mass,folder,openscad)
            mesh=trimesh.util.concatenate(
                [fixed[p][0] for p in SOURCE_PARTS]+[fork[0]])
            vertices,faces=np.asarray(mesh.vertices),np.asarray(mesh.faces)
            mask4=render_mask(vertices,faces,camera)
            for h,source in sorted(groups.items()):
                candidate=translated_4x_source_mask(
                    mask4,source["source_alpha_anchor_x2_y2"])
                values=score(source["mask"],candidate)
                per_mask[h]["scores"][str(mass)]={
                    k:values[k] for k in (
                        "mask_iou","mask_xor_pixels",
                        "boundary_chamfer_mean_physical_px",
                        "lowest_alpha_delta_x2_y2")}
            trials.append({
                "source_rig_frame_mass":mass,
                "source_owned_real_fork_stl_sha256":fork[1],
                "fork_source_triangles":fork[2],
                "all_parts_actual_model_triangle_count":int(len(faces)),
                "real_source_model_openSCAD_geometry_exported":True,
                "all_other_four_source_parts_unchanged":True,
            })
    summary=summaries_by_partition(per_mask,split)
    fit=summary["fit_connected_component"]["mass_trials"]["1.0"]
    # The 10 historical first-family masks are present in its larger connected
    # component, but do not assert 10-mask mean on an expanded fit partition.
    first_shas=checked["per_window_masks"][FIRST]
    first_mean=round(sum(per_mask[h]["scores"]["1.0"]["mask_iou"]
                         for h in first_shas)/len(first_shas),8)
    if len(first_shas)!=10 or abs(first_mean-UNMODIFIED_FIRST_FAMILY_MEAN)>1e-7:
        raise ValueError("actual source rig + source-camera fails historical first-family result")
    return {
        "schema":SCHEMA,
        "actual_original_USA_ROM_sha256":ROM_SHA,
        "original_corpus_sha256":sha(corpus_path.read_bytes()),
        "canonical_2026_OpenSCAD_source_sha256":EXPECTED_SCAD_SHA,
        "frozen_provisional_camera_sha256":sha(camera_raw),
        "source_camera_is_provisional":True,
        "actual_original_binary_silhouettes":len(groups),
        "actual_original_frame_observations":len(corpus[
            "source_temporal_frame_observations"]),
        "same_five_part_original_2026_source_model":True,
        "source_part_names":list(SOURCE_PARTS)+["fork_and_frame"],
        "frozen_mass_trials_preselected_using_first_family":[1.0,1.4,2.0],
        "first_family_source_mask_count":len(first_shas),
        "first_family_unmodified_mean_iou_reproduced":first_mean,
        "actual_source_OpenSCAD_mesh_exports":trials,
        "per_original_binary_mask":per_mask,
        "source_family_partition_results":summary,
        "withheld_shapes_are_SHA_disjoint_from_historical_fit_family":True,
        "withheld_shapes_are_not_authenticated_independent_1994_3D_views":True,
        "no_original_sprite_to_experimental_mesh_pose_registration":True,
        "source_1994_camera_or_pivots_recovered":False,
        "rig_geometry_or_shipping_default_modified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-scad",required=True,type=Path)
    ap.add_argument("--corpus",required=True,type=Path)
    ap.add_argument("--camera",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    payload=json.dumps(compute(args.source_scad,args.corpus,args.camera),
                       sort_keys=True,indent=2)+"\n"
    if args.out: publish_text_once(args.out,payload)
    else: print(payload,end="")


if __name__=="__main__":
    main()
