#!/usr/bin/env python3
"""Source-painted 2D axis to *2026* 3D frame hinge, with no IoU pose oracle.

Experimental semantic inverse-graphics discriminator. The exact original ROM
2D red/blue painted-centroid angle chooses the nearest projected angle of the
same unapproved GLB's blue fork material under one FROZEN provisional camera.
Original 1994 3D rig, source-camera and animation are NOT recovered.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.evaluate_original_racer_wheel_anchor_registered_hinge import (
        MODEL_SHA,CAMERA_SHA,CHROMA_SHA,CORPUS_SHA,SPLIT_SHA,
        digest,source_rings,centre_shift_4x,translate_4x,iou,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.evaluate_original_racer_wheel_holdout import originals_from_corpus
    from tools.art.render_racer_glb_projection import camera_config,render_mask
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from evaluate_original_racer_wheel_anchor_registered_hinge import (
        MODEL_SHA,CAMERA_SHA,CHROMA_SHA,CORPUS_SHA,SPLIT_SHA,
        digest,source_rings,centre_shift_4x,translate_4x,iou,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from evaluate_original_racer_wheel_holdout import originals_from_corpus
    from render_racer_glb_projection import camera_config,render_mask
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-2D-CHROMA-TO-EXPERIMENTAL-3D-HINGE/1"
ANGLES=tuple(range(-45,46,5))
CHROMA_NODE="fork_and_frame__material_0"
BLUE_RGBA=(28,89,222,255)


def painted_axis_from_mask(binary_64)->float:
    """Top and bottom three occupied source raster rows, SNES 7:6 physical X."""
    import numpy as np
    arr=np.asarray(binary_64)
    if arr.shape!=(64,64) or not arr.any():
        raise ValueError("source-coloured 64px binary image must be nonempty")
    rows=np.flatnonzero(arr.any(axis=1))
    if len(rows)<6:
        raise ValueError("not enough distinct painted 2D rows for an axis")
    top,bottom=rows[:3],rows[-3:]
    top_x=np.concatenate([np.flatnonzero(arr[y]) for y in top])
    bottom_x=np.concatenate([np.flatnonzero(arr[y]) for y in bottom])
    return math.degrees(math.atan2(
        (bottom_x.mean()-top_x.mean())*7/6, float(bottom.mean()-top.mean())
    ))


def source_selected_angle(source_axis_degrees:float,predicted_axes:dict)->int:
    """Never inspect source silhouette mask IoU to select one frame hinge."""
    if (type(source_axis_degrees) not in (float,int) or
            not math.isfinite(source_axis_degrees) or
            set(predicted_axes)!=set(ANGLES) or
            any(type(x) not in (float,int) or not math.isfinite(x)
                for x in predicted_axes.values())):
        raise ValueError("source angle / fixed source-model hinge grid invalid")
    return min(ANGLES,key=lambda angle:(
        abs(predicted_axes[angle]-source_axis_degrees),abs(angle),angle))


def spin_frame(scene,angle:int):
    if type(angle) is not int or angle not in ANGLES:
        raise ValueError("source hinge must be a predeclared bounded 5 degree step")
    import numpy as np
    axle=scene.graph.get("tire")[0]
    a=math.radians(angle)
    R=np.eye(4)
    R[0,0]=R[2,2]=math.cos(a)
    R[0,2]=math.sin(a)
    R[2,0]=-math.sin(a)
    K=axle@R@np.linalg.inv(axle)
    out=scene.copy()
    for name in ("fork_and_frame","saddle"):
        out.graph.update(frame_to=name,frame_from=out.graph.base_frame,
                         matrix=K@scene.graph.get(name)[0])
    for name in ("tire","rim_and_hub","pedals"):
        if not np.array_equal(out.graph.get(name)[0],scene.graph.get(name)[0]):
            raise ValueError("camera-independent hinge moved the wheel/crank")
    return out


def painted_model_axis(scene,camera)->float:
    import numpy as np
    import trimesh
    if CHROMA_NODE not in scene.graph.nodes_geometry:
        raise ValueError("expected painted source fork child absent")
    world,key=scene.graph.get(CHROMA_NODE)
    paint=scene.geometry[key].copy()
    colors=np.asarray(paint.visual.vertex_colors)
    if (len(colors)==0 or colors.shape[1]!=4 or
            not np.all(colors==np.array(BLUE_RGBA))):
        raise ValueError("source blue-frame material no longer authenticated")
    paint.apply_transform(world)
    mask=render_mask(paint.vertices,paint.faces,camera)[2::4,2::4]
    other=[]
    for node in sorted(scene.graph.nodes_geometry):
        if node==CHROMA_NODE:
            continue
        other_world,other_key=scene.graph.get(node)
        mesh=scene.geometry[other_key].copy()
        mesh.apply_transform(other_world)
        other.append(mesh)
    if len(other)!=15:
        raise ValueError("original source sixteen-material graph missing")
    merged=trimesh.util.concatenate(other)
    other_mask=render_mask(merged.vertices,merged.faces,camera)[2::4,2::4]
    occupied=int(mask.sum())
    if not occupied:
        raise ValueError("projected blue fork is empty")
    overlap=int((mask.astype(bool)&other_mask.astype(bool)).sum())
    return painted_axis_from_mask(mask),{
        "projected_blue_raster_pixels":occupied,
        "projected_blue_pixels_overlapping_other_materials":overlap,
        "overlap_fraction_not_proven_occluded":round(overlap/occupied,8),
        "true_visibility_and_depth_order_unknown":True,
    }


def evaluate(corpus_path:Path,glb_path:Path,camera_path:Path,
             chroma_path:Path,split_path:Path|None=None)->dict:
    import numpy as np
    import trimesh
    corpus,verified=validate_corpus(corpus_path)
    if verified["corpus_sha256"]!=CORPUS_SHA:
        raise ValueError("not original SHA-verified source ROM corpus")
    source=originals_from_corpus(corpus_path,corpus)
    if len(source)!=35 or set(source)!=verified["all_masks"]:
        raise ValueError("not complete original 35-source-mask corpus")
    rings=source_rings(corpus_path,corpus,source)
    camera_bytes=camera_path.read_bytes()
    if digest(camera_bytes)!=CAMERA_SHA:
        raise ValueError("source camera is not frozen provisional 7:6 camera")
    camera=json.loads(camera_bytes)
    right,up,origin,scale,anchor=camera_config(camera)
    raw_glb=glb_path.read_bytes()
    if digest(raw_glb)!=MODEL_SHA or raw_glb[:4]!=b"glTF":
        raise ValueError("not original five-part 2026 historical GLB")
    model=trimesh.load(io.BytesIO(raw_glb),file_type="glb",
                       force="scene",process=False)
    parents=("tire","rim_and_hub","pedals","fork_and_frame","saddle")
    if (not isinstance(model,trimesh.Scene) or
            not set(parents).issubset(model.graph.nodes) or
            len(model.graph.nodes_geometry)!=16):
        raise ValueError("source five-parent/16-material GLB absent")
    axle=model.graph.get("tire")[0]
    if any(not np.allclose(model.graph.get(n)[0],axle,atol=1e-8,rtol=0)
           for n in ("rim_and_hub","pedals")):
        raise ValueError("wheel/pedal common axle is broken")
    p=axle[:3,3]-origin
    axle4=(float(p@right*scale*4*6/7+2*anchor[0]+2),
           float(-p@up*scale*4+2*anchor[1]+2))
    source_chroma=chroma_path.read_bytes()
    if digest(source_chroma)!=CHROMA_SHA:
        raise ValueError("source colour axes must match original ROM research SHA")
    chroma=json.loads(source_chroma)
    observed={r["original_binary_mask_sha256"]:
              r["equal_colour_variant_mean_projected_angle_deg"]
              for r in chroma["source_variants"]["source_masks"]}
    if set(observed)!=set(source):
        raise ValueError("source painted axis missing or foreign mask")
    families={}
    if split_path is not None:
        raw=split_path.read_bytes()
        if digest(raw)!=SPLIT_SHA:
            raise ValueError("not original source SHA-disjoint family receipt")
        split=json.loads(raw)["leakage_free_window_split"]
        families={mask:"first16" for mask in split["fit_binary_shas"]}
        families.update({mask:"additional19" for mask in split["withheld_binary_shas"]})
        if set(families)!=set(source):
            raise ValueError("original source family leakage or missing masks")
    projected={}
    axes={}
    overlap_witness={}
    for angle in ANGLES:
        derived=spin_frame(model,angle)
        measured_axis,overlap=painted_model_axis(derived,camera)
        axes[angle]=round(measured_axis,8)
        overlap_witness[angle]=overlap
        mesh=(derived.to_geometry() if callable(getattr(derived,"to_geometry",None))
              else derived.dump(concatenate=True))
        projected[angle]=render_mask(mesh.vertices,mesh.faces,camera)
    rows=[]
    for sha,rec in sorted(source.items()):
        selected=source_selected_angle(observed[sha],axes)
        model_mask=projected[selected]
        ax,ay=rec["source_alpha_anchor_x2_y2"]
        historical=iou(rec["mask"],translate_4x(model_mask,2*(ax-67),2*(ay-76)))
        vals=[]
        for cx,cy,r in rings[sha]:
            dx,dy=centre_shift_4x(cx,cy,axle4)
            vals.append(iou(rec["mask"],translate_4x(model_mask,dx,dy)))
        rows.append({
            "source_binary_mask_sha256":sha,
            "original_source_painted_axis_degrees":observed[sha],
            "selected_2026_rig_fork_saddle_hinge_degrees":selected,
            "selected_rendered_blue_frame_axis_degrees":axes[selected],
            "source_2d_ring_centres":rings[sha],
            "source_family":families.get(sha),
            "historical_source_alpha_anchor_iou":historical,
            "wheel_centre_iou_min":min(vals),
            "wheel_centre_iou_max":max(vals),
            "source_target_model_silhouette_used_to_select_hinge_or_shift":False,
        })
    def mean(part):
        return {name:round(sum(r[name] for r in part)/len(part),8) for name in
                ("historical_source_alpha_anchor_iou","wheel_centre_iou_min","wheel_centre_iou_max")}
    summaries={"all35":{"count":35,"mean_iou":mean(rows)}}
    if families:
        for name in ("first16","additional19"):
            group=[r for r in rows if r["source_family"]==name]
            if not group:raise ValueError("empty historical source family")
            summaries[name]={"count":len(group),"mean_iou":mean(group)}
    return {
        "schema":SCHEMA,"original_rom_corpus_manifest_sha256":CORPUS_SHA,
        "historical_2026_glb_sha256":MODEL_SHA,
        "frozen_provisional_camera_sha256":CAMERA_SHA,
        "original_chroma_axes_receipt_sha256":CHROMA_SHA,
        "tested_rig_hinge_degrees":list(ANGLES),
        "rendered_2026_blue_frame_angle_by_hinge_degrees":{str(a):axes[a] for a in ANGLES},
        "blue_material_2d_overlap_by_hinge":{str(a):overlap_witness[a] for a in ANGLES},
        "painted_frame_true_visible_pixels_depth_tested":False,
        "pose_selected_using_source_2d_colour_and_model_painted_axis_only":True,
        "pose_selected_using_original_silhouette_iou_oracle":False,
        "translation_selected_using_original_model_silhouette_iou_oracle":False,
        "all_source_ring_centre_ties_remain_min_max":True,
        "camera_calibrated_or_1994_3d_joint_recovered":False,
        "original_1994_ppu_frame_timing_verified":False,
        "experiments_and_model_built_using_previously_inspected_35_masks":True,
        "owner_likeness_approved":False,"shipping_art_approved":False,
        "summaries":summaries,"per_original_binary_mask":rows}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus",required=True,type=Path)
    p.add_argument("--glb",required=True,type=Path)
    p.add_argument("--camera",required=True,type=Path)
    p.add_argument("--source-chroma",required=True,type=Path)
    p.add_argument("--source-family",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=evaluate(a.corpus,a.glb,a.camera,a.source_chroma,a.source_family)
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result["summaries"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
