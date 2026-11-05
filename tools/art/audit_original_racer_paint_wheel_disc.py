#!/usr/bin/env python3
"""Source wheel-disc / high-chroma paint attribution versus ONE historical GLB.

Both the original 1994 sprite and the 2026 GLB are observed in PIXEL SPACE.
This is a falsifiable material-correspondence hypothesis, not a source 3D
wheel, original camera or animation-time witness. Never select the source
ring candidate, projected model pose or camera by silhouette-overlap IoU.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

try:
    from tools.art.audit_art4k_original_wheel_ring import (
        validate_corpus_and_measure, CORPUS_MANIFEST_SHA256, ORIGINAL_ROM_SHA256,
    )
    from tools.art.audit_original_racer_chroma_components import source_chroma_pixels
    from tools.art.audit_original_racer_painted_frame_depth import (
        rasterize_depth, material_triangles,
    )
    from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CAMERA_SHA, CHROMA_SHA, MODEL_SHA, spin_frame,
        source_selected_angle, painted_axis_from_mask,
    )
    from tools.art.render_racer_glb_projection import camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_art4k_original_wheel_ring import (
        validate_corpus_and_measure, CORPUS_MANIFEST_SHA256, ORIGINAL_ROM_SHA256,
    )
    from audit_original_racer_chroma_components import source_chroma_pixels
    from audit_original_racer_painted_frame_depth import rasterize_depth, material_triangles
    from evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, CAMERA_SHA, CHROMA_SHA, MODEL_SHA, spin_frame,
        source_selected_angle, painted_axis_from_mask,
    )
    from render_racer_glb_projection import camera_config
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-2D-WHEEL-DISC-PAINT-CORRESPONDENCE/1"
SPLIT_SHA = "aa86e13348875a768351d926a2daa913c3428732e92c8f135bbeadf53398c"
WHEEL_RING_RADIUS_LOGICAL_PX = 7


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def disk_band_fractions(points: set[tuple[int,int]], centres: list) -> list[dict]:
    """Source/model pixels within an anchored 7px wheel disc and nearby bands.

    Explicitly preserve every possible original 2D ring centre. Points are
    unshifted pixel centres; x and y must use the SAME source raster basis.
    """
    if (type(points) is not set or not 12 <= len(points) <= 4096 or
            any(type(p) is not tuple or len(p)!=2 or
                any(type(v) is not int or not 0<=v<64 for v in p)
                for p in points) or
            type(centres) is not list or not centres):
        raise ValueError("need source-frame painted integer pixel set and centres")
    out=[]
    for centre in centres:
        if (not isinstance(centre,(tuple,list)) or len(centre)!=3 or
                any(type(v) not in (int,float) or not math.isfinite(v)
                    for v in centre)):
            raise ValueError("malformed 2D rim centre")
        cx,cy,radius=centre
        if not (0<=cx<64 and 0<=cy<64 and
                radius==WHEEL_RING_RADIUS_LOGICAL_PX):
            raise ValueError("unsupported or offscreen original wheel ring")
        n=len(points)
        out.append({
            "wheel_centre_xy_logical_px":[cx,cy],
            "wheel_ring_radius_logical_px":radius,
            "fraction_inside_source_ring_disc":sum(
                (x-cx)**2+(y-cy)**2<=radius**2 for x,y in points)/n,
            "fraction_at_or_below_wheel_top":sum(
                y>=cy-radius for _,y in points)/n,
            "fraction_at_or_below_wheel_centre":sum(
                y>=cy for _,y in points)/n,
        })
    return out


def envelope(records: list[dict], name: str) -> tuple[float,float]:
    if not records or any(name not in x for x in records):
        raise ValueError("empty wheel-centre uncertainty envelope")
    return min(x[name] for x in records), max(x[name] for x in records)


def relative_painted_centroids(points:set[tuple[int,int]], centres:list,
                               *, above_wheel_only:bool=False)->list[dict]:
    """Independent wheel-anchored screen-pixel paint centroid, retaining ties.

    The boundary is STRICTLY above the top of the frozen radius-seven ring
    at y = wheel_y - 7. Excludes the near-wheel paint, not the entire frame.
    Returned pixel differences are physical 7:6 source-screen pixels and
    never constitute a recovered anatomical origin or 3D joint.
    """
    disk_band_fractions(points,centres)  # Fail closed on source shape/ring input.
    if type(above_wheel_only) is not bool:
        raise ValueError("above-wheel selector must be a Boolean")
    observations=[]
    for cx,cy,radius in centres:
        selected=[(x,y) for x,y in points
                  if not above_wheel_only or y<cy-radius]
        if len(selected)<3:
            raise ValueError("insufficient painted pixels above original wheel rim")
        xmean=sum(x for x,y in selected)/len(selected)
        ymean=sum(y for x,y in selected)/len(selected)
        observations.append({
            "wheel_centre_xy_logical_px":[cx,cy],
            "painted_pixel_count":len(selected),
            "paint_centroid_relative_to_wheel_physical_xy":[
                (xmean-cx)*7/6,ymean-cy],
        })
    return observations


def original_source_paint(zip_path: Path, chroma_report:dict):
    """Fresh original-ROM PNG/alpha hashes and all colour variants, no mask clips."""
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("offline original raster requires Pillow") from error
    ring_report=validate_corpus_and_measure(zip_path)
    if (ring_report.get("source_corpus_manifest_sha256")!=CORPUS_MANIFEST_SHA256 or
            ring_report.get("original_usa_rom_sha256")!=ORIGINAL_ROM_SHA256 or
            ring_report.get("unique_rgba_images")!=41 or
            ring_report.get("unique_binary_silhouettes")!=35):
        raise ValueError("original USA ROM/ring corpus evidence changed")
    ring_by_rgba={
        r["source_rgba_sha256"]:
            r["2d_ring_candidate"]["best_candidate_centres_xy_radius_logical_px"]
        for r in ring_report["images"]
    }
    result={}
    by_shape=defaultdict(set)
    with zipfile.ZipFile(zip_path) as archive:
        manifest=json.loads(archive.read("source-corpus.json"))
        if len(manifest["source_representations"])!=59:
            raise ValueError("not original 59 source renderings")
        for label,rec in sorted(manifest["source_representations"].items()):
            png=archive.read(rec["local_file"])
            if _sha(png)!=rec["local_png_sha256"]:
                raise ValueError("source PNG content changed")
            with Image.open(io.BytesIO(png)) as im:
                if im.mode!="RGBA" or im.size!=(64,64):
                    raise ValueError("original image dimensions/palette changed")
                rgba=im.tobytes()
            if _sha(rgba)!=rec["source_rgba_sha256"]:
                raise ValueError("decoded source RGBA identity changed")
            name=rec["source_rgba_sha256"]
            player=rec["player"]
            points=source_chroma_pixels(rgba,player)
            if name not in ring_by_rgba:
                raise ValueError("original ring candidate lost its source PNG identity")
            bands=disk_band_fractions(points,ring_by_rgba[name])
            found={"source_player":player,
                   "source_binary_mask_sha256":rec["source_binary_mask_sha256"],
                   "painted_source_pixels":len(points),
                   "all_original_ring_centre_candidates":bands,
                   "all_original_paint_centroid_candidates":
                       relative_painted_centroids(points,ring_by_rgba[name]),
                   "above_wheel_paint_centroid_candidates":
                       relative_painted_centroids(points,ring_by_rgba[name],
                                                  above_wheel_only=True)}
            if name in result and result[name]!=found:
                raise ValueError("identical source RGBA assigned inconsistent colours")
            result[name]=found
            by_shape[rec["source_binary_mask_sha256"]].add(name)
    if len(result)!=41 or len(by_shape)!=35 or len(ring_by_rgba)!=41:
        raise ValueError("original 41-colour/35-mask census lost")
    source_shapes=chroma_report["source_variants"]["source_masks"]
    if len(source_shapes)!=35:
        raise ValueError("original source axis report has duplicate/missing source shapes")
    for row in source_shapes:
        sha=row["original_binary_mask_sha256"]
        variants=row["source_colour_variants"]
        if len({v["rgba_sha256"] for v in variants})!=len(variants) or (
            {v["rgba_sha256"] for v in variants}!=by_shape.get(sha)):
            raise ValueError("original source 2D paint report colour variants mismatch")
        for v in variants:
            actual=result[v["rgba_sha256"]]
            if actual["source_player"]!=v["player"] or (
                actual["painted_source_pixels"]!=v["measurement"]["pixel_count"]):
                raise ValueError("original RGBA paint identity/count mismatch")
    return result


def historical_model_paint(glb_path:Path,camera_path:Path,direction:int):
    """Actual historical sixteen-material blue depth, fixed camera and axle."""
    import numpy as np
    import trimesh
    if type(direction) is not int or direction not in (-1,1):
        raise ValueError("unsupported historical provisional side direction")
    raw=glb_path.read_bytes()
    if _sha(raw)!=MODEL_SHA or raw[:4]!=b"glTF":
        raise ValueError("historical unapproved model GLB SHA differs")
    camraw=camera_path.read_bytes()
    if _sha(camraw)!=CAMERA_SHA:
        raise ValueError("historical provisional camera changed")
    camera=json.loads(camraw)
    right,up,origin,scale,anchor=camera_config(camera)
    scene=trimesh.load(io.BytesIO(raw),file_type="glb",force="scene",process=False)
    axle_matrix=scene.graph.get("tire")[0]
    axle=axle_matrix[:3,3]-origin
    wheel_cx=float(axle@right*scale*6/7+anchor[0]/2)
    wheel_cy=float(-axle@up*scale+anchor[1]/2)
    if not (0<=wheel_cx<64 and 0<=wheel_cy<64):
        raise ValueError("source model wheel axle outside fixed original raster")
    model={}
    for angle in ANGLES:
        posed=spin_frame(scene,angle)
        triangles,material_ids,blue_id=material_triangles(posed)
        owner,tied,_=rasterize_depth(triangles,material_ids,camera,direction)
        mask=(owner==blue_id)&~tied
        pixel_yx=np.argwhere(mask)
        if len(pixel_yx)<12:
            raise ValueError("source model blue depth evidence vanished")
        pixels={(int(x),int(y)) for y,x in pixel_yx}
        fraction=disk_band_fractions(pixels,[[wheel_cx,wheel_cy,
                                              WHEEL_RING_RADIUS_LOGICAL_PX]])[0]
        fraction["blue_visible_pixel_count"]=len(pixels)
        fraction["all_blue_centroid_relative_to_axle_physical_xy"] = (
            relative_painted_centroids(pixels,
                [[wheel_cx,wheel_cy,WHEEL_RING_RADIUS_LOGICAL_PX]])[0][
                    "paint_centroid_relative_to_wheel_physical_xy"])
        fraction["above_wheel_blue_centroid_relative_to_axle_physical_xy"] = (
            relative_painted_centroids(pixels,
                [[wheel_cx,wheel_cy,WHEEL_RING_RADIUS_LOGICAL_PX]],
                above_wheel_only=True)[0][
                    "paint_centroid_relative_to_wheel_physical_xy"])
        fraction["blue_model_painted_axis_degrees"]=painted_axis_from_mask(mask)
        model[angle]=fraction
    return model


def compare_shapes(source_chroma:dict,source:dict,model:dict,
                   families:dict|None=None)->dict:
    if len(source)!=41 or set(model)!=set(ANGLES):
        raise ValueError("incomplete original/3D material census")
    rows=source_chroma["source_variants"]["source_masks"]
    if len(rows)!=35:
        raise ValueError("one vote per 35 distinct original binary masks")
    predicted={a:v["blue_model_painted_axis_degrees"] for a,v in model.items()}
    result=[]
    seen=set()
    keys=("fraction_inside_source_ring_disc","fraction_at_or_below_wheel_top",
          "fraction_at_or_below_wheel_centre")
    for row in sorted(rows,key=lambda r:r["original_binary_mask_sha256"]):
        mask=row["original_binary_mask_sha256"]
        if mask in seen:
            raise ValueError("duplicate original source silhouette")
        seen.add(mask)
        angle=row["equal_colour_variant_mean_projected_angle_deg"]
        if type(angle) not in (int,float) or not math.isfinite(angle):
            raise ValueError("original 2D paint source axis nonfinite")
        selected=source_selected_angle(angle,predicted)
        evidence=[]
        for variant in row["source_colour_variants"]:
            rgba=variant["rgba_sha256"]
            if rgba not in source or source[rgba]["source_binary_mask_sha256"]!=mask:
                raise ValueError("unpaired original painted RGB source evidence")
            witness=source[rgba]
            bounds={k:envelope(witness["all_original_ring_centre_candidates"],k)
                    for k in keys}
            centroid_mismatch={}
            for region,source_key,model_key in (
                ("all_paint","all_original_paint_centroid_candidates",
                 "all_blue_centroid_relative_to_axle_physical_xy"),
                ("above_wheel_only","above_wheel_paint_centroid_candidates",
                 "above_wheel_blue_centroid_relative_to_axle_physical_xy"),
            ):
                model_xy=model[selected][model_key]
                source_rows=witness[source_key]
                distances=[
                    math.hypot(
                        row["paint_centroid_relative_to_wheel_physical_xy"][0]-model_xy[0],
                        row["paint_centroid_relative_to_wheel_physical_xy"][1]-model_xy[1])
                    for row in source_rows
                ]
                centroid_mismatch[region]={
                    "distance_min":min(distances),"distance_max":max(distances),
                    "source_centres_and_painted_centroids":source_rows,
                    "model_blue_centroid_relative_to_axle_physical_xy":model_xy,
                }
            evidence.append({"original_rgba_sha256":rgba,
                             "original_player":witness["source_player"],
                             "painted_original_pixel_count":witness["painted_source_pixels"],
                             "original_all_wheel_centres":witness["all_original_ring_centre_candidates"],
                             "source_wheel_fraction_bounds":bounds,
                             "centroid_mismatch_by_region":centroid_mismatch})
        if not evidence:
            raise ValueError("no source RGB for binary mask")
        def source_avg(key,idx):
            return sum(x["source_wheel_fraction_bounds"][key][idx] for x in evidence)/len(evidence)
        def centroid_avg(region,name):
            return sum(v["centroid_mismatch_by_region"][region][name]
                       for v in evidence)/len(evidence)
        result.append({
            "source_original_binary_mask_sha256":mask,
            "source_family":families.get(mask) if families else None,
            "posthoc_painted_direction_selected_2026_hinge_degrees":selected,
            "source_original_RGBA_variants":evidence,
            "painted_centroid_distance_envelopes_physical_px":{
                region:{"min":centroid_avg(region,"distance_min"),
                        "max":centroid_avg(region,"distance_max")}
                for region in ("all_paint","above_wheel_only")
            },
            "painted_original_vs_model_fraction_by_wheel_region":{
                key:{"source_min":source_avg(key,0),
                     "source_max":source_avg(key,1),
                     "model":model[selected][key]}
                for key in keys},
        })
    if set(source)!={v["original_rgba_sha256"]
                    for row in result for v in row["source_original_RGBA_variants"]}:
        raise ValueError("original source colour identities absent or reused")
    if families is not None and (set(families)!=seen or
                                 set(families.values())!={"first16","additional19"}):
        raise ValueError("original SHA-disjoint source-family evidence differs")
    def summarize(part):
        if not part:raise ValueError("empty original source family")
        output={"distinct_original_binary_masks":len(part)}
        for k in keys:
            vals=[r["painted_original_vs_model_fraction_by_wheel_region"][k] for r in part]
            label=k.replace("fraction_","")
            output[label]={
                "source_min_mean":round(sum(v["source_min"] for v in vals)/len(vals),8),
                "source_max_mean":round(sum(v["source_max"] for v in vals)/len(vals),8),
                "model_mean":round(sum(v["model"] for v in vals)/len(vals),8),
                "source_strictly_greater_with_all_tied_centres":sum(
                    v["source_min"]>v["model"] for v in vals),
            }
        for region in ("all_paint","above_wheel_only"):
            bounds=[r["painted_centroid_distance_envelopes_physical_px"][region]
                    for r in part]
            output["centroid_distance_"+region]={
                "mean_min_physical_px":round(
                    sum(x["min"] for x in bounds)/len(bounds),8),
                "mean_max_physical_px":round(
                    sum(x["max"] for x in bounds)/len(bounds),8),
                "distinct_masks_with_min_distance_above_3px":sum(
                    x["min"]>3 for x in bounds),
            }
        output["masks_where_ignoring_near_wheel_paint_reduces_centroid_error"] = sum(
            r["painted_centroid_distance_envelopes_physical_px"]["above_wheel_only"]["max"] <
            r["painted_centroid_distance_envelopes_physical_px"]["all_paint"]["min"]
            for r in part)
        return output
    summary={"all35":summarize(result)}
    if families:
        for name in ("first16","additional19"):
            summary[name]=summarize([r for r in result if r["source_family"]==name])
    return {"summary":summary,"per_original_binary_mask":result}


def evaluate(corpus_zip:Path,glb_path:Path,camera_path:Path,
             chroma_path:Path,split_path:Path|None=None,direction:int=1):
    raw=chroma_path.read_bytes()
    if _sha(raw)!=CHROMA_SHA:
        raise ValueError("not original ROM-source painted-axis receipt")
    chroma=json.loads(raw)
    original=original_source_paint(corpus_zip,chroma)
    model=historical_model_paint(glb_path,camera_path,direction)
    family=None
    if split_path is not None:
        split=split_path.read_bytes()
        if _sha(split)!=SPLIT_SHA:
            raise ValueError("source-family split SHA differs")
        shape=json.loads(split)["leakage_free_window_split"]
        family={s:"first16" for s in shape["fit_binary_shas"]}
        family.update({s:"additional19" for s in shape["withheld_binary_shas"]})
    report=compare_shapes(chroma,original,model,family)
    return {"schema":SCHEMA,"original_usa_rom_sha256":ORIGINAL_ROM_SHA256,
            "source_corpus_manifest_sha256":CORPUS_MANIFEST_SHA256,
            "original_source_2d_chroma_receipt_sha256":CHROMA_SHA,
            "historical_unapproved_2026_glb_sha256":MODEL_SHA,
            "frozen_uncalibrated_camera_sha256":CAMERA_SHA,
            "observed_hypothetical_camera_direction_world_y":direction,
            "source_original_game_3d_material_correspondence_recovered":False,
            "source_original_game_camera_or_animation_timing_authenticated":False,
            "whole_model_geometry_modified":False,"owner_likeness_approved":False,
            "shipping_art_approved":False,
            **report}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-zip",type=Path,required=True)
    parser.add_argument("--glb",type=Path,required=True)
    parser.add_argument("--camera",type=Path,required=True)
    parser.add_argument("--source-chroma",type=Path,required=True)
    parser.add_argument("--family-split",type=Path)
    parser.add_argument("--view-y",type=int,choices=(-1,1),default=1)
    parser.add_argument("--out",type=Path,required=True)
    opts=parser.parse_args()
    report=evaluate(opts.corpus_zip,opts.glb,opts.camera,
                    opts.source_chroma,opts.family_split,opts.view_y)
    publish_text_once(opts.out,json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report["summary"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
