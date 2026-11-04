#!/usr/bin/env python3
"""Tiny read-only original Mesen24 2D upper-source integer-shift diagnostic.

The source is 1994 executed 2D OAM/VRAM/CGRAM, not an original 3D rig.
Only diagnostic already-inspected source edges; no blind 3D test.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-MESEN24-SOURCE-UPPER-BAND-BOUNDED-2D-TRANSLATION/1"
SOURCE_ZIP_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
TICKS=tuple(range(1601,1625))
SOURCE_ROLES={"blue":(96,4,14,(1602,1603)),"red":(97,5,15,(1605,1606))}
SHIFTS=tuple((dx,dy) for dx in range(-2,3) for dy in range(-2,3))


def sha(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()


def translated(source:bytes,dx:int,dy:int)->bytes:
    """Zero-filled source-local 64x64 shift, never wrap or resample."""
    if not isinstance(source,bytes) or len(source)!=4096:
        raise ValueError("exact 64x64 original source plane required")
    if type(dx) is not int or type(dy) is not int or not -2<=dx<=2 or not -2<=dy<=2:
        raise ValueError("only bounded integer shifts are admissible")
    out=bytearray(4096)
    for y in range(max(0,dy),min(64,64+dy)):
        for x in range(max(0,dx),min(64,64+dx)):
            out[y*64+x]=source[(y-dy)*64+(x-dx)]
    return bytes(out)


def score(a:dict,b:dict,lower:int,upper:int,dx:int,dy:int)->dict:
    """Compare source mask and independent source 4bpp indexes, not screen."""
    if type(lower) is not int or type(upper) is not int or not 0<=lower<=upper<64:
        raise ValueError("source band outside 64px sprite")
    mask_a=translated(a["alpha_mask"],dx,dy)
    plane_a=translated(a["plane"],dx,dy)
    mask_b=b["alpha_mask"]
    plane_b=b["plane"]
    cells=range(lower*64,(upper+1)*64)
    return {"dx":dx,"dy":dy,
            "upper_alpha_xor":sum(mask_a[i]!=mask_b[i] for i in cells),
            "upper_index_mismatch":sum(plane_a[i]!=plane_b[i] for i in cells)}


def analyze(before:dict,after:dict,lo:int,hi:int)->dict:
    baseline=score(before,after,lo,hi,0,0)
    candidates=[score(before,after,lo,hi,dx,dy) for dx,dy in SHIFTS]
    minimum=min(x["upper_alpha_xor"] for x in candidates)
    tied=[x for x in candidates if x["upper_alpha_xor"]==minimum]
    selected=min(tied,key=lambda x:(x["upper_index_mismatch"],
             abs(x["dx"])+abs(x["dy"]),x["dy"],x["dx"]))
    return {"baseline":baseline,"lowest_upper_alpha_xor":minimum,
            "all_alpha_minima":tied,"preferred_by_index_and_magnitude":selected}


def audit(source:bytes)->dict:
    if len(source)>1_000_000 or sha(source)!=SOURCE_ZIP_SHA:
        raise ValueError("not the authenticated original 24-tick source ZIP")
    per={}
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        manifest=json.loads(z.read("manifest.json"))
        if manifest.get("source_requested_capture_ticks")!=list(TICKS):
            raise ValueError("not the consecutively executed original Mesen ticks")
        for name,(slot,lo,hi,event) in SOURCE_ROLES.items():
            rasters=[]
            for tick in TICKS:
                oam=decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot]
                sprite=decode_source_obj(oam,z.read(f"frame-{tick:06d}-vram.bin"),
                           z.read(f"frame-{tick:06d}-cgram.bin"),
                           oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                if sprite["size"]!=64 or sprite["slot"]!=slot:
                    raise ValueError("wrong original source OBJ role or size")
                rasters.append(sprite)
            edges=[{"from_tick":1601+i,"to_tick":1602+i,
                    **analyze(rasters[i],rasters[i+1],lo,hi)}
                    for i in range(23)]
            changed=[r for r in edges if r["baseline"]["upper_alpha_xor"]!=0]
            improved=[r for r in edges
                      if r["lowest_upper_alpha_xor"]<r["baseline"]["upper_alpha_xor"]]
            if (len(changed)!=1 or len(improved)!=1 or
                    (changed[0]["from_tick"],changed[0]["to_tick"])!=event):
                raise ValueError("original source upper-event census changed")
            per[name]={"source_image_y_band":[lo,hi],
                "actual_upper_source_event":[*event],
                "baseline_unchanged_upper_edges":23-len(changed),
                "upper_edges_improved_by_bounded_2d_shift":len(improved),
                "original_23_consecutive_source_edge_comparisons":edges}
    return {"schema":SCHEMA,
            "source_actual_original_mesen_zip_sha256":SOURCE_ZIP_SHA,
            "source_actual_original_ticks":list(TICKS),
            "candidate_integer_shift_bounds_inclusive":[-2,2],
            "source_shift_zero_fill_no_wrap":True,
            "searched_observed_2d_only_not_3d_pose":True,
            "source_original_1994_rig_camera_or_pose_recovered":False,
            "original_PPU_final_screen_pixel_ownership_proven_by_this_audit":False,
            "source_frames_prospective_blind_holdout":False,
            "per_source_player":per}


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.archive.read_bytes())
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
       name:next(x for x in v["original_23_consecutive_source_edge_comparisons"]
                 if [x["from_tick"],x["to_tick"]]==v["actual_upper_source_event"])
       for name,v in result["per_source_player"].items()},sort_keys=True))


if __name__=="__main__":
    main()
