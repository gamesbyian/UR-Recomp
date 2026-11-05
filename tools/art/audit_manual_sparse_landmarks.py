#!/usr/bin/env python3
"""Authenticate sparse 2D figure observations from the retained 1994 manual.

Print illustrations can show a fork crown without a visible whole wheel.
Never invent occluded wheels, saddle bounds or an original 3D camera merely
to satisfy a complete original-gameplay silhouette schema.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from tools.art.extract_manual_3d_reference_views import (
    FIGURES, SCHEMA as CROP_SCHEMA, SOURCE, SOURCE_BLOB_SHA1, authenticate_pdf,
)
from tools.art.validate_upscale_trials import check_identity

SCHEMA="UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1"
REPORT_SCHEMA="UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D-REPORT/1"
# These are *printed image-plane coordinates*. No part is asserted to be
# original gameplay 3D geometry or an independent source-game camera.
PARTS={
    "wheel":("wheel_left","wheel_right","wheel_top","wheel_bottom"),
    "hub":("hub_left","hub_right","hub_top","hub_bottom"),
    "saddle":("saddle_left","saddle_right","saddle_top","saddle_bottom"),
    "crown":("crown_left","crown_right"),
    "fork":("fork_left","fork_right"),
    "clamp":("clamp_top","clamp_bottom"),
    "crank":("crank_root","pedal_center"),
}


def fail(message:str):
    raise ValueError(message)


def point(value,dimensions,name):
    if (type(value) is not list or len(value)!=2 or
            any(type(v) not in (int,float) or not math.isfinite(v)
                for v in value)):
        fail(name+": finite [x,y] source crop coordinates required")
    x,y=value
    if not (0<=x<dimensions[0] and 0<=y<dimensions[1]):
        fail(name+": 2D point outside authenticated original crop")
    return (float(x),float(y))


def bounds(points,part):
    if part in ("wheel","hub","saddle"):
        left,right,top,bottom=(points[name] for name in PARTS[part])
        if left[0]>=right[0] or top[1]>=bottom[1]:
            fail(part+": original print image-plane box inverted")
        return {"width_px":round(right[0]-left[0],6),
                "height_px":round(bottom[1]-top[1],6)}
    if part in ("crown","fork"):
        left,right=(points[name] for name in PARTS[part])
        if left[0]>=right[0]:
            fail(part+": original print lateral width inverted")
        return {"width_px":round(right[0]-left[0],6)}
    if part=="clamp":
        top,bottom=(points[name] for name in PARTS[part])
        if top[1]>=bottom[1]:
            fail(part+": original print clamp top/bottom inverted")
        return {"height_px":round(bottom[1]-top[1],6)}
    a,b=(points[name] for name in PARTS[part])
    return {"projected_endpoint_separation_px":
            round(math.hypot(a[0]-b[0],a[1]-b[1]),6)}


def authenticated_crops(folder:Path, raw_pdf:bytes,
                        expected_blob=SOURCE_BLOB_SHA1)->dict:
    auth=authenticate_pdf(raw_pdf,expected_blob)
    receipt=json.loads((folder/"source-crops.json").read_text(encoding="utf-8"))
    if (not isinstance(receipt,dict) or receipt.get("schema")!=CROP_SCHEMA
            or receipt.get("source_pdf_sha256")!=auth["source_pdf_sha256"]
            or receipt.get("source_git_blob_sha1")!=auth["source_git_blob_sha1"]
            or receipt.get("source_pdf_size_bytes")!=auth["source_pdf_size"]
            or receipt.get("printed_manual_page_count")!=40
            or receipt.get("render_dpi")!=144
            or receipt.get("shipping_art_approved") is not False
            or receipt.get("same_historical_3d_mesh_as_source_game_proven") is not False):
        fail("manual crop manifest is not source-PDF authenticated")
    rows=receipt.get("figures")
    if not isinstance(rows,list) or len(rows)!=len(FIGURES):
        fail("complete four-view original manual crop manifest required")
    registered={}
    for fixed,row in zip(FIGURES,rows):
        name,index,original_box,angle,notes=fixed
        if (not isinstance(row,dict) or row.get("reference_id")!=name
                or row.get("original_pdf_zero_based_page")!=index
                or row.get("original_printed_page")!=index+1
                or row.get("page_crop_basis_xyxy")!=list(original_box)
                or row.get("approximate_print_view")!=angle
                or row.get("historical_3d_camera_or_material_identity_verified") is not False
                or row.get("human_landmarks_measured") is not False
                or row.get("crop_png")!=name+".png"):
            fail("original manual source figure/order/page/view identity changed: "+name)
        image_meta={"path":row["crop_png"],"sha256":row.get("crop_png_sha256")}
        _,(w,h,_)=check_identity(folder,image_meta,name)
        a,b,c,d=row.get("page_crop_pixels_xyxy",[])
        if (type(a) is not int or type(b) is not int
                or type(c) is not int or type(d) is not int
                or (w,h)!=(c-a,d-b)):
            fail("real source PNG dimensions must equal original PDF crop: "+name)
        registered[name]={"dims":(w,h),"receipt":row}
    return {"pdf":auth,"figures":registered}


def measure(annotation:dict,folder:Path,raw_pdf:bytes,
            expected_blob=SOURCE_BLOB_SHA1)->dict:
    source=authenticated_crops(folder,raw_pdf,expected_blob)
    if (not isinstance(annotation,dict) or annotation.get("schema")!=SCHEMA
            or annotation.get("source_pdf_sha256")!=source["pdf"]["source_pdf_sha256"]):
        fail("annotations must identify authenticated PDF SHA-256 and sparse schema")
    samples=annotation.get("annotations")
    if not isinstance(samples,list) or not samples:
        fail("at least one visible original manual figure observation required")
    seen=set()
    report=[]
    for record in samples:
        if not isinstance(record,dict):
            fail("manual figure annotation must be an object")
        name=record.get("reference_id")
        if name not in source["figures"] or name in seen:
            fail("original manual figure must be unique and known")
        seen.add(name)
        uncertainty=record.get("pixel_uncertainty")
        if (type(uncertainty) not in (int,float) or
                not math.isfinite(uncertainty) or not 0<uncertainty<=100):
            fail("nonzero finite landmark pixel uncertainty required")
        reviewer=record.get("annotator")
        context=record.get("perspective_and_occlusion_notes")
        if (not isinstance(reviewer,str) or not reviewer.strip()
                or reviewer.startswith("UNANNOTATED")
                or not isinstance(context,str) or len(context.strip())<12):
            fail("actual reviewer and print perspective/occlusion rationale required")
        observed=record.get("visible_points")
        hidden=record.get("unmeasurable")
        if not isinstance(observed,dict) or not isinstance(hidden,dict):
            fail("explicit visible original 2D points and unmeasurable reasons required")
        if set(observed)&set(hidden) or set(observed)|set(hidden)!=set(PARTS):
            fail("each original print part must be observed OR explicitly unmeasurable")
        dimensions=source["figures"][name]["dims"]
        readings={}
        landmarks={}
        for part,names in PARTS.items():
            if part in hidden:
                reason=hidden[part]
                if not isinstance(reason,str) or len(reason.strip())<8:
                    fail(part+": explain original print occlusion")
                continue
            raw=observed[part]
            if not isinstance(raw,dict) or set(raw)!=set(names):
                fail(part+": complete visible landmark group required, otherwise mark occluded")
            pts={key:point(raw[key],dimensions,key) for key in names}
            readings[part]=bounds(pts,part)
            landmarks[part]={key:list(pts[key]) for key in names}
        if not readings:
            fail("do not emit measurements of an entirely obscured figure")
        wheel_diameter=readings.get("wheel",{}).get("height_px")
        normalized={}
        for part,dimensions_px in readings.items():
            normalized[part]={
                key.replace("_px","_over_projected_wheel_diameter"):
                    round(value/wheel_diameter,6) if wheel_diameter else None
                for key,value in dimensions_px.items()
            }
        report.append({
            "reference_id":name,
            "source_original_print_page":
                source["figures"][name]["receipt"]["original_printed_page"],
            "crop_png_sha256":
                source["figures"][name]["receipt"]["crop_png_sha256"],
            "crop_dimensions_pixels":list(dimensions),
            "view_approximation":
                source["figures"][name]["receipt"]["approximate_print_view"],
            "original_print_pixel_aspect":"square",
            "annotator":reviewer,
            "pixel_uncertainty":float(uncertainty),
            "perspective_and_occlusion_notes":context,
            "visible_points":landmarks,"unmeasurable":hidden,
            "projected_pixel_distances":readings,
            "projected_ratios_only_if_whole_wheel_visible":normalized,
            "historical_1994_3d_camera_calibrated":False,
            "original_source_mesh_dimensions_recovered":False,
        })
    return {
        "schema":REPORT_SCHEMA,
        "authenticated_source_pdf_sha256":source["pdf"]["source_pdf_sha256"],
        "authenticated_pdf_git_blob_sha1":source["pdf"]["source_git_blob_sha1"],
        "reviewed_print_figure_count":len(report),
        "observations":report,
        "print_observations_are_independent_original_game_3d_views":False,
        "three_dimensional_source_geometry_calibrated":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("annotation_json",type=Path)
    p.add_argument("--crop-dir",type=Path,required=True)
    p.add_argument("--source-pdf",type=Path,default=SOURCE)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    report=measure(json.loads(args.annotation_json.read_text(encoding="utf-8")),
                   args.crop_dir,args.source_pdf.read_bytes())
    rendered=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if args.out:
        if args.out.exists():
            fail("never overwrite earlier source review receipt")
        args.out.write_text(rendered,encoding="utf-8")
    print(rendered,end="")


if __name__=="__main__":
    main()
