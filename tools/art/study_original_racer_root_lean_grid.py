#!/usr/bin/env python3
"""Exploratory fixed-camera lean coverage of the ONE authentic 2026 GLB blockout.

Read-only: root-Y rotations are applied to a copy of the SHA-pinned actual
upright painted fork mesh IN MEMORY. Original source sprites are reverified
from the canonical ROM corpus, with no original 1994 3D joint/camera claim.
The angle grid is selected post-hoc and is NOT independent art validation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.compare_original_chroma_axes_to_glb_poses import (
        compare, COMMIT, CAMERA_SHA, POSE_GLB_SHA,
    )
    from tools.art.audit_original_racer_chroma_axes import painted_axis
    from tools.art.render_racer_glb_projection import render_mask, camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from compare_original_chroma_axes_to_glb_poses import compare,COMMIT,CAMERA_SHA,POSE_GLB_SHA
    from audit_original_racer_chroma_axes import painted_axis
    from render_racer_glb_projection import render_mask,camera_config
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-SHA-BOUND-EXPLORATORY-2026-ROOT-Y-LEAN-GRID/1"
PIVOT_WORLD_XYZ = (0.0, 0.0, 0.0)  # source hypothesized wheel-contact origin
ANGLES = tuple(float(v) for v in range(-45, 51, 5))
POSE_NAMES = ("upright","pedal","wheelie","stunt","bank")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def coverage(originals, baselines, candidates):
    """One vote per unique ORIGINAL binary source alpha shape."""
    if (not isinstance(originals,list) or not originals or
            not isinstance(baselines,dict) or set(baselines)!=set(POSE_NAMES) or
            not isinstance(candidates,(list,tuple))):
        raise ValueError("requires complete original and five experimental GLB inputs")
    sha_seen=set()
    source_angles=[]
    for row in originals:
        sha=row.get("source_binary_mask_sha256")
        angle=row.get("source_image_space_angle_deg")
        if (not isinstance(sha,str) or len(sha)!=64 or
                any(c not in "0123456789abcdef" for c in sha) or
                sha in sha_seen or type(angle) not in (int,float) or
                not math.isfinite(angle) or not -90<angle<90):
            raise ValueError("invalid or duplicate original source image descriptor")
        sha_seen.add(sha)
        source_angles.append(float(angle))
    all_axes=list(baselines.values())+list(candidates)
    if any(type(v) not in (int,float) or not math.isfinite(v) or not -90<v<90
           for v in all_axes):
        raise ValueError("unbounded candidate root-pose image-space descriptor")
    gaps=[min(abs(angle-axis) for axis in all_axes) for angle in source_angles]
    return {
        "source_original_unique_binary_masks":len(gaps),
        "one_original_mask_one_vote":True,
        "mean_nearest_projected_axis_gap_deg":round(sum(gaps)/len(gaps),6),
        "max_nearest_projected_axis_gap_deg":round(max(gaps),6),
        "source_masks_gap_above_10deg":sum(g>10 for g in gaps),
    }


def from_actual_glb(mesh, theta: float, camera: dict) -> dict:
    import numpy as np
    if type(theta) is not float or theta not in ANGLES:
        raise ValueError("root-lean study only accepts fixed declared angle grid")
    center=np.asarray(PIVOT_WORLD_XYZ,dtype=float)
    degrees=math.radians(theta)
    c,s=math.cos(degrees),math.sin(degrees)
    # Rotate around the source-contact origin, not a fitted camera/framing.
    # Trimesh vertices are source X/Y/Z; rotate about source world-Y.
    transform=np.array([[c,0,s],[0,1,0],[-s,0,c]])
    v=(np.asarray(mesh.vertices)-center) @ transform.T+center
    mask4=render_mask(v,mesh.faces,camera)
    if mask4.shape!=(256,256):
        raise ValueError("wrong source 4x raster measurement grid")
    rgba=np.zeros((64,64,4),dtype=np.uint8)
    rgba[mask4[2::4,2::4]!=0]=[28,89,222,255]
    m=painted_axis(rgba.tobytes(),"p2")
    return {
        "source_world_y_root_rotation_degrees":theta,
        "source_paint_axis_image_vertical_degrees":
            m["signed_axis_angle_from_image_vertical_deg"],
        "source_2d_paint_mask_opaque_pixels":m["pixel_count"],
        "only_preview_copy_of_painted_mesh_rotated":True,
    }


def audit(corpus:Path,source_axes:Path,model_root:Path,camera_file:Path)->dict:
    import trimesh
    prior=compare(corpus,source_axes,model_root,camera_file)
    original=prior["unpaired_2d_axis_coverage"]["per_original_binary_mask_unpaired_axis_gap"]
    baselines=prior["unpaired_2d_axis_coverage"]["experimental_2026_pose_axes_deg"]
    if len(original)!=35:
        raise ValueError("not the frozen verified original USA ROM source set")
    camera_bytes=camera_file.read_bytes()
    if digest(camera_bytes)!=CAMERA_SHA:
        raise ValueError("frozen provisional camera SHA diverged")
    camera=json.loads(camera_bytes)
    camera_config(camera)
    root=model_root.resolve()
    sha=POSE_GLB_SHA["upright"]
    glb=(root/"assets"/COMMIT/f"upright-{sha[:16]}.glb").resolve()
    if not glb.is_relative_to(root) or digest(glb.read_bytes())!=sha:
        raise ValueError("source upright GLB changed after actual 5-pose preflight")
    scene=trimesh.load(file_obj=io.BytesIO(glb.read_bytes()),file_type="glb",
                       force="scene",process=False)
    name="fork_and_frame__material_0"
    if list(n for n in scene.graph.nodes_geometry if n==name)!=[name]:
        raise ValueError("one source painted fork mesh required")
    world,geometry=scene.graph.get(name)
    mesh=scene.geometry[geometry].copy()
    mesh.apply_transform(world)
    rows=[from_actual_glb(mesh,theta,camera) for theta in ANGLES]
    upright=next(x for x in rows if x["source_world_y_root_rotation_degrees"]==0)
    if abs(upright["source_paint_axis_image_vertical_degrees"]-
           baselines["upright"])>1e-6:
        raise ValueError("real unchanged upright GLB no longer reproduces prior source axis")
    base=coverage(original,baselines,[])
    samples=[]
    for row in rows:
        result=coverage(original,baselines,
                        [row["source_paint_axis_image_vertical_degrees"]])
        samples.append({**row,"unpaired_original_2d_axis_coverage":result})
    pairs=[]
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            result=coverage(original,baselines,[
                a["source_paint_axis_image_vertical_degrees"],
                b["source_paint_axis_image_vertical_degrees"]])
            pairs.append({
                "source_world_y_root_rotations_degrees":[
                    a["source_world_y_root_rotation_degrees"],
                    b["source_world_y_root_rotation_degrees"]],
                "candidate_projected_painted_axes_deg":[
                    a["source_paint_axis_image_vertical_degrees"],
                    b["source_paint_axis_image_vertical_degrees"]],
                "unpaired_original_2d_axis_coverage":result,
            })
    pair_best_mean=sorted(pairs,key=lambda p:(
        p["unpaired_original_2d_axis_coverage"]["mean_nearest_projected_axis_gap_deg"],
        p["unpaired_original_2d_axis_coverage"]["source_masks_gap_above_10deg"]))[:5]
    pair_fewest_outliers=sorted(pairs,key=lambda p:(
        p["unpaired_original_2d_axis_coverage"]["source_masks_gap_above_10deg"],
        p["unpaired_original_2d_axis_coverage"]["mean_nearest_projected_axis_gap_deg"]))[:5]
    return {
        "schema":SCHEMA,
        "actual_original_rom_corpus_sha256":prior["source_corpus_sha256"],
        "actual_source_chroma_report_sha256":prior["original_source_chroma_report_sha256"],
        "source_model_GLb_sha256":sha,
        "frozen_provisional_camera_sha256":CAMERA_SHA,
        "original_mask_count":len(original),
        "known_five_static_experimental_axes_deg":baselines,
        "baseline_5_pose_unpaired_source_coverage":base,
        "all_predeclared_root_rotation_5deg_grid_samples":samples,
        "top_five_two_added_samples_by_training_mean_axis_gap":pair_best_mean,
        "top_five_two_added_samples_by_training_outlier_count":pair_fewest_outliers,
        "candidate_grid_selection_evaluated_on_all_35_original_masks_posthoc":True,
        "genuinely_new_original_3d_pose_holdout_tested":False,
        "original_1994_3d_camera_or_joint_mapping_recovered":False,
        "original_1994_frame_to_2026_rig_time_mapping_verified":False,
        "source_2026_mesh_or_default_geometry_modified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus",required=True,type=Path)
    ap.add_argument("--source-axes",required=True,type=Path)
    ap.add_argument("--model-review-dir",required=True,type=Path)
    ap.add_argument("--camera",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    content=json.dumps(audit(args.corpus,args.source_axes,
                             args.model_review_dir,args.camera),sort_keys=True,indent=2)+"\n"
    if args.out: publish_text_once(args.out,content)
    else: print(content,end="")


if __name__=="__main__":
    main()
