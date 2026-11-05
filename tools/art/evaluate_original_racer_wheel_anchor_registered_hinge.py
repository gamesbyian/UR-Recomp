#!/usr/bin/env python3
"""Measured original-ROM 2D wheel centres against the ONE real 2026 GLB.

Source ring candidates never use a 3D candidate overlap to select translation.
This is an unpaired, provisional-camera experiment, not original 3D recovery.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path

try:
    from tools.art.audit_art4k_original_wheel_ring import ring_candidates
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.evaluate_original_racer_wheel_holdout import originals_from_corpus
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.render_racer_glb_projection import camera_config, render_mask
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_art4k_original_wheel_ring import ring_candidates
    from freeze_racer_source_family_splits import validate_corpus
    from evaluate_original_racer_wheel_holdout import originals_from_corpus
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from render_racer_glb_projection import camera_config, render_mask
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ROM-2D-WHEEL-ANCHORED-FRAME-HINGE/1"
MODEL_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
CORPUS_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
CHROMA_SHA="78f420423c62e61bcb5c4271c61dc8dab17b786f693c2895cd0e3054d1d06bc8"
SPLIT_SHA="aa86e13348875a768351d926a2daa913c3428732e92c2f38f135bbeadf53398c"
PARTS=("tire","rim_and_hub","pedals","fork_and_frame","saddle")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def translate_4x(mask4,dx:int,dy:int)->bytes:
    import numpy as np
    if (getattr(mask4,"shape",None)!=(256,256) or
            type(dx) is not int or type(dy) is not int or not np.any(mask4)):
        raise ValueError("nonempty 256x256 source GLB mask and integer offset required")
    yy,xx=np.nonzero(mask4)
    if (xx.min()+dx<0 or xx.max()+dx>255 or
            yy.min()+dy<0 or yy.max()+dy>255):
        raise ValueError("source registration cannot crop visible model pixels")
    moved=np.zeros_like(mask4)
    moved[yy+dy,xx+dx]=1
    return bytes(int(v) for v in moved[2::4,2::4].reshape(-1))


def centre_shift_4x(cx:int,cy:int,axle_xy)->tuple[int,int]:
    if (type(cx) is not int or type(cy) is not int or
            not 0<=cx<64 or not 0<=cy<64 or len(axle_xy)!=2):
        raise ValueError("invalid source candidate or model axle")
    offsets=(4*cx+2-axle_xy[0],4*cy+2-axle_xy[1])
    if any(not math.isfinite(v) or abs(v-round(v))>1e-7 for v in offsets):
        raise ValueError("nonintegral 4x camera/axle offset cannot be guessed")
    return tuple(int(round(v)) for v in offsets)


def iou(a:bytes,b:bytes)->float:
    if (len(a)!=4096 or len(b)!=4096 or
            any(x not in (0,1) for x in a) or any(x not in (0,1) for x in b)):
        raise ValueError("two 64x64 binary masks required")
    common=sum(x and y for x,y in zip(a,b))
    union=sum(x or y for x,y in zip(a,b))
    if not union:
        raise ValueError("empty source/model union")
    return round(common/union,8)


def source_rings(corpus_path:Path,receipt,groups)->dict:
    """Verify every authentic source PNG, retaining ties and palette agreements."""
    result=defaultdict(list)
    for entry in receipt["source_representations"].values():
        path=corpus_path.parent/entry["local_file"]
        w,h,rgba,sha=decode_rgba_png(path)
        metrics=alpha_metrics(rgba,w,h)
        if ((w,h)!=(64,64) or sha!=entry["local_png_sha256"] or
                metrics["source_rgba_sha256"]!=entry["source_rgba_sha256"] or
                metrics["binary_mask_sha256"]!=entry["source_binary_mask_sha256"]):
            raise ValueError("source PNG differs from verified original USA ROM")
        result[entry["source_binary_mask_sha256"]].append(ring_candidates(rgba))
    if set(result)!=set(groups) or len(result)!=35:
        raise ValueError("source ring masks do not match original census")
    final={}
    for shape,variants in result.items():
        if any(x!=variants[0] for x in variants[1:]):
            raise ValueError("same source binary shape has divergent palette ring")
        choices=variants[0]["best_candidate_centres_xy_radius_logical_px"]
        if not choices or any(len(x)!=3 or x[2]!=7 for x in choices):
            raise ValueError("unexpected original source ring radius")
        final[shape]=choices
    return final


def source_projection(glb:bytes,camera:dict):
    import numpy as np
    import trimesh
    if digest(glb)!=MODEL_SHA or glb[:4]!=b"glTF":
        raise ValueError("not the exact historic 2026 experimental upright GLB")
    scene=trimesh.load(io.BytesIO(glb),file_type="glb",force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or not set(PARTS).issubset(scene.graph.nodes):
        raise ValueError("lost original five-part GLB")
    if len(scene.graph.nodes_geometry)!=16:
        raise ValueError("lost sixteen source GLB material meshes")
    axle=scene.graph.get("tire")[0]
    if (any(not np.allclose(scene.graph.get(p)[0],axle,atol=1e-8,rtol=0)
            for p in ("rim_and_hub","pedals")) or
            any(scene.graph.transforms.parents.get(p)!=scene.graph.base_frame for p in PARTS)):
        raise ValueError("GLB axle/parents differ from canonical rig")
    right,up,origin,scale,anchor=camera_config(camera)
    xyz=axle[:3,3]-origin
    axle4=(float(xyz@right*scale*4*6/7+2*anchor[0]+2),
           float(-xyz@up*scale*4+2*anchor[1]+2))
    def draw(s):
        mesh=(s.to_geometry() if callable(getattr(s,"to_geometry",None))
              else s.dump(concatenate=True))
        return render_mask(mesh.vertices,mesh.faces,camera)
    base=draw(scene)
    candidate=scene.copy()
    a=math.radians(-40)
    rot=np.eye(4)
    rot[0,0]=rot[2,2]=math.cos(a)
    rot[0,2]=math.sin(a)
    rot[2,0]=-math.sin(a)
    motion=axle@rot@np.linalg.inv(axle)
    for p in ("fork_and_frame","saddle"):
        candidate.graph.update(frame_to=p,frame_from=candidate.graph.base_frame,
                               matrix=motion@scene.graph.get(p)[0])
    for p in ("tire","rim_and_hub","pedals"):
        if not np.array_equal(candidate.graph.get(p)[0],scene.graph.get(p)[0]):
            raise ValueError("hinge rotated stationary wheel/pedal parent")
    return {"upright":base,"hinge_minus40":draw(candidate)},axle4


def evaluate(corpus_path:Path,glb_path:Path,camera_path:Path,
             chroma_path:Path|None=None,split_path:Path|None=None):
    corpus,proof=validate_corpus(corpus_path)
    if proof["corpus_sha256"]!=CORPUS_SHA:
        raise ValueError("source ROM corpus SHA differs from immutable original")
    groups=originals_from_corpus(corpus_path,corpus)
    if len(groups)!=35 or set(groups)!=proof["all_masks"]:
        raise ValueError("not original 35 binary source masks")
    centres=source_rings(corpus_path,corpus,groups)
    raw_camera=camera_path.read_bytes()
    if digest(raw_camera)!=CAMERA_SHA:
        raise ValueError("not frozen provisional 7:6 side camera")
    camera=json.loads(raw_camera)
    if camera.get("source_anchor_x2_y2")!=[67,76]:
        raise ValueError("unexpected original source anchor")
    render,axle4=source_projection(glb_path.read_bytes(),camera)
    axis={}
    if chroma_path:
        raw=chroma_path.read_bytes()
        if digest(raw)!=CHROMA_SHA:
            raise ValueError("not exact original 2D chroma report")
        data=json.loads(raw)
        axis={r["original_binary_mask_sha256"]:
              r["equal_colour_variant_mean_projected_angle_deg"]
              for r in data["source_variants"]["source_masks"]}
        if set(axis)!=set(groups):
            raise ValueError("chroma source binary-mask identity differs")
    family={}
    if split_path:
        raw=split_path.read_bytes()
        if digest(raw)!=SPLIT_SHA:
            raise ValueError("not original SHA-disjoint family witness")
        split=json.loads(raw)["leakage_free_window_split"]
        family={h:"first16" for h in split["fit_binary_shas"]}
        family.update({h:"additional19" for h in split["withheld_binary_shas"]})
        if set(family)!=set(groups):
            raise ValueError("source mask identity leaked from family split")
    rows=[]
    for sha,entry in sorted(groups.items()):
        original=entry["mask"]
        mx,my=entry["source_alpha_anchor_x2_y2"]
        poses={}
        for name,mask4 in render.items():
            old=iou(original,translate_4x(mask4,2*(mx-67),2*(my-76)))
            vals=[]
            for cx,cy,_ in centres[sha]:
                dx,dy=centre_shift_4x(cx,cy,axle4)
                vals.append(iou(original,translate_4x(mask4,dx,dy)))
            poses[name]={
                "old_lowest_alpha_anchor_iou":old,
                "source_wheel_anchor_iou_min":min(vals),
                "source_wheel_anchor_iou_max":max(vals),
                "possible_source_wheel_centres":len(vals)}
        row={"source_binary_mask_sha256":sha,"original_source_2d_ring_centres":centres[sha],
             "source_alpha_anchor_x2_y2":[mx,my],
             "source_painted_axis_deg":axis.get(sha),
             "source_family":family.get(sha),
             "unpaired_3d_pose_scores":poses}
        if axis:
            row["exploratory_colour_selected_pose"]="hinge_minus40" if axis[sha]>20 else "upright"
        rows.append(row)
    def means(rs):
        result={}
        for name in render:
            result[name]={k:round(sum(r["unpaired_3d_pose_scores"][name][k]
                                      for r in rs)/len(rs),8)
                          for k in ("old_lowest_alpha_anchor_iou","source_wheel_anchor_iou_min",
                                    "source_wheel_anchor_iou_max")}
        if axis:
            chosen=[r["unpaired_3d_pose_scores"][r["exploratory_colour_selected_pose"]] for r in rs]
            result["posthoc_source_colour_pose_selection"]={
                k:round(sum(v[k] for v in chosen)/len(chosen),8)
                for k in ("old_lowest_alpha_anchor_iou","source_wheel_anchor_iou_min",
                          "source_wheel_anchor_iou_max")}
            result["posthoc_hinge_selected_masks"]=sum(
                r["exploratory_colour_selected_pose"]=="hinge_minus40" for r in rs)
        return result
    regions={"all35":rows}
    if family:
        regions["first16"]=[r for r in rows if r["source_family"]=="first16"]
        regions["additional19"]=[r for r in rows if r["source_family"]=="additional19"]
    summary={name:{"original_binary_shapes":len(rs),"mean_iou":means(rs)}
             for name,rs in regions.items() if rs}
    return {"schema":SCHEMA,"source_rom_manifest_sha256":CORPUS_SHA,
            "historical_glb_sha256":MODEL_SHA,"frozen_camera_sha256":CAMERA_SHA,
            "original_emulator_live_chronology_verified":False,
            "3d_camera_or_source_axle_recovered":False,
            "ring_placement_selected_by_model_overlap":False,
            "all_tied_source_centres_retained_as_iou_bounds":True,
            "pose_rule_and_ring_detector_developed_posthoc":True,
            "owner_likeness_approved":False,"shipping_art_approved":False,
            "summary":summary,"per_source_mask":rows}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus",type=Path,required=True)
    p.add_argument("--glb",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--chroma",type=Path)
    p.add_argument("--split",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.corpus,a.glb,a.camera,a.chroma,a.split)
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result["summary"],indent=2,sort_keys=True))


if __name__=="__main__":
    main()
