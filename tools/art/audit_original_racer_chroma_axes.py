#!/usr/bin/env python3
"""Original-ROM 2D painted-axis constraints for one experimental racer rig.

Measures source P1 red / P2 blue chroma in every authenticated 64x64 PNG.
A projected coloured-pixel centroid axis is *not* an original 3D joint,
camera, wheel axis, direction of travel or source→GLB pose registration.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.audit_original_racer_colourway import classify_source_chroma
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.racer_source_pixels import decode_rgba_png
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_colourway import classify_source_chroma
    from freeze_racer_source_family_splits import validate_corpus
    from racer_source_pixels import decode_rgba_png
    from no_replace_report import publish_text_once

SCHEMA="UR-RACER-ORIGINAL-PROJECTED-CHROMA-AXES/1"
PIXEL_ASPECT=7/6
TOP_BOTTOM_ROWS=3
CANONICAL_ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def painted_axis(rgba:bytes,player:str)->dict:
    """Threshold is the already-merged original source colour-census rule.

    Fit a line between the centroids of the top and bottom three occupied
    raster rows. No semantic assumption about frame pivots, camera or light.
    """
    if (type(rgba) is not bytes or len(rgba)!=64*64*4 or player not in ("p1","p2")):
        raise ValueError("requires exact 64x64 original RGBA and known player")
    wanted="red" if player=="p1" else "blue"
    points=[]
    for k in range(0,len(rgba),4):
        r,g,b,a=rgba[k:k+4]
        if a not in (0,255):
            raise ValueError("original source has non-binary alpha")
        if a and classify_source_chroma((r,g,b))==wanted:
            n=k//4
            points.append((n%64,n//64))
    if len(points)<12:
        raise ValueError("source frame has too few verified player-colour pixels")
    rows=sorted(set(y for x,y in points))
    if len(rows)<8 or rows[-1]-rows[0]<8:
        raise ValueError("source coloured region has insufficient vertical extent")

    def centre(keys:set[int]):
        pts=[(x,y) for x,y in points if y in keys]
        return sum(x for x,y in pts)/len(pts),sum(y for x,y in pts)/len(pts)

    top=centre(set(rows[:TOP_BOTTOM_ROWS]))
    bottom=centre(set(rows[-TOP_BOTTOM_ROWS:]))
    dx=(bottom[0]-top[0])*PIXEL_ASPECT
    dy=bottom[1]-top[1]
    if dy<=0:
        raise ValueError("source chroma centroid ordering invalid")
    return {
        "player_colour_indicator":wanted,
        "pixel_count":len(points),
        "chroma_bbox_xyxy":[min(x for x,y in points),rows[0],
                            max(x for x,y in points),rows[-1]],
        "top_3_nonempty_rows":rows[:TOP_BOTTOM_ROWS],
        "bottom_3_nonempty_rows":rows[-TOP_BOTTOM_ROWS:],
        "top_centroid_logical_xy":[round(v,6) for v in top],
        "bottom_centroid_logical_xy":[round(v,6) for v in bottom],
        "signed_bottom_minus_top_dx_physical_pixels":round(dx,6),
        "signed_axis_angle_from_image_vertical_deg":round(math.degrees(math.atan2(dx,dy)),6),
        "source_geometry_or_joints_recovered":False,
    }

def reduce_source_variants(items:list[dict])->dict:
    """Each SHA-distinct binary mask counts once, not once per held frame.

    Original paint variants or opposite-player colours of the SAME source
    binary silhouette are separately recorded, then averaged per mask.
    """
    if not items:
        raise ValueError("no source original colour observations")
    by_mask=defaultdict(dict)
    for item in items:
        player,mask,rgba_sha=(item.get("player"),item.get("binary_mask_sha256"),
                             item.get("source_rgba_sha256"))
        if (player not in ("p1","p2") or not isinstance(mask,str) or
            len(mask)!=64 or not isinstance(rgba_sha,str) or len(rgba_sha)!=64 or
            not isinstance(item.get("representation_id"),str) or
            not item["representation_id"]):
            raise ValueError("invalid original source representation")
        key=(player,rgba_sha)
        existing=by_mask[mask].get(key)
        if existing is not None:
            if existing["measurement"]!=item["measurement"]:
                raise ValueError("same original RGB representation measured differently")
            existing["representation_ids"].append(item["representation_id"])
        else:
            by_mask[mask][key]={
                "player":player,"rgba_sha256":rgba_sha,
                "representation_ids":[item["representation_id"]],
                "measurement":item["measurement"],
            }
    outputs=[]
    for mask in sorted(by_mask):
        variants=sorted(by_mask[mask].values(),key=lambda v:(v["player"],v["rgba_sha256"]))
        angles=[v["measurement"]["signed_axis_angle_from_image_vertical_deg"]
                for v in variants]
        outputs.append({
            "original_binary_mask_sha256":mask,
            "source_colour_variants":variants,
            "different_player_or_palette_variants":len(variants),
            "equal_colour_variant_mean_projected_angle_deg":
                round(sum(angles)/len(angles),6),
            "min_variant_projected_angle_deg":min(angles),
            "max_variant_projected_angle_deg":max(angles),
        })
    return {
        "independent_exact_source_binary_masks":len(outputs),
        "source_2d_chroma_axis_range_deg":[
            min(x["min_variant_projected_angle_deg"] for x in outputs),
            max(x["max_variant_projected_angle_deg"] for x in outputs)],
        "one_vote_per_exact_binary_mask":True,
        "source_masks":outputs,
    }

def audit(corpus_file:Path)->dict:
    receipt,verified=validate_corpus(corpus_file)
    if (receipt["source_rom_sha256"]!=CANONICAL_ROM_SHA or
            len(verified["all_masks"])!=receipt["unique_binary_silhouettes"]):
        raise ValueError("original ROM and source-mask census mismatched")
    root=corpus_file.resolve().parent
    items=[]
    for rid,rep in sorted(receipt["source_representations"].items()):
        file=(root/rep["local_file"]).resolve()
        if not file.is_relative_to(root):
            raise ValueError("source path escaped authenticated corpus")
        w,h,rgba,sha=decode_rgba_png(file)
        if ((w,h)!=(64,64) or sha!=rep["local_png_sha256"] or
                digest(rgba)!=rep["source_rgba_sha256"] or
                digest(bytes(1 if a else 0 for a in rgba[3::4]))!=
                    rep["source_binary_mask_sha256"]):
            raise ValueError("original source raster modified after validation")
        items.append({
            "player":rep["player"],
            "representation_id":rid,
            "binary_mask_sha256":rep["source_binary_mask_sha256"],
            "source_rgba_sha256":rep["source_rgba_sha256"],
            "measurement":painted_axis(rgba,rep["player"]),
        })
    aggregate=reduce_source_variants(items)
    if (aggregate["independent_exact_source_binary_masks"]!=len(verified["all_masks"])
            or len(items)!=receipt["unique_representations"]):
        raise ValueError("source raster and source variant census changed")
    return {
        "schema":SCHEMA,
        "source_rom_sha256":CANONICAL_ROM_SHA,
        "source_corpus_sha256":digest(corpus_file.read_bytes()),
        "source_registry_sha256":receipt["source_registry_sha256"],
        "source_representation_count":len(items),
        "source_temporal_frame_observations":
            len(receipt["source_temporal_frame_observations"]),
        "original_source_2d_pixel_aspect":"7:6",
        "original_chroma_rule":"classify_source_chroma from existing original colour census",
        "axis_definition":"bottom 3 minus top 3 occupied player-colour pixel-row centroids; angle is from image vertical, positive toward right",
        "source_variants":aggregate,
        "original_3d_camera_identified":False,
        "original_mesh_lean_angle_recovered":False,
        "original_sprite_to_experimental_rig_pose_mapped":False,
        "source_coloured_pixels_are_proven_one_3d_part":False,
        "independent_source_3d_views_verified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
    }

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus",required=True,type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    result=json.dumps(audit(args.corpus),indent=2,sort_keys=True)+"\n"
    if args.out:
        publish_text_once(args.out,result)
    else:
        print(result,end="")

if __name__=="__main__":
    main()
