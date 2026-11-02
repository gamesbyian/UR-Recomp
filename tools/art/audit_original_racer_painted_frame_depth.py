#!/usr/bin/env python3
"""Depth-aware source-painted blue fork diagnostic on ONE historical 2026 GLB.

Strictly an offline side-camera robustness check. Neither candidate view (+Y
or -Y) is a measured 1994 camera; PPU timing and original 3D rig stay unknown.
The 2026 model/ROM-chroma/camera SHA evidence is immutable and versioned.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, BLUE_RGBA, CHROMA_NODE, CAMERA_SHA, CHROMA_SHA,
        MODEL_SHA, painted_axis_from_mask, source_selected_angle, spin_frame,
    )
    from tools.art.render_racer_glb_projection import camera_config
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from evaluate_original_racer_chroma_guided_3d_hinge import (
        ANGLES, BLUE_RGBA, CHROMA_NODE, CAMERA_SHA, CHROMA_SHA,
        MODEL_SHA, painted_axis_from_mask, source_selected_angle, spin_frame,
    )
    from render_racer_glb_projection import camera_config
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-HISTORICAL-GLB-PAINT-DEPTH-ROBUSTNESS/1"
SIDES = (1, -1)
DEPTH_TIE_EPS = 1e-6


def rasterize_depth(triangles, material_ids, camera, direction=1, eps=DEPTH_TIE_EPS):
    """64px pixel-centre orthographic z-buffer; tied distinct material is unknown.

    Triangles are already in their actual GLB world transforms. +Y and -Y
    mean hypothetical camera origins looking toward the model from ±world Y.
    Blue/other attribution must use each triangle's material identity.
    """
    import numpy as np
    camera_config(camera)
    t = np.asarray(triangles, dtype=np.float64)
    ids = np.asarray(material_ids)
    if (t.ndim != 3 or t.shape[1:] != (3, 3) or len(t)==0
            or ids.shape != (len(t),) or ids.dtype.kind not in "iu"
            or not np.isfinite(t).all()
            or type(direction) is not int or direction not in SIDES
            or type(eps) not in (int, float) or not 0 < eps <= 1e-3):
        raise ValueError("invalid finite triangle/material or depth camera arguments")
    right, up, origin, scale, anchor = camera_config(camera)
    # Match render_racer_glb_projection.py 4x sample (4*x+2,4*y+2).
    q = t - origin
    xy = np.empty((len(t), 3, 2), dtype=np.float64)
    xy[:, :, 0] = q @ right * (scale*6/7) + anchor[0]/2
    xy[:, :, 1] = -(q @ up) * scale + anchor[1]/2
    # This existing frozen side camera has right +X and up +Z.
    if not (np.allclose(right, [1, 0, 0]) and np.allclose(up, [0, 0, 1])):
        raise ValueError("only the historical provisional ±Y side view is admissible")
    if (xy.min() < 0 or xy.max() > 63):
        raise ValueError("source-fixed depth image would crop actual 2026 mesh")
    depth = t[:, :, 1] * direction
    if np.any(ids < 0):
        raise ValueError("negative material identity is forbidden")
    materials = np.unique(ids)
    material_layer_index = {int(value):index for index,value in enumerate(materials)}
    # Max-depth per material is associative and independent of face iteration
    # order. Resolve *cross-material* near-depth ambiguity only after every
    # triangle, avoiding a false clear when zA < zB < zC but B~C within eps.
    layers = np.full((len(materials),64,64), -np.inf)
    hits = np.zeros((64,64), dtype=np.int32)
    for i, corners in enumerate(xy):
        a, b, c = corners
        det = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if abs(det) < 1e-10:
            continue
        x0 = max(0, math.ceil(min(a[0],b[0],c[0])-1e-9))
        x1 = min(63, math.floor(max(a[0],b[0],c[0])+1e-9))
        y0 = max(0, math.ceil(min(a[1],b[1],c[1])-1e-9))
        y1 = min(63, math.floor(max(a[1],b[1],c[1])+1e-9))
        if x0 > x1 or y0 > y1:
            continue
        yy, xx = np.mgrid[y0:y1+1, x0:x1+1]
        dx, dy = xx-a[0], yy-a[1]
        u = (dx*(c[1]-a[1])-dy*(c[0]-a[0]))/det
        v = (dy*(b[0]-a[0])-dx*(b[1]-a[1]))/det
        covered = (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8)
        if not covered.any():
            continue
        z = depth[i,0]*(1-u-v)+depth[i,1]*u+depth[i,2]*v
        layer = layers[material_layer_index[int(ids[i])],y0:y1+1,x0:x1+1]
        hits[y0:y1+1,x0:x1+1][covered] += 1
        np.maximum(layer,z,out=layer,where=covered)
    best = layers.max(axis=0)
    occupied = np.isfinite(best)
    closest_index = np.argmax(layers,axis=0)
    owner = materials[closest_index].astype(np.int32)
    owner[~occupied] = -1
    within = occupied[None,:,:] & (layers >= best[None,:,:]-eps)
    tied = within.sum(axis=0) > 1
    return owner, tied, hits


def material_triangles(scene):
    """Exposes exact original nodes and stable per-triangle material identities."""
    import numpy as np
    names = sorted(scene.graph.nodes_geometry)
    if len(names) != 16 or CHROMA_NODE not in names:
        raise ValueError("not historical 16-material blue fork GLB")
    triangles, ids = [], []
    for material_id, name in enumerate(names):
        world, geometry = scene.graph.get(name)
        mesh = scene.geometry[geometry].copy()
        if name == CHROMA_NODE:
            rgba = np.asarray(mesh.visual.vertex_colors)
            if rgba.shape != (len(mesh.vertices), 4) or not np.all(
                    rgba == np.asarray(BLUE_RGBA)):
                raise ValueError("source-blue fork RGBA/material identity changed")
        mesh.apply_transform(world)
        triangles.append(np.asarray(mesh.vertices[mesh.faces], dtype=np.float64))
        ids.extend([material_id]*len(mesh.faces))
    return np.concatenate(triangles), np.asarray(ids, dtype=np.int32), names.index(CHROMA_NODE)


def angle_witness(scene, camera, hinge_angle):
    """Full model attribution and unoccluded blue probe at exactly same samples."""
    import numpy as np
    posed = spin_frame(scene, hinge_angle)
    triangles, ids, blue_id = material_triangles(posed)
    blue = ids == blue_id
    blue_owner, blue_tie, _ = rasterize_depth(
        triangles[blue], np.zeros(int(blue.sum()),dtype=np.int32), camera)
    unoccluded = (blue_owner == 0) & ~blue_tie
    if not unoccluded.any():
        raise ValueError("the authentic blue material projected empty")
    report = {
        "unoccluded_blue_pixels": int(unoccluded.sum()),
        "unoccluded_blue_axis_degrees": painted_axis_from_mask(unoccluded),
    }
    for direction, label in ((1,"camera_from_plus_world_y"),(-1,"camera_from_minus_world_y")):
        owners, ties, hits = rasterize_depth(triangles, ids, camera, direction)
        visible = (owners == blue_id) & ~ties
        if not visible.any():
            raise ValueError("blue source frame hidden completely under candidate side")
        report[label] = {
            "depth_visible_blue_pixels": int(visible.sum()),
            "occluded_blue_pixels": int((unoccluded & ~visible).sum()),
            "depth_tied_blue_pixels": int((unoccluded & ties).sum()),
            "all_material_depth_tie_pixels": int(ties.sum()),
            "covered_pixels_with_multiple_overlapping_triangles": int((hits>1).sum()),
            "visible_blue_axis_degrees": painted_axis_from_mask(visible),
        }
    return report



def variant_painted_angle_selections(source_row:dict,axes:dict)->dict:
    """Do not erase distinct original player-colour pose evidence by averaging.

    The *binary* silhouette retains one vote, but every source-authenticated
    RGB variant can express a different 2D painted frame axis. No IoU oracle.
    """
    variants=source_row.get("source_colour_variants")
    if not isinstance(variants,list) or not variants:
        raise ValueError("source original colour variants absent")
    observations=[]
    for variant in variants:
        if not isinstance(variant,dict) or variant.get("player") not in ("p1","p2"):
            raise ValueError("invalid source original colour variant")
        rgba=variant.get("rgba_sha256")
        if (not isinstance(rgba,str) or len(rgba)!=64 or
                any(c not in "0123456789abcdef" for c in rgba)):
            raise ValueError("source colour variant SHA invalid")
        measurement=variant.get("measurement")
        if not isinstance(measurement,dict):
            raise ValueError("source 2D variant colour measurement absent")
        value=measurement.get("signed_axis_angle_from_image_vertical_deg")
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError("source original painted axis must be finite")
        observations.append({
            "source_player":variant["player"],
            "source_rgba_sha256":rgba,
            "original_source_2d_painted_axis_deg":value,
            "selected_hinges_by_model_visibility":{
                key:source_selected_angle(value,predictions)
                for key,predictions in axes.items()},
        })
    observed_different={}
    for label in axes:
        choices=sorted({o["selected_hinges_by_model_visibility"][label]
                        for o in observations})
        observed_different[label]={
            "possible_hinge_degrees":choices,
            "distinct_hinge_count":len(choices),
            "variant_disagreement":len(choices)>1,
        }
    return {"authenticated_source_rgba_variants":observations,
            "source_variant_pose_ambiguity":observed_different}

def evaluate(glb_path: Path, camera_path: Path, source_chroma_path: Path):
    import trimesh
    glb = glb_path.read_bytes()
    if hashlib.sha256(glb).hexdigest() != MODEL_SHA or glb[:4] != b"glTF":
        raise ValueError("historical 2026 GLB hash mismatch")
    camera_bytes = camera_path.read_bytes()
    if hashlib.sha256(camera_bytes).hexdigest() != CAMERA_SHA:
        raise ValueError("frozen 2026 source camera hash mismatch")
    camera = json.loads(camera_bytes)
    camera_config(camera)
    source_bytes = source_chroma_path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != CHROMA_SHA:
        raise ValueError("authentic original USA ROM 2D chroma SHA mismatch")
    source = json.loads(source_bytes)
    originals = source["source_variants"]["source_masks"]
    if len(originals) != 35 or len({r["original_binary_mask_sha256"] for r in originals}) != 35:
        raise ValueError("35 independent original source binary silhouettes required")
    scene = trimesh.load(io.BytesIO(glb), file_type="glb", force="scene", process=False)
    witnesses = {angle:angle_witness(scene,camera,angle) for angle in ANGLES}
    cases = []
    for row in originals:
        target = row["equal_colour_variant_mean_projected_angle_deg"]
        if type(target) not in (int,float) or not math.isfinite(target):
            raise ValueError("source 2D painted centroid axis invalid")
        axes = {
            "unoccluded":{a:witnesses[a]["unoccluded_blue_axis_degrees"] for a in ANGLES},
            "camera_from_plus_world_y":{
                a:witnesses[a]["camera_from_plus_world_y"]["visible_blue_axis_degrees"] for a in ANGLES},
            "camera_from_minus_world_y":{
                a:witnesses[a]["camera_from_minus_world_y"]["visible_blue_axis_degrees"] for a in ANGLES},
        }
        selected = {name:source_selected_angle(target, candidates)
                    for name,candidates in axes.items()}
        variants=variant_painted_angle_selections(row,axes)
        cases.append({
            "source_binary_mask_sha256":row["original_binary_mask_sha256"],
            "source_painted_2d_axis_degrees":target,
            "selected_rig_hinge_degrees":selected,
            "selected_painted_axis_error_degrees":{
                k:round(abs(axes[k][v]-target),8) for k,v in selected.items()
            },
            **variants,
        })
    def changes(key):
        return sum(r["selected_rig_hinge_degrees"][key] !=
                   r["selected_rig_hinge_degrees"]["unoccluded"] for r in cases)
    return {
        "schema":SCHEMA,
        "historical_2026_upright_glb_sha256":MODEL_SHA,
        "provisional_camera_sha256":CAMERA_SHA,
        "authentic_original_rom_2d_colour_axis_sha256":CHROMA_SHA,
        "tested_hinges_degrees":list(ANGLES),
        "depth_tie_tolerance_world_units":DEPTH_TIE_EPS,
        "hypothetical_camera_directions":["+world-Y","-world-Y"],
        "source_camera_depth_order_authenticated":False,
        "source_painted_colour_is_proven_same_anatomical_part":False,
        "original_3d_joint_or_animation_timing_recovered":False,
        "experiments_selected_after_source_corpus_inspection":True,
        "summary":{
            "source_original_binary_masks":len(cases),
            "changed_pose_plus_y_vs_unoccluded":changes("camera_from_plus_world_y"),
            "changed_pose_minus_y_vs_unoccluded":changes("camera_from_minus_world_y"),
            "plus_minus_y_pose_disagreement_count":sum(
                r["selected_rig_hinge_degrees"]["camera_from_plus_world_y"] !=
                r["selected_rig_hinge_degrees"]["camera_from_minus_world_y"] for r in cases),
            "source_binary_shapes_with_multiple_rgb_variants":sum(
                len(r["authenticated_source_rgba_variants"])>1 for r in cases),
            "source_binary_shapes_with_variant_pose_disagreement_plus_y":sum(
                r["source_variant_pose_ambiguity"]["camera_from_plus_world_y"]["variant_disagreement"]
                for r in cases),
            "source_variant_angles_are_not_reduced_to_one_physical_3d_joint":True,
        },
        "per_hinge":{str(angle):witnesses[angle] for angle in ANGLES},
        "per_original_binary_mask":cases,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--source-chroma",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.glb,a.camera,a.source_chroma)
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result["summary"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
