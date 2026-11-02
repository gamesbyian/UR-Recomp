#!/usr/bin/env python3
"""Original 2D painted end-to-end extent vs 2026 depth-visible GLB blue frame.

The centre-to-centre vector is invariant to translation, so this diagnostic
never invokes source-target silhouette IoU or chooses a best 2D pixel shift.
Neither original 3D camera nor original game anatomy has been recovered.
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
        rasterize_depth, material_triangles, CAMERA_SHA, CHROMA_SHA,
        MODEL_SHA, ANGLES, source_selected_angle, spin_frame,
    )
    from tools.art.render_racer_glb_projection import camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_painted_frame_depth import (
        rasterize_depth, material_triangles, CAMERA_SHA, CHROMA_SHA,
        MODEL_SHA, ANGLES, source_selected_angle, spin_frame,
    )
    from render_racer_glb_projection import camera_config
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-2D-PAINT-ENDPOINT-VERSUS-2026-FORK-LENGTH/1"
SPLIT_SHA="aa86e13348875a768351d926a2daa913c3428732e92c2f38f135bbeadf53398c"


def physical_painted_vector(top,bottom):
    """Source 7:6 pixel aspect, direction from top to bottom, exact endpoints."""
    if (type(top) not in (tuple,list) or type(bottom) not in (tuple,list) or
            len(top)!=2 or len(bottom)!=2 or
            any(type(n) not in (int,float) or not math.isfinite(n)
                for n in (*top,*bottom))):
        raise ValueError("two finite source painted endpoints required")
    dx=(bottom[0]-top[0])*7/6
    dy=bottom[1]-top[1]
    if dy<=0:
        raise ValueError("source top/bottom painted order reversed")
    return {"dx_physical_px":round(dx,8),
            "dy_physical_px":round(dy,8),
            "length_physical_px":round(math.hypot(dx,dy),8),
            "angle_from_image_vertical_deg":round(math.degrees(math.atan2(dx,dy)),8)}


def painted_area_ratio(original_pixels:int,model_visible_pixels:int)->float:
    """Original high-chroma area versus depth-frontmost blue, not 3D coverage."""
    if (type(original_pixels) is not int or type(model_visible_pixels) is not int
            or not 0<original_pixels<=4096 or not 0<model_visible_pixels<=4096):
        raise ValueError("two finite nonzero original/model 64px painted areas required")
    return round(original_pixels/model_visible_pixels,8)


def visible_blue_endpoints(blue_mask):
    import numpy as np
    mask=np.asarray(blue_mask)
    if mask.shape!=(64,64) or mask.dtype.kind not in "biu" or not mask.any():
        raise ValueError("nonempty binary painted model 64px mask required")
    if not np.all((mask==0)|(mask==1)):
        raise ValueError("blue material raster must be binary")
    rows=np.flatnonzero(mask.any(axis=1))
    if len(rows)<8 or rows[-1]-rows[0]<8:
        raise ValueError("painted model material has too little vertical extent")
    def centroid(ends):
        pixels=np.argwhere(mask[ends])
        return [float(pixels[:,1].mean()),float(np.mean(ends[pixels[:,0]]))]
    return physical_painted_vector(centroid(rows[:3]),centroid(rows[-3:]))


def candidate_blue_extent(scene,camera,angle):
    import numpy as np
    posed=spin_frame(scene,angle)
    tris,ids,blueid=material_triangles(posed)
    result={}
    for sign,label in ((1,"plus_y"),(-1,"minus_y")):
        owners,ties,_=rasterize_depth(tris,ids,camera,sign)
        visible=(owners==blueid)&~ties
        result[label]=visible_blue_endpoints(visible)
        result[label]["depth_visible_blue_pixel_count"]=int(visible.sum())
        result[label]["material_depth_tie_count"]=int(ties.sum())
    return result


def evaluate(glb_path:Path,camera_path:Path,chroma_path:Path,split_path:Path|None=None):
    import trimesh
    data=glb_path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=MODEL_SHA or data[:4]!=b"glTF":
        raise ValueError("not exact historical 2026 source GLB")
    camera_data=camera_path.read_bytes()
    if hashlib.sha256(camera_data).hexdigest()!=CAMERA_SHA:
        raise ValueError("camera differs from frozen provisional side hypothesis")
    camera=json.loads(camera_data)
    camera_config(camera)
    chroma_raw=chroma_path.read_bytes()
    if hashlib.sha256(chroma_raw).hexdigest()!=CHROMA_SHA:
        raise ValueError("not original authenticated 2D painted axes")
    chroma=json.loads(chroma_raw)
    cases=chroma["source_variants"]["source_masks"]
    if len(cases)!=35 or len({r["original_binary_mask_sha256"] for r in cases})!=35:
        raise ValueError("original unique binary mask census must remain 35")
    split={}
    if split_path is not None:
        raw=split_path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=SPLIT_SHA:
            raise ValueError("unexpected source family split SHA")
        groups=json.loads(raw)["leakage_free_window_split"]
        split={h:"first16" for h in groups["fit_binary_shas"]}
        split.update({h:"additional19" for h in groups["withheld_binary_shas"]})
        if set(split)!={r["original_binary_mask_sha256"] for r in cases}:
            raise ValueError("source binary family split leaks masks or misses one")
    scene=trimesh.load(io.BytesIO(data),file_type="glb",force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or len(scene.graph.nodes_geometry)!=16:
        raise ValueError("source model material graph changed")
    poses={angle:candidate_blue_extent(scene,camera,angle) for angle in ANGLES}
    signed_axes_by_side={side:{
        a:poses[a][side]["angle_from_image_vertical_deg"] for a in ANGLES}
        for side in ("plus_y","minus_y")}
    rows=[]
    for row in cases:
        masksha=row["original_binary_mask_sha256"]
        variants=row.get("source_colour_variants")
        if not isinstance(variants,list) or not variants:
            raise ValueError("original painted source variants absent")
        signed=row["equal_colour_variant_mean_projected_angle_deg"]
        choices={side:source_selected_angle(signed,axes)
                 for side,axes in signed_axes_by_side.items()}
        original=[]
        for variant in variants:
            m=variant["measurement"]
            vector=physical_painted_vector(
                m["top_centroid_logical_xy"],m["bottom_centroid_logical_xy"])
            original.append({"original_source_rgba_sha256":variant["rgba_sha256"],
                "source_player":variant["player"],
                "original_high_chroma_pixel_count":m["pixel_count"],
                "source_painted_endpoints":vector})
        source_mean=sum(v["source_painted_endpoints"]["length_physical_px"]
                        for v in original)/len(original)
        mean_source_painted_area=sum(v["original_high_chroma_pixel_count"]
                                      for v in original)/len(original)
        relatives={}
        for side,chosen in choices.items():
            measured=poses[chosen][side]
            relatives[side]={
                "source_angle_selected_2026_hinge_degrees":chosen,
                "source_mean_painted_length_physical_px":round(source_mean,8),
                "source_mean_original_high_chroma_pixels":round(mean_source_painted_area,8),
                "depth_visible_model_blue_pixels":measured["depth_visible_blue_pixel_count"],
                "original_to_model_painted_area_ratio":round(
                    mean_source_painted_area/measured["depth_visible_blue_pixel_count"],8),
                "source_original_variant_to_model_area_ratio_bounds":[
                    painted_area_ratio(min(v["original_high_chroma_pixel_count"] for v in original),
                                      measured["depth_visible_blue_pixel_count"]),
                    painted_area_ratio(max(v["original_high_chroma_pixel_count"] for v in original),
                                      measured["depth_visible_blue_pixel_count"])],
                "depth_visible_model_blue_length_physical_px":measured["length_physical_px"],
                "original_to_model_painted_length_ratio":
                    round(source_mean/measured["length_physical_px"],8),
                "source_original_variant_to_model_length_ratio_bounds":[
                    round(min(v["source_painted_endpoints"]["length_physical_px"]
                              for v in original)/measured["length_physical_px"],8),
                    round(max(v["source_painted_endpoints"]["length_physical_px"]
                              for v in original)/measured["length_physical_px"],8)],
            }
        rows.append({"source_binary_mask_sha256":masksha,
            "source_family":split.get(masksha),
            "source_original_rgb_variants":original,
            "translation_or_source_target_silhouette_iou_used":False,
            "unpaired_selected_model_endpoint_lengths":relatives})
    def summarize(items):
        result={"unique_original_binary_mask_count":len(items)}
        for side in ("plus_y","minus_y"):
            numbers=[r["unpaired_selected_model_endpoint_lengths"][side][
                "original_to_model_painted_length_ratio"] for r in items]
            result[side]={
                "mean_original_to_model_painted_length_ratio":
                    round(sum(numbers)/len(numbers),8),
                "minimum_original_to_model_ratio":min(numbers),
                "maximum_original_to_model_ratio":max(numbers),
                "original_shapes_with_ratio_below_one":sum(x<1 for x in numbers),
                "mean_original_to_model_visible_painted_area_ratio":round(
                    sum(r["unpaired_selected_model_endpoint_lengths"][side][
                        "original_to_model_painted_area_ratio"] for r in items)/len(items),8),
                "source_shapes_with_more_painted_pixels_than_model":sum(
                    r["unpaired_selected_model_endpoint_lengths"][side][
                        "original_to_model_painted_area_ratio"]>1 for r in items)}
        return result
    summaries={"all35":summarize(rows)}
    if split:
        for label in ("first16","additional19"):
            subset=[row for row in rows if row["source_family"]==label]
            if not subset:
                raise ValueError("original source family unexpectedly empty")
            summaries[label]=summarize(subset)
    return {
        "schema":SCHEMA,
        "historical_unapproved_2026_glb_sha256":MODEL_SHA,
        "frozen_provisional_camera_sha256":CAMERA_SHA,
        "original_1994_rom_composed_painted_axes_sha256":CHROMA_SHA,
        "actual_original_camera_or_3d_anatomical_part_recovered":False,
        "source_blue_frame_is_proven_original_fork_geometry":False,
        "3d_geometry_modified":False,
        "source_2d_target_model_silhouette_iou_used_for_selection":False,
        "any_translation_selected_or_optimized":False,
        "source_painted_axis_2026_hinge_selection_is_posthoc":True,
        "original_emulator_ppu_frame_timing_verified":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
        "summary":summaries,
        "per_experimental_2026_hinge":{str(a):v for a,v in poses.items()},
        "per_original_binary_mask":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb",required=True,type=Path)
    p.add_argument("--camera",required=True,type=Path)
    p.add_argument("--source-chroma",required=True,type=Path)
    p.add_argument("--source-family",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=evaluate(a.glb,a.camera,a.source_chroma,a.source_family)
    publish_text_once(a.out,json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report["summary"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
