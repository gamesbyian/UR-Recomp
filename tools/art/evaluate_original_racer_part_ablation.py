#!/usr/bin/env python3
"""Source-authenticated five-part 2026 GLB leave-one-out versus original 2D masks.

Each reported source-part contribution measures ONLY pixels uniquely exposed
after removing one whole source-owned 2026 3D part under a frozen 7:6
provisional camera. It cannot identify any original 1994 sprite part or
prove source pose pairing. No model/source/ROM files are changed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

try:
    from tools.art.evaluate_original_racer_wheel_holdout import (
        ROM_SHA, originals_from_corpus, split_family_components,
        translated_4x_source_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.render_racer_glb_projection import render_mask, camera_config
    from tools.art.study_original_racer_root_lean_grid import CAMERA_SHA
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from evaluate_original_racer_wheel_holdout import (
        ROM_SHA, originals_from_corpus, split_family_components,
        translated_4x_source_mask,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from render_racer_glb_projection import render_mask, camera_config
    from study_original_racer_root_lean_grid import CAMERA_SHA
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-REAL-GLB-SOURCE-PART-LEAVE-ONE-OUT-ALPHA/1"
PARTS=("tire","rim_and_hub","pedals","saddle","fork_and_frame")
ACTUAL_GLB_SHA={
    "unchanged":"ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04",
    "wheel1p1_fork1p4":"5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53",
}
PRIOR_FROZEN_BASELINE_IoU={"unchanged":.46002071,
                           "wheel1p1_fork1p4":.49816283}


def hash_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def source_owned_part(node:str)->str:
    matches=[part for part in PARTS if node.startswith(part+"__material_")]
    if len(matches)!=1:
        raise ValueError("unexpected source-owned 3D material part "+str(node))
    return matches[0]


def parts_from_sha_locked_GLb(path:Path,kind:str):
    import numpy as np
    import trimesh
    raw=path.read_bytes()
    if kind not in ACTUAL_GLB_SHA or hash_bytes(raw)!=ACTUAL_GLB_SHA[kind] or raw[:4]!=b"glTF":
        raise ValueError("not one of the two original source-authored upright GLBs")
    scene=trimesh.load(file_obj=io.BytesIO(raw),file_type="glb",
                       force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or len(scene.graph.nodes_geometry)!=16:
        raise ValueError("incorrect source 5-part/16-material hierarchy")
    if not set(PARTS).issubset(scene.graph.nodes):
        raise ValueError("source pivots missing")
    result={p:[] for p in PARTS}
    for node in sorted(scene.graph.nodes_geometry):
        owner=source_owned_part(node)
        world,geometry=scene.graph.get(node)
        mesh=scene.geometry[geometry].copy()
        mesh.apply_transform(world)
        if kind=="wheel1p1_fork1p4" and owner in ("tire","rim_and_hub"):
            vertices=np.asarray(mesh.vertices,dtype=float).copy()
            vertices[:,0]*=1.1
            mesh.vertices=vertices
        if not np.isfinite(mesh.vertices).all() or len(mesh.faces)<1:
            raise ValueError("invalid real source mesh part")
        result[owner].append(mesh)
    if any(not result[p] for p in PARTS):
        raise ValueError("missing one or more source parts")
    return result


def part_projections(parts:dict,camera:dict):
    import trimesh
    if set(parts)!=set(PARTS) or any(not parts[p] for p in PARTS):
        raise ValueError("incomplete source-owned model")
    def project(without=None):
        meshes=[m for p in PARTS if p!=without for m in parts[p]]
        combined=trimesh.util.concatenate(meshes)
        return render_mask(combined.vertices,combined.faces,camera)
    return {"full":project(),**{p:project(p) for p in PARTS}}


def lost_pixel_stats(source,full,without)->dict:
    """Exact source shape counters for only nonoccluded source-owned pixels."""
    import numpy as np
    a=np.asarray(source,dtype=bool)
    b=np.asarray(full,dtype=bool)
    c=np.asarray(without,dtype=bool)
    if a.shape!=(64,64) or b.shape!=(64,64) or c.shape!=(64,64):
        raise ValueError("full/partless/original source masks must be 64x64")
    if not (a.any() and b.any() and c.any()) or np.any(c & ~b):
        raise ValueError("missing/invalid geometric subset of full silhouette")
    exclusive=b & ~c
    def iou(candidate):
        union=int(np.count_nonzero(a|candidate))
        if not union:raise ValueError("empty original union")
        return float(np.count_nonzero(a&candidate))/union
    return {
        "source_owned_unique_model_pixels_removed":int(np.count_nonzero(exclusive)),
        "original_true_positive_pixels_lost":int(np.count_nonzero(exclusive&a)),
        "original_false_positive_pixels_removed":int(np.count_nonzero(exclusive&~a)),
        "original_source_false_negative_pixels_remaining":int(np.count_nonzero(a&~b)),
        "whole_model_source_mask_iou":round(iou(b),8),
        "without_part_source_mask_iou":round(iou(c),8),
    }


def summarize_family(per_source:dict,hashes:list[str])->dict:
    if not hashes or set(hashes)-set(per_source) or len(hashes)!=len(set(hashes)):
        raise ValueError("original SHA binary family is empty, leaky or duplicated")
    output={}
    for part in PARTS:
        items=[per_source[h]["parts"][part] for h in sorted(hashes)]
        output[part]={
            "source_independent_binary_masks":len(items),
            "original_true_positive_pixels_lost_across_masks":
                sum(x["original_true_positive_pixels_lost"] for x in items),
            "original_false_positive_pixels_removed_across_masks":
                sum(x["original_false_positive_pixels_removed"] for x in items),
            "mean_iou_without_part_minus_full":round(sum(
                x["without_part_source_mask_iou"]-x["whole_model_source_mask_iou"]
                for x in items)/len(items),8),
            "masks_better_without_part":sum(
                x["without_part_source_mask_iou"]>
                x["whole_model_source_mask_iou"] for x in items),
            "masks_worse_without_part":sum(
                x["without_part_source_mask_iou"]<
                x["whole_model_source_mask_iou"] for x in items),
        }
    return output


def evaluate(corpus:Path,unchanged:Path,combined:Path,camera_file:Path)->dict:
    import numpy as np
    original,verified=validate_corpus(corpus)
    if original["source_rom_sha256"]!=ROM_SHA:
        raise ValueError("unauthenticated original USA ROM")
    sources=originals_from_corpus(corpus,original)
    partition=split_family_components(verified["per_window_masks"])
    if len(sources)!=35 or set(sources)!=verified["all_masks"]:
        raise ValueError("original source ROM shape census mismatch")
    if len(partition["withheld_binary_shas"])!=19 or len(partition["fit_binary_shas"])!=16:
        raise ValueError("original binary holdout components changed")
    raw=camera_file.read_bytes()
    if hash_bytes(raw)!=CAMERA_SHA:raise ValueError("provisional camera changed")
    camera=json.loads(raw)
    camera_config(camera)
    datasets={}
    for kind,path in (("unchanged",unchanged),("wheel1p1_fork1p4",combined)):
        projections=part_projections(parts_from_sha_locked_GLb(path,kind),camera)
        per={}
        for h,src in sorted(sources.items()):
            original_pixels=np.frombuffer(src["mask"],dtype=np.uint8).reshape(64,64)
            anchor=src["source_alpha_anchor_x2_y2"]
            full=np.frombuffer(translated_4x_source_mask(projections["full"],anchor),
                               dtype=np.uint8).reshape(64,64)
            per[h]={
                "original_source_players":sorted(src["players"]),
                "original_representation_ids":sorted(src["source_representations"]),
                "parts":{p:lost_pixel_stats(
                    original_pixels,full,
                    np.frombuffer(translated_4x_source_mask(projections[p],anchor),
                                  dtype=np.uint8).reshape(64,64))
                         for p in PARTS},
            }
        mean=round(sum(row["parts"]["tire"]["whole_model_source_mask_iou"]
                       for row in per.values())/len(per),8)
        if abs(mean-PRIOR_FROZEN_BASELINE_IoU[kind])>1e-8:
            raise ValueError("original full-model 35-mask IoU identity not reproduced")
        datasets[kind]={
            "mean_full_model_original_source_IoU":mean,
            "original_per_binary_shape":per,
            "families":{
                "first_connected_16_binary_masks":
                    summarize_family(per,partition["fit_binary_shas"]),
                "19_SHA_disconnected_additional_2D_source_masks":
                    summarize_family(per,partition["withheld_binary_shas"]),
                "all_35_original_binary_masks":summarize_family(per,list(per)),
            },
        }
    return {
        "schema":SCHEMA,
        "original_ROM_sha256":ROM_SHA,
        "original_source_corpus_sha256":hash_bytes(corpus.read_bytes()),
        "actual_2026_source_GLB_sha256":ACTUAL_GLB_SHA,
        "provisional_source_camera_sha256":hash_bytes(raw),
        "five_2026_source_owned_parts":list(PARTS),
        "one_original_binary_mask_one_vote":True,
        "original_1994_art_parts_or_mesh_recovered":False,
        "original_1994_source_3D_camera_or_pose_pairs_known":False,
        "original_1994_collision_contact_recovered":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
        "visible_2D_part_contribution_is_not_original_1994_sprite_part_segmentation":True,
        "result":datasets,
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus",required=True,type=Path)
    ap.add_argument("--unchanged-glb",required=True,type=Path)
    ap.add_argument("--combined-glb",required=True,type=Path)
    ap.add_argument("--camera",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    payload=json.dumps(evaluate(args.corpus,args.unchanged_glb,
                                args.combined_glb,args.camera),
                       indent=2,sort_keys=True)+"\n"
    publish_text_once(args.out,payload)


if __name__=="__main__":
    main()
