#!/usr/bin/env python3
"""Measure actual unchanged five-parent 2026 GLB 64px image-band occupancy.

The original ROM/1994 artwork supplies only the fixed *image-space* band
boundaries. Part labels describe the existing 2026 SCAD model, not recovered
1994 3D anatomy, physical camera, or original source material identities.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.glb_parent_part_id_raster import PARTS, validated_camera
from tools.art.experimental_direct_drive_phase import CHILD_COUNTS
from tools.art.render_racer_glb_projection import render_mask
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-SOURCE-Y-BAND-REAL-2026-GLB-PARENT-CENSUS/1"
SOURCE_SCAD_SHA="e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
SOURCE_Y_BANDS=(("upper_y0_14",0,14),
                ("middle_y15_26",15,26),
                ("lower_y27_63",27,63))
# Previously verified identical source 2026 upright GLB under this provisional
# 7:6 camera. Exact source GLB file bytes may vary by exporter attempt, so
# these *rasterised part counts* are a useful geometry consistency check.
CANONICAL_TOTAL=267
CANONICAL_PARTS={"tire":124,"rim_and_hub":70,"fork_and_frame":46,
                 "pedals":14,"saddle":56}


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def count_parts(source64_by_part:dict[str,bytes])->dict:
    """Count part occupancy and *exclusive* silhouette pixels per y band.

    In model geometry, individual projected parent silhouettes can overlap.
    Individual part totals must never be summed to infer union occupancy.
    """
    if (not isinstance(source64_by_part,dict) or
            set(source64_by_part)!=set(PARTS) or
            any(type(value) is not bytes or len(value)!=4096 or
                set(value)-{0,1} or not any(value)
                for value in source64_by_part.values())):
        raise ValueError("all five real 64x64 source-coordinate binary parent masks required")
    masks=list(source64_by_part.values())
    full=bytes(int(any(x[k] for x in masks)) for k in range(4096))
    report={}
    for name,low,high in SOURCE_Y_BANDS:
        union_count=sum(full[low*64:(high+1)*64])
        components={}
        for part,mask in source64_by_part.items():
            support=sum(mask[low*64:(high+1)*64])
            exclusive=sum(mask[k] and not any(
                source64_by_part[other][k] for other in PARTS if other!=part)
                for k in range(low*64,(high+1)*64))
            if exclusive>support:
                raise ValueError("exclusive source parent occupancy exceeds its own pixels")
            components[part]={"projected_source64_occupied_pixels":support,
                              "unique_union_silhouette_pixels":exclusive}
        report[name]={"source_y_range_inclusive":[low,high],
                      "whole_actual_2026_model_opaque_pixels":union_count,
                      "per_2026_parent":components}
    whole_parts={name:sum(
        report[band]["per_2026_parent"][name]["projected_source64_occupied_pixels"]
        for band,_,_ in SOURCE_Y_BANDS) for name in PARTS}
    if sum(report[band]["whole_actual_2026_model_opaque_pixels"]
           for band,_,_ in SOURCE_Y_BANDS)!=sum(full):
        raise ValueError("source y-band census does not partition 64px silhouette")
    return {
        "full_2026_model_union_64px_pixels":sum(full),
        "full_2026_model_part_occupancy_before_union":whole_parts,
        "per_source_y_band":report,
        "source_y_bands_partition_all_64_rows":True,
        "model_parent_support_is_additive_only_within_each_parent":True,
    }


def scene_part_source_masks(scene,camera:dict)->dict[str,bytes]:
    """Exact 2026 scene-graph source64 part supports for any fixed pose.

    Uses the same 7:6 camera and 4x source-centre sampling as the canonical
    real-GLB union renderer. Parent membership is projected support, not a
    recovered 1994 source-material assignment or 3D visibility oracle.
    """
    import numpy as np
    import trimesh
    validated_camera(camera)
    masks=scene_part_source_masks(scene,camera)

    return masks


def actual_part_source_masks(verified_exports:Path,camera_path:Path)->dict:
    """Use only a source-verified canonical GLB export attempt (not any GLB)."""
    import numpy as np
    import trimesh
    if not isinstance(verified_exports,Path) or not isinstance(camera_path,Path):
        raise ValueError("existing real export root and camera file required")
    camera_raw=camera_path.read_bytes()
    if sha(camera_raw)!=CAMERA_SHA:
        raise ValueError("provisional source camera SHA changed")
    camera=json.loads(camera_raw)
    validated_camera(camera)
    validate=runpy.run_path(str(Path(__file__).resolve().parent /
                                "model-review/stage_pages.py"))["validate"]
    pointer,outputs=validate(verified_exports,"upright")
    source=outputs["glb"].read_bytes()
    if (pointer["source_sha256"]!=SOURCE_SCAD_SHA or
            pointer["glb_sha256"]!=sha(source) or
            source[:4]!=b"glTF"):
        raise ValueError("not the current successful source-authenticated 2026 GLB")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)
    if (not isinstance(scene,trimesh.Scene) or
            not set(PARTS).issubset(scene.graph.nodes) or
            len(scene.graph.nodes_geometry)!=16):
        raise ValueError("not the canonical five-parent, sixteen-material real model")
    by_part={p:[] for p in PARTS}
    for name in sorted(scene.graph.nodes_geometry):
        part=name.split("__material_",1)[0]
        if part not in by_part or scene.graph.transforms.parents.get(name)!=part:
            raise ValueError("unexpected material mesh parent")
        transform,geometry=scene.graph.get(name)
        mesh=scene.geometry[geometry]
        if not isinstance(mesh,trimesh.Trimesh) or len(mesh.faces)==0:
            raise ValueError("real source model material geometry missing")
        world=mesh.copy()
        world.apply_transform(transform)
        by_part[part].append((world.vertices,world.faces))
    masks={}
    for part,records in by_part.items():
        if len(records)!=CHILD_COUNTS[part]:
            raise ValueError("2026 original material geometry child census changed")
        vertices=np.concatenate([v for v,_ in records])
        offset=0
        faces=[]
        for v,f in records:
            faces.append(f+offset)
            offset+=len(v)
        alpha=render_mask(vertices,np.concatenate(faces),camera)
        masks[part]=bytes(alpha[2::4,2::4].astype(np.uint8).ravel())
    census=count_parts(masks)
    if (census["full_2026_model_union_64px_pixels"]!=CANONICAL_TOTAL or
            census["full_2026_model_part_occupancy_before_union"]!=CANONICAL_PARTS):
        raise ValueError("authentic current 2026 geometry no longer matches previous 7:6 raster")
    return {
        "schema":SCHEMA,
        "unapproved_2026_authored_SCAD_sha256":SOURCE_SCAD_SHA,
        "attempt_specific_source_verified_upright_GLB_sha256":pointer["glb_sha256"],
        "original_provisional_fixed_side_camera_sha256":CAMERA_SHA,
        "true_GLb_material_child_mesh_count":16,
        "true_GLb_part_parent_count":5,
        "source64_sampling":"4*x+2, 4*y+2, 7:6 display aspect",
        "part_occupancy_derived_only_from_existing_2026_GLb_geometry":True,
        "source_image_y_bands_are_original_2D_regions_not_1994_part_labels":True,
        "original_1994_camera_mesh_material_or_joint_recovered":False,
        "source_to_2026_GLb_pose_map_recovered":False,
        "owner_likeness_approved":False,
        "existing_2026_rig_original_geometry_unchanged":True,
        **census,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verified-exports",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=actual_part_source_masks(a.verified_exports,a.camera)
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("OK ART4K_REAL_2026_GLB_SOURCE_UPPER_PARENT_CENSUS",
          json.dumps({
              "source_GLB_sha256":result["attempt_specific_source_verified_upright_GLB_sha256"],
              "bands":result["per_source_y_band"],
          },sort_keys=True))


if __name__=="__main__":
    main()
