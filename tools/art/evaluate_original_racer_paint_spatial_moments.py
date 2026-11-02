#!/usr/bin/env python3
"""Source-pixel 2D paint covariance versus depth-visible 2026 blue material.

Independent of translation, IoU and source pose timing. The source high-chroma
colours are NOT proven to represent the same physical part as the 2026 fork.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.audit_original_racer_chroma_components import source_chroma_pixels
    from tools.art.audit_original_racer_painted_frame_depth import material_triangles, rasterize_depth
    from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CHROMA_SHA, CAMERA_SHA, MODEL_SHA, spin_frame,
        source_selected_angle, painted_axis_from_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.render_racer_glb_projection import camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_chroma_components import source_chroma_pixels
    from audit_original_racer_painted_frame_depth import material_triangles, rasterize_depth
    from evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CHROMA_SHA, CAMERA_SHA, MODEL_SHA, spin_frame,
        source_selected_angle, painted_axis_from_mask,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from render_racer_glb_projection import camera_config
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-ROM-PAINTED-SPATIAL-MOMENTS-2D/1"
CORPUS_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SPLIT_SHA="aa86e13348875a768351d926a2daa913c3428732e92c8f135bbeadf53398c"


def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def painted_spread(points:set[tuple[int,int]])->dict:
    """Population spatial sigma in physical 7:6 2D pixels; no model-fit shift.

    Eigenvalues of the 2x2 covariance matrix are invariant to pixel
    translation and basis rotation, and expose width-like versus length-like
    spread without inventing a 3D cylindrical part or texture width.
    """
    if (type(points) is not set or not 12<=len(points)<=4096 or
            any(type(v) is not tuple or len(v)!=2 or
                any(type(c) is not int or not 0<=c<64 for c in v)
                for v in points)):
        raise ValueError("requires nonempty 64px binary-colour coordinate set")
    n=len(points)
    x_mean=sum(x*7/6 for x,_ in points)/n
    y_mean=sum(y for _,y in points)/n
    xx=sum((x*7/6-x_mean)**2 for x,_ in points)/n
    yy=sum((y-y_mean)**2 for _,y in points)/n
    xy=sum((x*7/6-x_mean)*(y-y_mean) for x,y in points)/n
    tr=xx+yy
    disc=math.hypot(xx-yy,2*xy)
    major=(tr+disc)/2
    minor=(tr-disc)/2
    if not math.isfinite(major) or not math.isfinite(minor) or minor<=1e-8:
        raise ValueError("degenerate projected paint footprint cannot imply a finite width")
    return {
        "painted_pixels":n,
        "sigma_major_physical_px":math.sqrt(major),
        "sigma_minor_physical_px":math.sqrt(minor),
        "ellipse_major_over_minor":math.sqrt(major/minor),
        "original_3d_part_width_recovered":False,
    }


def spread_from_binary_mask(mask)->dict:
    import numpy as np
    arr=np.asarray(mask)
    if (arr.shape!=(64,64) or arr.dtype.kind not in "biu" or
            not np.isin(arr,[0,1]).all()):
        raise ValueError("expected 64px depth-visible binary painted mask")
    pts=np.argwhere(arr.astype(bool))
    return painted_spread({(int(x),int(y)) for y,x in pts})


def source_spreads(corpus_path:Path,source_chroma:dict)->dict:
    """Original PNG/RGBA/alpha SHA checked independently, with variant census."""
    corpus,verified=validate_corpus(corpus_path)
    if (verified["corpus_sha256"]!=CORPUS_SHA or
            corpus.get("source_rom_sha256")!=ROM_SHA or
            corpus.get("source_rom_verified_and_used_for_composition") is not True):
        raise ValueError("not authenticated original USA ROM 64px source corpus")
    root=corpus_path.resolve().parent
    by_rgba={}
    by_mask=defaultdict(set)
    for name,entry in sorted(corpus["source_representations"].items()):
        p=(root/entry["local_file"]).resolve()
        if not p.is_relative_to(root):
            raise ValueError("source PNG path escaped private original corpus")
        w,h,rgba,pngsha=decode_rgba_png(p)
        stats=alpha_metrics(rgba,w,h)
        if ((w,h)!=(64,64) or pngsha!=entry["local_png_sha256"] or
                stats["source_rgba_sha256"]!=entry["source_rgba_sha256"] or
                stats["binary_mask_sha256"]!=entry["source_binary_mask_sha256"]):
            raise ValueError("original ROM-composed PNG / RGBA / alpha altered")
        rgba_sha=entry["source_rgba_sha256"]
        mask_sha=entry["source_binary_mask_sha256"]
        if rgba_sha not in by_rgba:
            record=painted_spread(source_chroma_pixels(rgba,entry["player"]))
            by_rgba[rgba_sha]={
                "source_binary_mask_sha256":mask_sha,
                "source_player":entry["player"],
                **record,
            }
        elif (by_rgba[rgba_sha]["source_binary_mask_sha256"]!=mask_sha or
              by_rgba[rgba_sha]["source_player"]!=entry["player"]):
            raise ValueError("same authentic source RGBA falsely assigned another player or shape")
        by_mask[mask_sha].add(rgba_sha)
    src_rows=source_chroma["source_variants"]["source_masks"]
    if (len(by_rgba)!=41 or len(by_mask)!=35 or len(src_rows)!=35 or
            set(by_mask)!=verified["all_masks"]):
        raise ValueError("not the original 41 RGBA / 35 silhouette source")
    for row in src_rows:
        shape=row["original_binary_mask_sha256"]
        rgba={v["rgba_sha256"] for v in row["source_colour_variants"]}
        if rgba!=by_mask.get(shape):
            raise ValueError("original-source colour variants differ from independently audited PNGs")
        for v in row["source_colour_variants"]:
            if (v["player"]!=by_rgba[v["rgba_sha256"]]["source_player"] or
                    v["measurement"]["pixel_count"]!=by_rgba[v["rgba_sha256"]]["painted_pixels"]):
                raise ValueError("source painted pixel-count or player receipt inconsistent")
    return by_rgba


def model_spreads(scene,camera,direction:int)->dict:
    import numpy as np
    if type(direction) is not int or direction not in (-1,1):
        raise ValueError("only two provisional world-Y depth directions supported")
    out={}
    for angle in ANGLES:
        posed=spin_frame(scene,angle)
        tri,ids,blue=material_triangles(posed)
        owner,tie,_=rasterize_depth(tri,ids,camera,direction)
        foreground=(owner==blue)&~tie
        shape=spread_from_binary_mask(foreground)
        shape["painted_axis_degrees"]=painted_axis_from_mask(foreground)
        shape["ambiguous_coplanar_pixels_excluded"]=int(tie.sum())
        out[angle]=shape
    return out


def compare(source_chroma:dict,actual_source_spreads:dict,models:dict,
            family:dict|None=None)->dict:
    if (set(models)!=set(ANGLES) or not isinstance(actual_source_spreads,dict)
            or len(actual_source_spreads)!=41):
        raise ValueError("source 41-RGBA and complete 2026 hinge grid needed")
    original=source_chroma["source_variants"]["source_masks"]
    if len(original)!=35:
        raise ValueError("expected 35 unique original 2D source silhouettes")
    angles={a:models[a]["painted_axis_degrees"] for a in ANGLES}
    rows=[]
    seen=set()
    for item in sorted(original,key=lambda x:x["original_binary_mask_sha256"]):
        shape=item["original_binary_mask_sha256"]
        if shape in seen:
            raise ValueError("duplicate original source binary mask")
        seen.add(shape)
        srcangle=item["equal_colour_variant_mean_projected_angle_deg"]
        chosen=source_selected_angle(srcangle,angles)
        model=models[chosen]
        variants=[]
        for v in item["source_colour_variants"]:
            sha=v["rgba_sha256"]
            if sha not in actual_source_spreads or actual_source_spreads[sha]["source_binary_mask_sha256"]!=shape:
                raise ValueError("source colour variant not independently verified against PNG")
            source=actual_source_spreads[sha]
            variants.append({
                "source_rgba_sha256":sha,"source_player":source["source_player"],
                "source_sigma_major_physical_px":source["sigma_major_physical_px"],
                "source_sigma_minor_physical_px":source["sigma_minor_physical_px"],
                "model_sigma_major_physical_px":model["sigma_major_physical_px"],
                "model_sigma_minor_physical_px":model["sigma_minor_physical_px"],
                "source_to_model_major_spread_ratio":source["sigma_major_physical_px"]/model["sigma_major_physical_px"],
                "source_to_model_minor_spread_ratio":source["sigma_minor_physical_px"]/model["sigma_minor_physical_px"],
            })
        if not variants:
            raise ValueError("original binary source shape lacks RGB variant")
        rows.append({
            "original_binary_mask_sha256":shape,
            "source_family":family.get(shape) if family else None,
            "source_angle_selected_2026_hinge_degrees":chosen,
            "source_original_RGBA_variants":variants,
            "equal_variant_mean_source_to_model_major_sigma_ratio":sum(v["source_to_model_major_spread_ratio"] for v in variants)/len(variants),
            "equal_variant_mean_source_to_model_minor_sigma_ratio":sum(v["source_to_model_minor_spread_ratio"] for v in variants)/len(variants),
        })
    if len(seen)!=35 or set(actual_source_spreads)!={v["source_rgba_sha256"] for r in rows for v in r["source_original_RGBA_variants"]}:
        raise ValueError("source mask and original colour-variant census incomplete")
    if family is not None and (set(family)!=seen or set(family.values())!={"first16","additional19"}):
        raise ValueError("source-family independence receipt mismatched")
    def summ(part):
        if not part:raise ValueError("missing source family")
        return {
            "independent_binary_masks":len(part),
            "mean_source_to_model_major_spread_ratio":round(sum(r["equal_variant_mean_source_to_model_major_sigma_ratio"] for r in part)/len(part),8),
            "mean_source_to_model_minor_spread_ratio":round(sum(r["equal_variant_mean_source_to_model_minor_sigma_ratio"] for r in part)/len(part),8),
            "source_major_spread_exceeds_model_count":sum(r["equal_variant_mean_source_to_model_major_sigma_ratio"]>1 for r in part),
            "source_minor_spread_exceeds_model_count":sum(r["equal_variant_mean_source_to_model_minor_sigma_ratio"]>1 for r in part),
        }
    groups={"all35":summ(rows)}
    if family:
        for name in ("first16","additional19"):
            groups[name]=summ([r for r in rows if r["source_family"]==name])
    return {"summary":groups,"per_original_binary_mask":rows}


def evaluate(glb_path:Path,camera_path:Path,source_chroma_path:Path,
             corpus_path:Path,split_path:Path|None=None,direction:int=1):
    import trimesh
    raw_glb=glb_path.read_bytes()
    if digest(raw_glb)!=MODEL_SHA or raw_glb[:4]!=b"glTF":
        raise ValueError("not historical unapproved 2026 upright model")
    cam_bytes=camera_path.read_bytes()
    if digest(cam_bytes)!=CAMERA_SHA:
        raise ValueError("camera not identical to frozen uncalibrated 7:6 view")
    camera=json.loads(cam_bytes)
    camera_config(camera)
    chroma_bytes=source_chroma_path.read_bytes()
    if digest(chroma_bytes)!=CHROMA_SHA:
        raise ValueError("not exact authenticated original-ROM painted axes report")
    chroma=json.loads(chroma_bytes)
    originals=source_spreads(corpus_path,chroma)
    family=None
    if split_path is not None:
        raw=split_path.read_bytes()
        if digest(raw)!=SPLIT_SHA:
            raise ValueError("source-independent family split receipt altered")
        groups=json.loads(raw)["leakage_free_window_split"]
        family={s:"first16" for s in groups["fit_binary_shas"]}
        family.update({s:"additional19" for s in groups["withheld_binary_shas"]})
    scene=trimesh.load(io.BytesIO(raw_glb),file_type="glb",force="scene",process=False)
    model=model_spreads(scene,camera,direction)
    compared=compare(chroma,originals,model,family)
    return {"schema":SCHEMA,
            "authentic_original_usa_ROM_SHA256":ROM_SHA,
            "authenticated_source_corpus_manifest_sha256":CORPUS_SHA,
            "original_2D_chroma_receipt_sha256":CHROMA_SHA,
            "historical_2026_GLb_sha256":MODEL_SHA,
            "provisional_fixed_camera_sha256":CAMERA_SHA,
            "provisional_world_y_view_direction":direction,
            "source_mask_and_original_RGB_files_individually_verified":True,
            "source_colour_and_model_blue_are_one_original_physical_part":False,
            "source_original_3D_camera_or_anatomy_recovered":False,
            "source_1994_emulator_frame_order_verified":False,
            "mean_ratios_one_vote_per_source_binary_mask":True,
            "owner_likeness_approved":False,"shipping_art_approved":False,
            **compared}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--source-chroma",type=Path,required=True)
    p.add_argument("--corpus",type=Path,required=True)
    p.add_argument("--source-family",type=Path)
    p.add_argument("--view-y",type=int,choices=(-1,1),default=1)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.glb,a.camera,a.source_chroma,a.corpus,a.source_family,a.view_y)
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result["summary"],sort_keys=True,indent=2))


if __name__=="__main__":
    main()
