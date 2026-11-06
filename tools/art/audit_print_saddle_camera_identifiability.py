#!/usr/bin/env python3
"""Bound what TWO uncalibrated original 1994 printed saddles can constrain.

The authentic 1994 image-plane observations are not 3D camera measurements.
Enumerate frozen orthographic yaw/elevation views of the SAME five-parent
unapproved 2026 GLB to show whether perspective can account for both 2D
aspect ratios without changing any vertices. No source fitting, shape
adoption or original-game camera reconstruction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-PRINT-2D-VERSUS-2026-SADDLE-CAMERA-IDENTIFIABILITY/1"
ORIGINAL_2026_UPRIGHT_GLB_SHA256="634aa0280ec1a8a322c34d1598680e854980f317965b3a848a2cf6b240c50c08"
ORIGINAL_1994_PRINT_SHA256="50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235"
SOURCE_PRINT_RESULT="analysis/data/racer-original-manual-saddle-2d-pdf-verified-20261105.json"
YAW_DEGREES=tuple(range(0,181,5))
ELEVATION_DEGREES=tuple(range(-70,71,5))
SOURCE_SADDLE_NODES={"saddle__material_0":1393,"saddle__material_1":1315}
ORIGINAL_SADDLE_PRINTS={
 "p14-twist-fork-front":(
     "cfbbc7b3e3cd1e3786897eba580bffec2ee9ceec268bcf4cdb4b5b6e30f4642b",
     14,154,66,8),
 "p15-mega-underside":(
     "4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22",
     15,318,273,14),
}


def verify_print_report(report:dict)->list[dict]:
    if (not isinstance(report,dict) or report.get("schema")!=
            "UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D-REPORT/1"
            or report.get("authenticated_source_pdf_sha256")!=ORIGINAL_1994_PRINT_SHA256
            or report.get("reviewed_print_figure_count")!=2
            or report.get("three_dimensional_source_geometry_calibrated") is not False
            or report.get("owner_character_likeness_approved") is not False
            or report.get("shipping_art_approved") is not False):
        raise ValueError("two original source-PDF-reviewed printed saddle observations required")
    rows=report.get("observations")
    if not isinstance(rows,list) or len(rows)!=2:
        raise ValueError("exact original p14/p15 printed source observations required")
    found={}
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("invalid original print entry")
        key=row.get("reference_id")
        if key not in ORIGINAL_SADDLE_PRINTS or key in found:
            raise ValueError("duplicate/unknown source original printed figure")
        sha,page,w,h,unc=ORIGINAL_SADDLE_PRINTS[key]
        saddle=row.get("projected_pixel_distances",{}).get("saddle",{})
        ratios=row.get("projected_ratios_only_if_whole_wheel_visible",{}).get("saddle",{})
        if (row.get("crop_png_sha256")!=sha
                or row.get("source_original_print_page")!=page
                or row.get("pixel_uncertainty")!=unc
                or row.get("original_print_pixel_aspect")!="square"
                or row.get("historical_1994_3d_camera_calibrated") is not False
                or row.get("original_source_mesh_dimensions_recovered") is not False
                or saddle!={"height_px":float(h),"width_px":float(w)}
                or set(row.get("visible_points",{}))!={"saddle"}
                or set(row.get("unmeasurable",{}))!=
                     {"wheel","hub","crown","fork","clamp","crank"}
                or not ratios or any(v is not None for v in ratios.values())):
            raise ValueError("original print source crop/2D saddle measurements changed")
        found[key]=row
    if set(found)!=set(ORIGINAL_SADDLE_PRINTS):
        raise ValueError("both original source print views required")
    return [found[key] for key in ORIGINAL_SADDLE_PRINTS]


def camera_aspect_ratio(source_vertices,yaw:int,elevation:int)->float:
    """Bounds of 2026 model saddle vertices under one arbitrary orthographic orbit.

    This is a model-only vertex *envelope*, not the true printed 1994 render
    silhouette, a z-buffered contour, a registration or calibrated lens.
    """
    import numpy as np
    if (type(yaw) is not int or yaw not in YAW_DEGREES or
            type(elevation) is not int or elevation not in ELEVATION_DEGREES):
        raise ValueError("frozen 2026 camera grid only")
    v=np.asarray(source_vertices,dtype=float)
    if v.ndim!=2 or v.shape[1]!=3 or not 3<=len(v)<=100000 or not np.isfinite(v).all():
        raise ValueError("finite 2026 model saddle XYZ required")
    a,b=math.radians(yaw),math.radians(elevation)
    right=v[:,0]*math.cos(a)-v[:,1]*math.sin(a)
    up=v[:,0]*(-math.sin(a)*math.sin(b))+v[:,1]*(-math.cos(a)*math.sin(b))+v[:,2]*math.cos(b)
    height=float(np.ptp(up))
    width=float(np.ptp(right))
    if height<=1e-9 or width<=1e-9:
        raise ValueError("projected source saddle degenerate")
    return width/height


def compare_source_model(glb:Path,source_report:Path)->dict:
    raw=glb.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_2026_UPRIGHT_GLB_SHA256:
        raise ValueError("require exact original source-qualified 2026 upright GLB SHA")
    report=json.loads(source_report.read_text(encoding="utf-8"))
    prints=verify_print_report(report)
    import numpy as np
    import trimesh
    scene=trimesh.load(glb,force="scene",process=False)
    if (not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world"
            or len(scene.geometry)!=16 or set(scene.graph.nodes_geometry)!=set(scene.geometry)):
        raise ValueError("one original authored five-parent/16-material GLB required")
    for part,size in SOURCE_SADDLE_NODES.items():
        if part not in scene.geometry or len(scene.geometry[part].vertices)!=size:
            raise ValueError("original 2026 source saddle shape/mesh version changed")
    vertices=np.vstack([scene.geometry[n].vertices for n in SOURCE_SADDLE_NODES])
    assert vertices.shape==(2708,3)
    rays=[(yaw,elev,camera_aspect_ratio(vertices,yaw,elev))
          for yaw in YAW_DEGREES for elev in ELEVATION_DEGREES]
    if len(rays)!=1073:
        raise ValueError("source 2026 camera census incomplete")
    summaries=[]
    for row in prints:
        w=row["projected_pixel_distances"]["saddle"]["width_px"]
        h=row["projected_pixel_distances"]["saddle"]["height_px"]
        unc=row["pixel_uncertainty"]
        if not 0<2*unc<min(w,h):
            raise ValueError("source 1994 visual uncertainty too large for ratio bounds")
        target=w/h
        lower=(w-2*unc)/(h+2*unc)
        upper=(w+2*unc)/(h-2*unc)
        compatible=[q for q in rays if lower<=q[2]<=upper]
        best=sorted(rays,key=lambda q:(abs(q[2]-target),q[0],q[1]))[0]
        summaries.append({
            "source_original_print_reference_id":row["reference_id"],
            "source_original_print_crop_png_sha256":row["crop_png_sha256"],
            "observed_original_print_image_plane_width_px":w,
            "observed_original_print_image_plane_height_px":h,
            "human_artist_reviewed":False,
            "source_per_point_visual_uncertainty_px":unc,
            "observed_image_plane_width_over_height":round(target,8),
            "uncertainty_propagated_ratio_lower_bound":round(lower,8),
            "uncertainty_propagated_ratio_upper_bound":round(upper,8),
            "matching_2026_model_only_orbits_within_uncertainty":len(compatible),
            "closest_uncalibrated_2026_model_orbit":{
                "yaw_degrees":best[0],"elevation_degrees":best[1],
                "saddle_vertex_envelope_ratio":round(best[2],8),
            },
            "original_1994_artist_camera_estimated":False,
            "original_1994_actual_source_model_geometry_constrained":False,
        })
    return {
        "schema":SCHEMA,
        "source_original_1994_print_pdf_sha256":ORIGINAL_1994_PRINT_SHA256,
        "source_2026_actual_authored_upright_glb_sha256":ORIGINAL_2026_UPRIGHT_GLB_SHA256,
        "source_original_2026_saddle_material_vertex_counts":SOURCE_SADDLE_NODES,
        "source_2026_saddle_total_vertices":len(vertices),
        "experimental_2026_camera_yaw_degrees":list(YAW_DEGREES),
        "experimental_2026_camera_elevation_degrees":list(ELEVATION_DEGREES),
        "total_different_source_model_orthographic_camera_orbits":len(rays),
        "source_2026_model_only_ratio_range":[
            round(min(a[2] for a in rays),8),round(max(a[2] for a in rays),8)],
        "original_print_sources":summaries,
        "uncalibrated_independent_two_print_orbit_pair_combinations":
            math.prod(v["matching_2026_model_only_orbits_within_uncertainty"]
                      for v in summaries),
        "camera_fits_are_anatomical_1994_source_3d_validation":False,
        "observations_constrain_camera_or_model_uniquely":False,
        "original_printed_1994_render_mesh_or_camera_recovered":False,
        "original_game_ROM_64px_PPU_frames_used":False,
        "unapproved_2026_saddle_vertices_or_materials_modified":False,
        "owner_artist_likeness_approved":False,
        "shipping_4k_character_art_approved":False,
        "notes":"Model-only projected vertex bounding envelopes, NOT actual source original 1994 3D rendering; two independent uncalibrated print crops have different scales/occlusions. Numerous camera angle pairs can explain apparent aspect ratios without a physical sculpt.",
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upright-glb",type=Path,required=True)
    p.add_argument("--source-print-report",type=Path,
                   default=Path(SOURCE_PRINT_RESULT))
    p.add_argument("--out",type=Path)
    opts=p.parse_args()
    report=compare_source_model(opts.upright_glb,opts.source_print_report)
    rendered=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if opts.out:
        publish_text_once(opts.out,rendered)
    print(rendered,end="")


if __name__=="__main__":
    main()
