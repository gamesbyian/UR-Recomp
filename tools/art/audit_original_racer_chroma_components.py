#!/usr/bin/env python3
"""Authenticated 2D original-racer painted-region connected-component witness.

Source-colour morphology only. NEVER replace the historical painted-axis
descriptor or call a high-chroma 2D region an original physical 3D fork.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.audit_original_racer_colourway import classify_source_chroma
    from tools.art.audit_original_racer_chroma_axes import painted_axis
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import validate_corpus
    from audit_original_racer_colourway import classify_source_chroma
    from audit_original_racer_chroma_axes import painted_axis
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-2D-PAINT-COMPONENT-ROBUSTNESS/1"
CORPUS_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def source_chroma_pixels(rgba:bytes, player:str)->set[tuple[int,int]]:
    if type(rgba) is not bytes or len(rgba)!=64*64*4 or player not in ("p1","p2"):
        raise ValueError("exact original 64px source RGBA and player required")
    wanted="red" if player=="p1" else "blue"
    found=set()
    for i in range(4096):
        r,g,b,a=rgba[4*i:4*i+4]
        if a not in (0,255):
            raise ValueError("source pixels must have binary alpha")
        if a and classify_source_chroma((r,g,b))==wanted:
            found.add((i%64,i//64))
    if len(found)<12:
        raise ValueError("original source painted region too small")
    return found


def connected_components(points:set[tuple[int,int]], *, diagonal:bool)->list[set[tuple[int,int]]]:
    """Deterministic iterative BFS. Diagonal adjacency is explicit, not assumed."""
    if (not isinstance(points,set) or not points or type(diagonal) is not bool
            or any(type(p) is not tuple or len(p)!=2
                   or any(type(v) is not int or not 0<=v<64 for v in p)
                   for p in points)):
        raise ValueError("nonempty set of finite source integer pixels required")
    adjacent=((0,1),(1,0),(0,-1),(-1,0))
    if diagonal:
        adjacent+=((1,1),(1,-1),(-1,1),(-1,-1))
    remaining=set(points)
    groups=[]
    while remaining:
        first=min(remaining)
        remaining.remove(first)
        component={first}
        stack=[first]
        while stack:
            x,y=stack.pop()
            for dx,dy in adjacent:
                next_point=(x+dx,y+dy)
                if next_point in remaining:
                    remaining.remove(next_point)
                    component.add(next_point)
                    stack.append(next_point)
        groups.append(component)
    groups.sort(key=lambda x:(-len(x),min(x)))
    if set().union(*groups)!=points or sum(len(g) for g in groups)!=len(points):
        raise ValueError("connected painted-source pixels not conserved")
    return groups


def centroid_axis(points:set[tuple[int,int]])->float:
    """Preserve historical 7:6 pixel-aspect and top/bottom 3 occupied rows."""
    if len(points)<12:
        raise ValueError("not enough authentic 2D painted-source pixels")
    rows=sorted({y for _,y in points})
    if len(rows)<8 or rows[-1]-rows[0]<8:
        raise ValueError("painted source has insufficient vertical extent")
    def centroid(ys):
        pixels=[(x,y) for x,y in points if y in set(ys)]
        return sum(x for x,y in pixels)/len(pixels),sum(y for x,y in pixels)/len(pixels)
    top=centroid(rows[:3])
    bottom=centroid(rows[-3:])
    return round(math.degrees(math.atan2(
        (bottom[0]-top[0])*7/6,bottom[1]-top[1])),6)


def painted_components(rgba:bytes,player:str)->dict:
    pixels=source_chroma_pixels(rgba,player)
    groups4=connected_components(pixels,diagonal=False)
    groups8=connected_components(pixels,diagonal=True)
    whole=centroid_axis(pixels)
    largest=centroid_axis(groups8[0])
    if abs(whole-painted_axis(rgba,player)["signed_axis_angle_from_image_vertical_deg"])>1e-6:
        raise ValueError("whole paint axis disagrees with historical original report")
    return {
        "source_player":player,
        "original_high_chroma_pixel_count":len(pixels),
        "four_neighbour_component_pixel_counts":[len(c) for c in groups4],
        "eight_neighbour_component_pixel_counts":[len(c) for c in groups8],
        "largest_eight_neighbour_component_fraction":round(len(groups8[0])/len(pixels),8),
        "original_whole_chroma_axis_degrees":whole,
        "largest_component_axis_degrees":largest,
        "largest_minus_original_axis_degrees":round(largest-whole,6),
        "source_2d_chroma_is_one_physical_3d_part":False,
    }


def evaluate(corpus_path:Path)->dict:
    corpus,verified=validate_corpus(corpus_path)
    if (verified["corpus_sha256"]!=CORPUS_SHA or
            corpus.get("source_rom_sha256")!=ROM_SHA or
            corpus.get("source_rom_verified_and_used_for_composition") is not True):
        raise ValueError("not the exact authenticated original USA ROM corpus")
    original_root=corpus_path.resolve().parent
    by_rgba={}
    by_binary=defaultdict(set)
    for name,record in sorted(corpus["source_representations"].items()):
        file=(original_root/record["local_file"]).resolve()
        if not file.is_relative_to(original_root):
            raise ValueError("original source raster path escaped authenticated corpus root")
        width,height,rgba,pngsha=decode_rgba_png(file)
        metrics=alpha_metrics(rgba,width,height)
        if ((width,height)!=(64,64) or
                pngsha!=record["local_png_sha256"] or
                metrics["source_rgba_sha256"]!=record["source_rgba_sha256"] or
                metrics["binary_mask_sha256"]!=record["source_binary_mask_sha256"]):
            raise ValueError("original source PNG/RGBA/mask identity changed")
        key=record["source_rgba_sha256"]
        if key not in by_rgba:
            measurement=painted_components(rgba,record["player"])
            by_rgba[key]={**measurement,
                "source_rgba_sha256":key,
                "source_binary_mask_sha256":record["source_binary_mask_sha256"],
                "original_representation_ids":[name]}
        else:
            previous=by_rgba[key]
            if (previous["source_player"]!=record["player"] or
                    previous["source_binary_mask_sha256"]!=record["source_binary_mask_sha256"]):
                raise ValueError("same source colour SHA has different player or alpha mask")
            previous["original_representation_ids"].append(name)
        by_binary[record["source_binary_mask_sha256"]].add(key)
    if len(by_rgba)!=41 or len(by_binary)!=35 or set(by_binary)!=verified["all_masks"]:
        raise ValueError("expected 41 original colours and 35 independent silhouettes")
    rows=sorted(by_rgba.values(),key=lambda x:x["source_rgba_sha256"])
    ratios=[x["largest_eight_neighbour_component_fraction"] for x in rows]
    disconnected=[x for x in rows if len(x["eight_neighbour_component_pixel_counts"])>1]
    mask_variants=[sorted(v) for v in by_binary.values()]
    return {
        "schema":SCHEMA,
        "original_rom_sha256":ROM_SHA,
        "source_manifest_sha256":CORPUS_SHA,
        "original_rgba_image_count":len(rows),
        "distinct_original_binary_silhouettes":len(by_binary),
        "source_representation_count":sum(len(x["original_representation_ids"]) for x in rows),
        "eight_connected_component_count_distribution":{
            str(k):sum(len(x["eight_neighbour_component_pixel_counts"])==k for x in rows)
            for k in sorted({len(x["eight_neighbour_component_pixel_counts"]) for x in rows})
        },
        "source_images_with_minor_disconnected_chroma":len(disconnected),
        "minimum_largest_component_fraction":min(ratios),
        "mean_abs_largest_component_axis_change_degrees":round(
            sum(abs(x["largest_minus_original_axis_degrees"]) for x in rows)/len(rows),6),
        "maximum_abs_largest_component_axis_change_degrees":max(
            abs(x["largest_minus_original_axis_degrees"]) for x in rows),
        "original_binary_masks_with_multiple_colour_variants":sum(len(v)>1 for v in mask_variants),
        "source_1994_3d_anatomy_or_camera_recovered":False,
        "original_emulator_chronology_recovered":False,
        "unapproved_model_geometry_modified":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
        "per_original_unique_rgba_image":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=evaluate(args.corpus)
    publish_text_once(args.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="per_original_unique_rgba_image"},
                     indent=2,sort_keys=True))


if __name__=="__main__":
    main()
