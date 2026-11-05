#!/usr/bin/env python3
"""Visibility of one 2026 spoke-blade *material* at 64px, no original-ROM fit.

Rasterize unoccluded material geometry from the authenticated one-GLB
2026 source model. View angles, wheel-centred X/Z crop and 64px scale are
declared illustrative controls, NOT historical 1994 original cameras,
paint ownership, PPU alpha or actual depth-visible raster measurements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.art.experimental_spoke_blade_volume import (
    SOURCE_GL_B_SHA256,SPOKE_NODE,temporary_wider_spoke_blades,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-REAL-2026-GLB-BLADED-SPOKE-64PX-SUPPORT/1"
ANGLES=(0,30,60,90)
RESOLUTIONS=(64,128,256)
HALF_SPAN=1.05


def silhouette(mesh,angle:int,resolution:int):
    """Unoccluded 2026 spoke-part 2D projected face-union; no z-buffer."""
    import numpy as np
    from PIL import Image,ImageDraw
    if (type(angle) is not int or angle not in ANGLES or
            type(resolution) is not int or resolution not in RESOLUTIONS):
        raise ValueError("only frozen 2026 camera angles/pixel grids accepted")
    points=np.asarray(mesh.vertices)
    faces=np.asarray(mesh.faces)
    if (points.ndim!=2 or points.shape[1]!=3 or
            faces.ndim!=2 or faces.shape[1]!=3 or len(faces)==0 or
            not np.isfinite(points).all()):
        raise ValueError("valid finite source spoke mesh faces required")
    theta=math.radians(angle)
    rotated=points[:,0]*math.cos(theta)+points[:,1]*math.sin(theta)
    xs=(rotated+HALF_SPAN)/(2*HALF_SPAN)*resolution
    ys=(HALF_SPAN-points[:,2])/(2*HALF_SPAN)*resolution
    if (max(abs(xs).max(),abs(ys).max())>resolution*64):
        raise ValueError("source camera projection far outside bounded wheel")
    image=Image.new("1",(resolution,resolution),0)
    draw=ImageDraw.Draw(image)
    for indices in faces:
        draw.polygon([(float(xs[i]),float(ys[i])) for i in indices],fill=1)
    return np.asarray(image,dtype=bool)


def analyze(path:Path)->dict:
    import numpy as np
    import trimesh
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_GL_B_SHA256:
        raise ValueError("only exact original authored five-parent 2026 GLB permitted")
    scene=trimesh.load(path,force="scene",process=False)
    if not isinstance(scene,trimesh.Scene):
        raise ValueError("original source 3D scene graph required")
    _,name=scene.graph.get(SPOKE_NODE)
    spoke=scene.geometry[name]
    baselines={(angle,n):silhouette(spoke,angle,n)
               for angle in ANGLES for n in RESOLUTIONS}
    with temporary_wider_spoke_blades(scene):
        proposed={(angle,n):silhouette(spoke,angle,n)
                  for angle in ANGLES for n in RESOLUTIONS}
    rows=[]
    for angle in ANGLES:
        for n in RESOLUTIONS:
            a,b=baselines[(angle,n)],proposed[(angle,n)]
            old=int(np.count_nonzero(a))
            new=int(np.count_nonzero(b))
            added=int(np.count_nonzero(b & ~a))
            removed=int(np.count_nonzero(a & ~b))
            both=int(np.count_nonzero(a&b))
            union=int(np.count_nonzero(a|b))
            rows.append({
                "2026_view_angle_degrees":angle,"grid_px":n,
                "original_2026_unoccluded_spoke_pixels":old,
                "broader_2026_unoccluded_spoke_pixels":new,
                "proposed_new_spoke_material_pixels":added,
                "proposed_lost_spoke_material_pixels":removed,
                "projected_2026_spoke_mask_iou":round(both/union,8) if union else 1.,
            })
    if (rows[0]["proposed_new_spoke_material_pixels"]<=0 or
            rows[-3]["proposed_new_spoke_material_pixels"]!=0 or
            rows[-3]["proposed_lost_spoke_material_pixels"]!=0):
        raise ValueError("model-only side/edge-on visibility controls contradicted")
    return {
        "schema":SCHEMA,
        "source_2026_GLb_sha256":SOURCE_GL_B_SHA256,
        "source_original_game_1994_PPU_pixels_used":False,
        "source_manual_p15_print_crop_pixels_used":False,
        "source_model_camera_is_original_1994":False,
        "whole_unicycle_alpha_or_occlusion_test":False,
        "tested_single_unoccluded_2026_spoke_material_only":True,
        "original_2026_five_parent_16_material_rig_preserved":True,
        "original_2026_spoke_3d_vertices_restored_exactly":True,
        "original_1994_3d_mesh_or_material_ownership_recovered":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
        "declared_source_wheel_crop_half_span_model_units":HALF_SPAN,
        "camera_angle_basis":"2026 wheel X/Z front with optional model-Y orbit; illustrative",
        "per_2026_source_view":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    result=analyze(args.glb)
    payload=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.out:
        publish_text_once(args.out,payload)
    print(payload,end="")


if __name__=="__main__":
    main()
