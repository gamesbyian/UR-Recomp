#!/usr/bin/env python3
"""Original 2D painted extent versus depth-visible 2026 GLB blue material.

The old original-ROM colour receipt and frozen experimental GLB are SHA pinned.
This comparison DOES NOT prove that their coloured pixels depict one physical
part, recover the 1994 camera, or approve a 3D likeness. Mask selection is one
vote per original binary silhouette; RGB variants retain separate estimates.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.audit_original_racer_painted_frame_depth import (
        rasterize_depth, material_triangles,
    )
    from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CHROMA_SHA, CAMERA_SHA, MODEL_SHA, spin_frame,
        source_selected_angle,
    )
    from tools.art.render_racer_glb_projection import camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_painted_frame_depth import rasterize_depth, material_triangles
    from evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CHROMA_SHA, CAMERA_SHA, MODEL_SHA, spin_frame, source_selected_angle,
    )
    from render_racer_glb_projection import camera_config
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-2D-PAINT-EXTENT-TO-2026-DEPTH-GLB/1"
SPLIT_SHA = "aa86e13348875a768351d926a2daa913c3428732e92c8f135bbeadf53398c"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extent_from_endpoints(top, bottom, count) -> dict:
    """Image-space 7:6 physical-pixel axis length; translation irrelevant."""
    if (type(count) is not int or not 0<count<=4096 or
            not isinstance(top,(list,tuple)) or
            not isinstance(bottom,(list,tuple)) or
            len(top)!=2 or len(bottom)!=2 or
            any(type(v) not in (float,int) or not math.isfinite(v)
                for v in (*top,*bottom)) or
            any(not 0<=v<64 for v in (*top,*bottom))):
        raise ValueError("invalid source/model 2D painted-region endpoints")
    dx=(bottom[0]-top[0])*7/6
    dy=bottom[1]-top[1]
    if dy<=0:
        raise ValueError("painted source axis has nonpositive vertical extent")
    length=math.hypot(dx,dy)
    return {"painted_pixels":count,
            "axial_length_physical_px":length,
            "painted_area_per_axial_length":count/length,
            "signed_painted_axis_deg":math.degrees(math.atan2(dx,dy))}


def extent_from_mask(mask) -> dict:
    """Same top/bottom THREE occupied rows as original source painted census."""
    import numpy as np
    m=np.asarray(mask)
    if (m.shape!=(64,64) or m.dtype.kind not in "biu" or
            not np.isin(m,[0,1]).all()):
        raise ValueError("model blue painted mask must be 64x64 binary")
    pts=np.argwhere(m.astype(bool))
    if len(pts)<12:
        raise ValueError("too little model blue paint to infer its 2D axis")
    rows=np.unique(pts[:,0])
    if len(rows)<8 or rows[-1]-rows[0]<8:
        raise ValueError("model painted region has too few occupied rows")
    top=pts[np.isin(pts[:,0],rows[:3])].mean(axis=0)
    bottom=pts[np.isin(pts[:,0],rows[-3:])].mean(axis=0)
    return extent_from_endpoints((float(top[1]),float(top[0])),
                                 (float(bottom[1]),float(bottom[0])),len(pts))


def original_variant_extent(variant:dict)->dict:
    """Source RGB variant is authenticated by the separately SHA-pinned report."""
    if not isinstance(variant,dict) or variant.get("player") not in ("p1","p2"):
        raise ValueError("source RGB player unknown")
    rgba=variant.get("rgba_sha256")
    if (not isinstance(rgba,str) or len(rgba)!=64 or
            any(c not in "0123456789abcdef" for c in rgba)):
        raise ValueError("source RGB variant SHA missing")
    m=variant.get("measurement")
    if not isinstance(m,dict):
        raise ValueError("original source painted region measurement missing")
    r=extent_from_endpoints(m.get("top_centroid_logical_xy"),
                            m.get("bottom_centroid_logical_xy"),m.get("pixel_count"))
    axis=m.get("signed_axis_angle_from_image_vertical_deg")
    if (type(axis) not in (float,int) or not math.isfinite(axis) or
            abs(axis-r["signed_painted_axis_deg"])>0.00002):
        raise ValueError("original source axial centroid receipt inconsistent")
    return {"source_player":variant["player"],"source_rgba_sha256":rgba,**r}


def measured_blue_model(scene,camera,direction=1)->dict:
    """Depth-test exact sixteen material meshes, no hidden blue pixels counted."""
    import numpy as np
    if type(direction) is not int or direction not in (-1,1):
        raise ValueError("only one of two provisional world-Y side views allowed")
    results={}
    for angle in ANGLES:
        posed=spin_frame(scene,angle)
        triangles,material,blue=material_triangles(posed)
        owner,tied,_=rasterize_depth(triangles,material,camera,direction)
        visible=(owner==blue)&~tied
        stats=extent_from_mask(visible)
        stats["depth_tied_pixels_excluded"]=int(tied.sum())
        results[angle]=stats
    return results


def compare(source_rows:list[dict],model_by_angle:dict,
            families:dict|None=None)->dict:
    """Source axis picks hinge, then compare area and length, without IoU.

    Never use a target silhouette to choose an original colour variant, pose,
    pixel translation or relative pixel-area normalization.
    """
    if (not isinstance(source_rows,list) or len(source_rows)!=35 or
            set(model_by_angle)!=set(ANGLES)):
        raise ValueError("requires 35 unique source shapes and full fixed hinge grid")
    if families is not None and (set(families)!={r["original_binary_mask_sha256"] for r in source_rows}
                                or set(families.values())!={"first16","additional19"}):
        raise ValueError("source-family SHA grouping incomplete")
    model_axis={a:model_by_angle[a]["signed_painted_axis_deg"] for a in ANGLES}
    rows=[]
    seen=set()
    for original in sorted(source_rows,key=lambda x:x["original_binary_mask_sha256"]):
        mask=original["original_binary_mask_sha256"]
        if (not isinstance(mask,str) or len(mask)!=64 or
                any(c not in "0123456789abcdef" for c in mask) or mask in seen):
            raise ValueError("original binary source SHA missing or duplicated")
        seen.add(mask)
        variants=original.get("source_colour_variants")
        if not isinstance(variants,list) or not variants:
            raise ValueError("original source mask has no RGB measurements")
        src=[original_variant_extent(v) for v in variants]
        if len({v["source_rgba_sha256"] for v in src})!=len(src):
            raise ValueError("duplicate original colour variant identity")
        measured_mean=original.get("equal_colour_variant_mean_projected_angle_deg")
        if (type(measured_mean) not in (float,int) or not math.isfinite(measured_mean)
                or abs(sum(v["signed_painted_axis_deg"] for v in src)/len(src)-
                       measured_mean)>0.00002):
            raise ValueError("source variant mean-angle authentication failed")
        chosen=source_selected_angle(measured_mean,model_axis)
        model=model_by_angle[chosen]
        if (model["painted_pixels"]<=0 or model["axial_length_physical_px"]<=0
                or model["painted_area_per_axial_length"]<=0):
            raise ValueError("model blue paint extent empty")
        per_variant=[]
        for v in src:
            per_variant.append({
                **v,
                "source_to_model_painted_area_ratio":v["painted_pixels"]/model["painted_pixels"],
                "source_to_model_axial_length_ratio":v["axial_length_physical_px"]/model["axial_length_physical_px"],
                "source_to_model_area_per_length_ratio":v["painted_area_per_axial_length"]/model["painted_area_per_axial_length"],
                "individual_source_variant_alternative_hinge_degrees":
                    source_selected_angle(v["signed_painted_axis_deg"],model_axis),
            })
        rows.append({
            "source_binary_mask_sha256":mask,
            "source_family":families.get(mask) if families else None,
            "equal_variant_source_painted_axis_selected_hinge_degrees":chosen,
            "projected_blue_model_painted_pixels":model["painted_pixels"],
            "projected_blue_model_axial_length_physical_px":model["axial_length_physical_px"],
            "source_rgb_variants":per_variant,
            "mean_source_to_model_painted_area_ratio":sum(v["source_to_model_painted_area_ratio"] for v in per_variant)/len(per_variant),
            "mean_source_to_model_axial_length_ratio":sum(v["source_to_model_axial_length_ratio"] for v in per_variant)/len(per_variant),
            "mean_source_to_model_area_per_length_ratio":sum(v["source_to_model_area_per_length_ratio"] for v in per_variant)/len(per_variant),
            "source_variant_pose_disagreement":len({v["individual_source_variant_alternative_hinge_degrees"] for v in per_variant})>1,
        })
    def summary(group):
        if not group:
            raise ValueError("empty original source-mask group")
        return {
            "independent_binary_source_masks":len(group),
            "mean_source_to_model_area_ratio":round(sum(r["mean_source_to_model_painted_area_ratio"] for r in group)/len(group),8),
            "mean_source_to_model_length_ratio":round(sum(r["mean_source_to_model_axial_length_ratio"] for r in group)/len(group),8),
            "mean_source_to_model_area_per_length_ratio":round(sum(r["mean_source_to_model_area_per_length_ratio"] for r in group)/len(group),8),
            "original_shapes_with_more_painted_pixels_than_model":sum(r["mean_source_to_model_painted_area_ratio"]>1 for r in group),
            "source_shapes_with_RGB_variant_pose_disagreement":sum(r["source_variant_pose_disagreement"] for r in group),
        }
    groups={"all35":summary(rows)}
    if families:
        for name in ("first16","additional19"):
            groups[name]=summary([r for r in rows if r["source_family"]==name])
    return {"summary":groups,"per_original_binary_mask":rows}


def evaluate(glb_path:Path,camera_path:Path,chroma_path:Path,
             source_family_path:Path|None=None,direction:int=1)->dict:
    import trimesh
    glb=glb_path.read_bytes()
    if sha(glb)!=MODEL_SHA or glb[:4]!=b"glTF":
        raise ValueError("historical experimental unapproved GLB SHA mismatch")
    camera_bytes=camera_path.read_bytes()
    if sha(camera_bytes)!=CAMERA_SHA:
        raise ValueError("frozen provisional source camera SHA mismatch")
    camera=json.loads(camera_bytes)
    camera_config(camera)
    raw=chroma_path.read_bytes()
    if sha(raw)!=CHROMA_SHA:
        raise ValueError("authenticated 2D ROM-composed chroma receipt SHA mismatch")
    source=json.loads(raw)
    if source.get("original_chroma_rule")!="classify_source_chroma from existing original colour census":
        raise ValueError("unexpected original 2D painted source rule")
    shapes=source["source_variants"]["source_masks"]
    families=None
    if source_family_path:
        file=source_family_path.read_bytes()
        if sha(file)!=SPLIT_SHA:
            raise ValueError("historical original source family split SHA mismatch")
        pairs=json.loads(file)["leakage_free_window_split"]
        families={x:"first16" for x in pairs["fit_binary_shas"]}
        families.update({x:"additional19" for x in pairs["withheld_binary_shas"]})
    scene=trimesh.load(io.BytesIO(glb),file_type="glb",force="scene",process=False)
    model=measured_blue_model(scene,camera,direction)
    compared=compare(shapes,model,families)
    return {
        "schema":SCHEMA,
        "historical_2026_glb_sha256":MODEL_SHA,
        "original_rom_painted_axis_report_sha256":CHROMA_SHA,
        "provisional_fixed_camera_sha256":CAMERA_SHA,
        "optional_sha_disjoint_source_family_receipt_sha256":SPLIT_SHA if families else None,
        "source_report_independently_revalidated_original_PNG_bytes":False,
        "source_3d_material_correspondence_verified":False,
        "original_1994_camera_and_animation_recovered":False,
        "selected_2026_hinges_based_on_source_painted_axis_only":True,
        "mean_values_one_vote_per_original_binary_mask":True,
        "source_colour_variants_not_silently_dropped":True,
        "hypothetical_view_direction_world_y":direction,
        "original_3d_character_likeness_approved":False,
        "shipping_art_approved":False,
        **compared,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb",required=True,type=Path)
    parser.add_argument("--camera",required=True,type=Path)
    parser.add_argument("--source-chroma",required=True,type=Path)
    parser.add_argument("--source-family",type=Path)
    parser.add_argument("--view-y",type=int,choices=(-1,1),default=1)
    parser.add_argument("--out",required=True,type=Path)
    opts=parser.parse_args()
    result=evaluate(opts.glb,opts.camera,opts.source_chroma,opts.source_family,opts.view_y)
    publish_text_once(opts.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result["summary"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
