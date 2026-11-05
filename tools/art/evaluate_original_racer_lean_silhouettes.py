#!/usr/bin/env python3
"""Actual original-ROM FULL silhouette vs five SHA-locked 2026 root-lean GLBs.

This is a fixed-camera, unpaired raster fit diagnostic using the actual whole
five-part experimental source model and authentic 64x64 ROM-derived silhouettes,
NOT a recovered 1994 3D rig, camera, source pose registration or art approval.
Angles were selected POST-HOC on these source shapes in the painted-axis grid.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.evaluate_original_racer_wheel_holdout import (
        ROM_SHA, MODEL_SHA, BASE_ANCHOR, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from tools.art.render_racer_glb_projection import camera_config, render_mask, PARTS
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
    from tools.art.study_original_racer_root_lean_grid import CAMERA_SHA
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import validate_corpus
    from evaluate_original_racer_wheel_holdout import (
        ROM_SHA, MODEL_SHA, BASE_ANCHOR, originals_from_corpus,
        split_family_components, translated_4x_source_mask,
    )
    from render_racer_glb_projection import camera_config, render_mask, PARTS
    from score_racer_candidate import score
    from no_replace_report import publish_text_once
    from study_original_racer_root_lean_grid import CAMERA_SHA

SCHEMA = "UR-RACER-AUTHENTIC-ROM-FULL-SILHOUETTE-LEAN-COMPARISON/1"
ANGLES = (0., -35., 10., 15., 30.)  # Frozen before THIS full-mask test.
ANGLE_LABEL = {0.:"unchanged", -35.:"root-minus-35", 10.:"root-plus-10",
               15.:"root-plus-15", 30.:"root-plus-30"}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rotate_y_with_contact(vertices, tire_vertices, angle):
    """Rotate ALL source-world geometry together; lift to old tire min Z.

    No per-source raster fitting. The returned Z lift is only a provisional
    displayed tire-bottom constraint and does not guarantee physical contact.
    """
    import numpy as np
    if type(angle) is not float or angle not in ANGLES:
        raise ValueError("root angle not among declared source-coverage presets")
    all_v = np.asarray(vertices, dtype=float)
    tire_v = np.asarray(tire_vertices, dtype=float)
    if (all_v.ndim != 2 or all_v.shape[1] != 3 or len(all_v) < 3
            or tire_v.ndim != 2 or tire_v.shape[1] != 3 or len(tire_v) < 3
            or not np.isfinite(all_v).all() or not np.isfinite(tire_v).all()):
        raise ValueError("source 3D mesh or tire bounds missing/nonfinite")
    theta = math.radians(angle)
    c,s=math.cos(theta),math.sin(theta)
    matrix=np.asarray(((c,0,s),(0,1,0),(-s,0,c)),dtype=float)
    whole=all_v@matrix.T
    tire=tire_v@matrix.T
    old_lower=float(tire_v[:,2].min())
    tire_before=float(tire[:,2].min())
    lift=old_lower-tire_before
    whole[:,2]+=lift
    tire[:,2]+=lift
    if not math.isfinite(lift) or abs(float(tire[:,2].min())-old_lower)>1e-8:
        raise ValueError("source tire display-level preservation failed")
    return whole, {
        "root_world_y_angle_degrees":angle,
        "unadjusted_rotated_tire_min_source_z":round(tire_before,9),
        "visual_tire_bottom_lift_source_z":round(lift,9),
        "preserved_original_tire_min_source_z":round(old_lower,9),
        "whole_model_min_source_z_after_tire_lift":round(float(whole[:,2].min()),9),
        "original_1994_contact_physics_recovered":False,
    }


def summarize_per_mask(rows: dict[str, dict]) -> dict:
    """One original binary shape gets exactly one vote, never frame holds."""
    if not isinstance(rows,dict) or not rows:
        raise ValueError("no SHA-distinct source silhouettes to summarize")
    labels=set(ANGLE_LABEL.values())
    means={label:[] for label in labels}
    best_count={label:0 for label in labels}
    root0 = ANGLE_LABEL[0.]
    for sha, row in rows.items():
        if (not isinstance(sha,str) or len(sha)!=64
                or any(ch not in "0123456789abcdef" for ch in sha)
                or not isinstance(row,dict) or
                set(row.get("unpaired_study_scores",{}))!=labels):
            raise ValueError("missing original mask or five actual GLB hypotheses")
        scores=row["unpaired_study_scores"]
        for name, result in scores.items():
            iou=result.get("mask_iou")
            if type(iou) not in (int,float) or not math.isfinite(iou) or not 0<=iou<=1:
                raise ValueError("nonfinite or invalid whole-silhouette IoU")
            means[name].append(float(iou))
        best=max(labels,key=lambda name:(scores[name]["mask_iou"],
                                        -abs(float(row["root_angle_degrees"][name])),
                                        name))
        best_count[best]+=1
    values={k:round(sum(v)/len(v),8) for k,v in sorted(means.items())}
    # Compute differences from unrounded means. Subtracting two separately
    # rounded summaries causes a reproducible one-unit-at-1e-8 error.
    unrounded={key:sum(items)/len(items) for key,items in means.items()}
    paired={name:round(unrounded[name]-unrounded[root0],8)
            for name in sorted(labels) if name!=root0}
    return {
        "original_unique_binary_masks":len(rows),
        "source_frames_not_counted_as_independent":True,
        "mean_full_silhouette_iou_per_fixed_source_root_pose":values,
        "mean_iou_delta_relative_to_unmodified_upright":paired,
        "which_fixed_pose_has_highest_unpaired_iou_count":best_count,
        "original_frames_paired_to_1994_3d_pose":False,
    }


def compute(corpus_path:Path, glb_path:Path, camera_path:Path)->dict:
    import numpy as np
    import trimesh
    corpus,verified=validate_corpus(corpus_path)
    if corpus["source_rom_sha256"]!=ROM_SHA:
        raise ValueError("original-ROM source identity changed")
    source_groups=originals_from_corpus(corpus_path,corpus)
    if len(source_groups)!=35 or set(source_groups)!=verified["all_masks"]:
        raise ValueError("not the authenticated 35-mask original source study")
    split=split_family_components(verified["per_window_masks"])
    camera_bytes=camera_path.read_bytes()
    if digest(camera_bytes)!=CAMERA_SHA:
        raise ValueError("frozen 2026 provisional camera changed")
    camera=json.loads(camera_bytes)
    camera_config(camera)
    if (camera.get("source_anchor_x2_y2")!=list(BASE_ANCHOR)
            or camera.get("camera_calibration_status")!="provisional"):
        raise ValueError("source anchor/camera status modified")
    original_glb=glb_path.read_bytes()
    if digest(original_glb)!=MODEL_SHA or original_glb[:4]!=b"glTF":
        raise ValueError("not the exact frozen actual five-part 2026 GLB")
    scene=trimesh.load(file_obj=io.BytesIO(original_glb),file_type="glb",
                       force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or not set(PARTS).issubset(scene.graph.nodes):
        raise ValueError("five source-owned GLB part nodes missing")
    # Bake original parent matrices exactly once, matching existing projector.
    mesh=scene.dump(concatenate=True)
    all_v=np.asarray(mesh.vertices,dtype=float)
    faces=np.asarray(mesh.faces)
    if len(faces)!=28860:
        raise ValueError("frozen original 2026 GLB triangle identity changed")
    tire_parts=[]
    for child in ("tire__material_0","tire__material_1"):
        if child not in scene.graph.nodes_geometry:
            raise ValueError("source tire part missing: "+child)
        transform,geometry=scene.graph.get(child)
        owned=scene.geometry[geometry].copy()
        owned.apply_transform(transform)
        tire_parts.append(np.asarray(owned.vertices,dtype=float))
    tire=np.concatenate(tire_parts,axis=0)
    source_masks={}
    for angle in ANGLES:
        vertices,model_meta=rotate_y_with_contact(all_v,tire,angle)
        mask4=render_mask(vertices,faces,camera)
        source_masks[ANGLE_LABEL[angle]]={
            "model_source_owned_root_study":model_meta,
            "raster":mask4,
        }
    individual={}
    for sha,src in sorted(source_groups.items()):
        scores={}
        for angle in ANGLES:
            label=ANGLE_LABEL[angle]
            candidate=translated_4x_source_mask(
                source_masks[label]["raster"],src["source_alpha_anchor_x2_y2"])
            measured=score(src["mask"],candidate)
            scores[label]={
                "mask_iou":measured["mask_iou"],
                "mask_xor_pixels":measured["mask_xor_pixels"],
                "boundary_chamfer_mean_physical_px":
                    measured["boundary_chamfer_mean_physical_px"],
                "lowest_alpha_delta_x2_y2":measured["lowest_alpha_delta_x2_y2"],
            }
        individual[sha]={
            "source_original_alpha_contact_x2_y2":list(src["source_alpha_anchor_x2_y2"]),
            "players":sorted(src["players"]),
            "registered_source_representations":sorted(src["source_representations"]),
            "root_angle_degrees":{ANGLE_LABEL[a]:a for a in ANGLES},
            "unpaired_study_scores":scores,
        }
    return {
        "schema":SCHEMA,
        "source_original_USA_ROM_sha256":ROM_SHA,
        "source_verified_corpus_sha256":digest(corpus_path.read_bytes()),
        "source_2026_actual_GLb_sha256":MODEL_SHA,
        "source_provisional_camera_sha256":CAMERA_SHA,
        "fixed_original_canvas_64x64_and_pixel_aspect_7_6":True,
        "original_source_frame_observations":len(corpus["source_temporal_frame_observations"]),
        "original_unique_binary_silhouettes":len(source_groups),
        "model_2026_faces":len(faces),
        "model_2026_root_pose_hypotheses":[
            {"label":ANGLE_LABEL[a],
             **source_masks[ANGLE_LABEL[a]]["model_source_owned_root_study"]}
            for a in ANGLES],
        "per_original_binary_silhouette":individual,
        "summary":summarize_per_mask(individual),
        "original_source_window_leakage_split_for_descriptive_audit":{
            "fit_connected_windows":split["fit_connected_windows"],
            "withheld_connected_window_components":
                split["withheld_connected_window_components"],
            "withheld_binary_mask_count":split["independent_holdout_mask_count"],
            "withheld_was_NOT_hidden_during_earlier_root_lean_angle_selection":True,
        },
        "angle_grid_was_selected_using_these_known_original_masks":True,
        "source_authentic_original_1994_camera_identified":False,
        "source_original_1994_sprite_to_2026_rig_pose_paired":False,
        "original_3d_mesh_joint_or_tire_contact_recovered":False,
        "experimental_rig_geometry_altered_or_republished":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus",required=True,type=Path)
    parser.add_argument("--glb",required=True,type=Path)
    parser.add_argument("--camera",required=True,type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    output=json.dumps(compute(args.corpus,args.glb,args.camera),
                      sort_keys=True,indent=2)+"\n"
    if args.out:publish_text_once(args.out,output)
    else:print(output,end="")


if __name__=="__main__":
    main()
