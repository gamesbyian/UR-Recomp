#!/usr/bin/env python3
"""Unpaired 2D painted-axis coverage of five REAL 2026 GLB pose studies.

Compares the same 7:6 side-camera projected raster descriptor as the
authenticated original P1/P2 source chroma audit. No original sprite is
labelled as any of the five experimental GLB poses; nearest angle is merely
a missing-direction diagnostic, not a pose classifier or animation fit.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

try:
    from tools.art.audit_original_racer_chroma_axes import (
        SCHEMA as SOURCE_SCHEMA, CANONICAL_ROM_SHA, painted_axis,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.render_racer_glb_projection import camera_config, render_mask
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_chroma_axes import (
        SCHEMA as SOURCE_SCHEMA, CANONICAL_ROM_SHA, painted_axis,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from render_racer_glb_projection import camera_config, render_mask
    from no_replace_report import publish_text_once

SCHEMA="UR-RACER-UNPAIRED-SOURCE-GLB-PAINTED-AXIS-COVERAGE/1"
COMMIT="d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
POSE_GLB_SHA={
    "upright":"efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5",
    "pedal":"f692277bb9bf215ccc97bc89f44d28378a43ddc9aa45843c4f0ab30e8747db53",
    "wheelie":"859b985d8fc51f994e5e42fd64bc871d493249285454ec836b415ec833f33c27",
    "stunt":"d3375cf4d44d973ca7b4308bfff5b3646087a37d206a2746792c8083483f3212",
    "bank":"50d56b4f702ad655929c17e5cbc4e281386cf6b2fb2cd80e71d0a2e6b672fd59",
}

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def paint_axis_from_model(scene,camera:dict)->dict:
    import numpy as np
    import trimesh
    if not isinstance(scene,trimesh.Scene):
        raise ValueError("actual GLB must contain source-owned scene")
    meshes=[]
    for node in scene.graph.nodes_geometry:
        if node=="fork_and_frame__material_0":
            matrix,key=scene.graph.get(node)
            mesh=scene.geometry[key].copy()
            mesh.apply_transform(matrix)
            meshes.append(mesh)
    if len(meshes)!=1:
        raise ValueError("actual 2026 GLB lacks unique painted fork material")
    mesh=meshes[0]
    mask4=render_mask(mesh.vertices,mesh.faces,camera)
    if mask4.shape!=(256,256):
        raise ValueError("unexpected GLB fixed projection density")
    alpha=mask4[2::4,2::4]
    if alpha.shape!=(64,64):
        raise ValueError("not logical 64x64 original-scale projection")
    # Convert only the blue 2026 experimental GLB paint geometry to the
    # exact same descriptive 2D chroma-mask measurement as source sprites.
    # No claim that the 1994 palette was a 3D material parameter.
    rgba=np.zeros((64,64,4),dtype=np.uint8)
    rgba[alpha!=0]=[28,89,222,255]
    result=painted_axis(rgba.tobytes(),"p2")
    result["source_raster_or_original_1994_3d_material"]=False
    return result

def summarize_unpaired_source_coverage(source_masks:list[dict],
                                       poses:dict[str,dict])->dict:
    if (len(source_masks)<2 or len(poses)!=5 or
            set(poses)!=set(POSE_GLB_SHA)):
        raise ValueError("real five-pose blockout and multiple original masks required")
    axes={}
    for pose,value in poses.items():
        a=value.get("signed_axis_angle_from_image_vertical_deg")
        if type(a) not in (float,int) or not -90<a<90:
            raise ValueError("unbounded experimental model projected painted axis")
        axes[pose]=float(a)
    values=[]
    for source in source_masks:
        angle=source.get("equal_colour_variant_mean_projected_angle_deg")
        sha=source.get("original_binary_mask_sha256")
        if (type(angle) not in (float,int) or not -90<angle<90 or
                not isinstance(sha,str) or len(sha)!=64):
            raise ValueError("invalid authenticated source angle descriptor")
        closest=min(abs(angle-v) for v in axes.values())
        values.append({"source_binary_mask_sha256":sha,
                       "source_image_space_angle_deg":angle,
                       "distance_to_nearest_experimental_pose_axis_deg":round(closest,6)})
    if len({v["source_binary_mask_sha256"] for v in values})!=len(values):
        raise ValueError("repeated exact original source shape counted as separate pose")
    gaps=sorted(x["distance_to_nearest_experimental_pose_axis_deg"] for x in values)
    return {
        "original_binary_mask_count":len(values),
        "experimental_2026_pose_count":len(axes),
        "experimental_2026_pose_axes_deg":axes,
        "original_source_axis_range_deg":[
            min(x["source_image_space_angle_deg"] for x in values),
            max(x["source_image_space_angle_deg"] for x in values)],
        "experimental_glb_axis_range_deg":[min(axes.values()),max(axes.values())],
        "original_masks_with_axis_gap_gt_10_deg":sum(g>10 for g in gaps),
        "mean_nearest_projected_angle_gap_deg":round(sum(gaps)/len(gaps),6),
        "max_nearest_projected_angle_gap_deg":max(gaps),
        "pose_identity_inferred_from_smallest_angle":False,
        "per_original_binary_mask_unpaired_axis_gap":values,
    }

def compare(corpus:Path, source_report:Path, model_root:Path, camera_file:Path)->dict:
    import trimesh
    original,verified=validate_corpus(corpus)
    source_bytes=source_report.read_bytes()
    source=json.loads(source_bytes)
    if (source.get("schema")!=SOURCE_SCHEMA or
            source.get("source_corpus_sha256")!=digest(corpus.read_bytes()) or
            source.get("source_rom_sha256")!=CANONICAL_ROM_SHA or
            source.get("owner_character_likeness_approved") is not False or
            source.get("original_mesh_lean_angle_recovered") is not False or
            source["source_variants"]["independent_exact_source_binary_masks"]!=
                len(verified["all_masks"])):
        raise ValueError("not the authenticated original source chroma-axis packet")
    camera_bytes=camera_file.read_bytes()
    if digest(camera_bytes)!=CAMERA_SHA:
        raise ValueError("not the original frozen provisional side camera bytes")
    camera=json.loads(camera_bytes)
    camera_config(camera)
    if camera.get("camera_calibration_status")!="provisional":
        raise ValueError("unverified 1994 original camera claim")
    poses={}
    root=model_root.resolve()
    for name,expected in POSE_GLB_SHA.items():
        path=(root/"assets"/COMMIT/f"{name}-{expected[:16]}.glb").resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("missing exact old five-pose 2026 GLB asset")
        raw=path.read_bytes()
        if digest(raw)!=expected:
            raise ValueError("actual GLB pose is not the source-hash-verified asset")
        scene=trimesh.load(file_obj=io.BytesIO(raw),file_type="glb",
                           force="scene",process=False)
        poses[name]=paint_axis_from_model(scene,camera)
    comparison=summarize_unpaired_source_coverage(
        source["source_variants"]["source_masks"],poses)
    return {
        "schema":SCHEMA,
        "original_rom_sha256":CANONICAL_ROM_SHA,
        "original_source_chroma_report_sha256":digest(source_bytes),
        "source_corpus_sha256":digest(corpus.read_bytes()),
        "frozen_provisional_camera_sha256":CAMERA_SHA,
        "experimental_2026_source_model_commit":COMMIT,
        "five_experimental_2026_glb_sha256":POSE_GLB_SHA,
        "original_model_camera_or_3d_joint_recovered":False,
        "authenticated_original_sprite_to_2026_glb_pose_mapping":False,
        "experimental_painted_material_is_original_1994_albedo":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
        "unpaired_2d_axis_coverage":comparison,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus",required=True,type=Path)
    parser.add_argument("--source-axes",required=True,type=Path)
    parser.add_argument("--model-review-dir",required=True,type=Path)
    parser.add_argument("--camera",required=True,type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    result=json.dumps(compare(args.corpus,args.source_axes,args.model_review_dir,
                              args.camera),indent=2,sort_keys=True)+"\n"
    if args.out:
        publish_text_once(args.out,result)
    else:
        print(result,end="")

if __name__=="__main__":
    main()
