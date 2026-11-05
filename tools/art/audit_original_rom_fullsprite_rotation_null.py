#!/usr/bin/env python3
"""Do the original ROM's 64 orientations encode new views or mostly 2D rotation?

Compare genuine full 64x64 source 4bpp frames across four fixed source phases,
with zero per-angle translations, cameras, colour mappings or 3D parameters.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.recover_original_mesen24_rom_pose_ids import (
    ROM_SHA, source_frame_tiles, render_original_primary_sprite64,
)
from tools.art.analyze_original_rom_phase_support_2d_null import even_index_harmonic
from tools.art.analyze_original_rom_phase_orbit import SOURCE_SHA, SOURCE_SCHEMA

SCHEMA = "UR-ART4K-ORIGINAL-ROM-WHOLE-SPRITE-2D-ROTATION-IDENTIFIABILITY/1"
PHASES = (0, 6, 12, 18)
ODD_ANGLES = tuple(range(1, 64, 2))
SIZE = 64


def rigid_rotation_indices(plane: bytes, angle: int,
                           pivot_x: float, pivot_y: float) -> bytes:
    if (not isinstance(plane,bytes) or len(plane)!=4096 or
            any(v>15 for v in plane) or
            type(angle) is not int or not 0<=angle<64 or
            not math.isfinite(pivot_x) or not math.isfinite(pivot_y)):
        raise ValueError("original 64x64 4bpp plane/angle/pivot required")
    theta=2*math.pi*angle/64
    c,s=math.cos(theta),math.sin(theta)
    out=bytearray(4096)
    for y in range(SIZE):
        dy=y-pivot_y
        for x in range(SIZE):
            dx=x-pivot_x
            sx=math.floor(pivot_x+c*dx+s*dy+0.5)
            sy=math.floor(pivot_y-s*dx+c*dy+0.5)
            if 0<=sx<64 and 0<=sy<64:
                out[y*64+x]=plane[sy*64+sx]
    return bytes(out)


def score(original: bytes, predicted: bytes) -> dict:
    if (not isinstance(original,bytes) or not isinstance(predicted,bytes) or
            len(original)!=4096 or len(predicted)!=4096 or
            any(v>15 for v in original) or any(v>15 for v in predicted)):
        raise ValueError("original planar 4bpp source sprite comparison required")
    hit=fp=fn=exact_colour=wrong_colour=0
    for src,model in zip(original,predicted):
        if src and model:
            hit+=1
            if src==model:exact_colour+=1
            else:wrong_colour+=1
        elif model:fp+=1
        elif src:fn+=1
    return {
        "alpha_intersection":hit, "alpha_predicted_only":fp,
        "alpha_source_only":fn,
        "source_opaque_pixels":hit+fn,
        "predicted_opaque_pixels":hit+fp,
        "exact_original_4bpp_index_matches_in_overlap":exact_colour,
        "different_original_4bpp_indices_in_overlap":wrong_colour,
        "alpha_iou":round(hit/(hit+fp+fn),8) if hit+fp+fn else 1.0,
        "opaque_exact_index_recall":round(exact_colour/(hit+fn),8)
            if hit+fn else 1.0,
    }


def audit(rom:bytes, axis_raw:bytes) -> dict:
    if hashlib.sha256(axis_raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("wrong original ROM source-axis SHA")
    source=json.loads(axis_raw)
    if (source.get("schema")!=SOURCE_SCHEMA or
            source.get("original_ROM_24phase_64angle_exact_source_frame_count")!=1536 or
            source.get("original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered") is not False):
        raise ValueError("original ROM source-axis evidence invalid")
    boxes=source["source_phase_variation_bbox_by_ROM_angle_index"]
    if not isinstance(boxes,dict) or set(boxes)!={str(i) for i in range(64)}:
        raise ValueError("original source 64-angle support incomplete")
    xcentres=[(boxes[str(a)][0]+boxes[str(a)][2])/2 for a in range(64)]
    ycentres=[(boxes[str(a)][1]+boxes[str(a)][3])/2 for a in range(64)]
    xfit=even_index_harmonic(xcentres)
    yfit=even_index_harmonic(ycentres)
    pivot_x,pivot_y=xfit["mean"],yfit["mean"]
    frames=source_frame_tiles(rom)
    if len(frames)!=1536:
        raise ValueError("not all original 24 x 64 source frames recovered")
    rows=[]
    for phase in PHASES:
        reference=render_original_primary_sprite64(frames[phase*64])
        for a in ODD_ANGLES:
            target=render_original_primary_sprite64(frames[phase*64+a])
            static=score(target,reference)
            rigid=score(target,rigid_rotation_indices(reference,a,pivot_x,pivot_y))
            rows.append({
                "original_ROM_phase_index":phase,
                "original_ROM_orientation_index":a,
                "source_opaque_pixels":rigid["source_opaque_pixels"],
                "original_orientation_zero_reference_4bpp_sha256":
                    hashlib.sha256(reference).hexdigest(),
                "source_full_target_index4_sha256":hashlib.sha256(target).hexdigest(),
                "static_2D_sprite":static,
                "one_pivot_2D_rigid_rotation":rigid,
            })
    aggregate={}
    for arm in ("static_2D_sprite","one_pivot_2D_rigid_rotation"):
        scores=[r[arm] for r in rows]
        tp=sum(x["alpha_intersection"] for x in scores)
        fp=sum(x["alpha_predicted_only"] for x in scores)
        fn=sum(x["alpha_source_only"] for x in scores)
        paint=sum(x["exact_original_4bpp_index_matches_in_overlap"] for x in scores)
        aggregate[arm]={
            "source_sprite_observations":len(rows),
            "source_phase_count":len(PHASES),
            "original_odd_orientation_count":len(ODD_ANGLES),
            "pooled_alpha_iou":round(tp/(tp+fp+fn),8),
            "mean_one_sprite_alpha_iou":round(
                sum(x["alpha_iou"] for x in scores)/len(scores),8),
            "pooled_source_opaque_index_exact_recall":round(paint/(tp+fn),8),
            "source_opaque_alpha_intersection":tp,
            "source_opaque_alpha_false_positive":fp,
            "source_opaque_alpha_false_negative":fn,
            "original_4bpp_exact_matching_opaque_pixels":paint,
            "original_4bpp_differing_opaque_intersection":
                sum(x["different_original_4bpp_indices_in_overlap"] for x in scores),
        }
    by_phase={}
    for p in PHASES:
        subset=[row for row in rows if row["original_ROM_phase_index"]==p]
        by_phase[str(p)]={
            arm:round(sum(row[arm]["alpha_iou"] for row in subset)/len(subset),8)
            for arm in aggregate}
    return {
        "schema":SCHEMA,
        "source_authenticated_original_USA_ROM_SHA256":ROM_SHA,
        "source_axis_counterfactual_SHA256":SOURCE_SHA,
        "source_original_phase_indices_tested":list(PHASES),
        "source_original_orientation_indices_tested":list(ODD_ANGLES),
        "source_rotation_2pi_per_64_index_is_uncalibrated_2D_null":True,
        "source_pivot_fit_even_orientation_indices_only":True,
        "source_fixed_pivot_source_pixels":[pivot_x,pivot_y],
        "source_7_6_aspect_correction_not_applied_to_raw_PPU_plane":True,
        "full_original_4bpp_colour_indices_not_just_alpha_tested":True,
        "already_inspected_ROM_frame_manifold_NOT_prospective_blind":True,
        "independent_1994_3D_camera_or_viewpoint_recovered":False,
        "owner_2026_character_likeness_approved":False,
        "aggregate":aggregate, "mean_alpha_iou_by_phase":by_phase,
        "per_original_source_sprite":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--original-axis-report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.rom.read_bytes(),a.original_axis_report.read_bytes())
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ART4K_ORIGINAL_ROM_FULL_SPRITE_ROTATION_NULL",
          json.dumps({"aggregate":result["aggregate"],
                      "by_phase":result["mean_alpha_iou_by_phase"]},sort_keys=True))


if __name__=="__main__":
    main()
