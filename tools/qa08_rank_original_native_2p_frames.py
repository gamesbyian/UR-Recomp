#!/usr/bin/env python3
"""Rank genuine original Snes9x 2P 256x224 frames against native source-size 2P.

Similarity is merely an alignment *candidate*. Without same-controller,
camera/WRAM and exact source phase parity it NEVER constitutes event
oracle acceptance or permission to patch production PPU/Widescreen.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA="qa08-source-original-2P-37-full-PPU-raster-frames-2188-2224/1"
REFERENCE_SHA="a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f"
REGION={
    "full":(0,0,256,224),
    "upper_play":(32,32,208,80),
    "lower_play":(32,144,208,192),
    "split_edge":(0,104,256,120),
}
WIDTH=256
HEIGHT=224

def read_json(path:Path):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError("duplicated original/native pixel source field")
            out[k]=v
        return out
    return json.loads(path.read_text(encoding="utf8"),object_pairs_hook=unique)

def load_native(path:Path)->bytes:
    payload=path.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=REFERENCE_SHA:
        raise ValueError("native 2P guest2208 exact source-size P7 image SHA differs")
    head,sep,raster=payload.partition(b"ENDHDR\n")
    if (not sep or head !=
            b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\n"
            or len(raster)!=WIDTH*HEIGHT*4):
        raise ValueError("native 256x224 original-source P7 layout differs")
    # Native's 'ALPHA=0' means PPU screen is source data. The reported
    # pixels are still meaningful; its 4th channel is deliberately ignored.
    return raster

def rank(original_window:Path, manifest:dict, native_p7:bytes, handoff:dict)->dict:
    if (manifest.get("schema")!=SCHEMA
            or manifest.get("original_ROM_SHA256")!=
                "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
            or manifest.get("original_script_SHA256")!=
                "94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
            or manifest.get("full_256x224_original_frames")!=37
            or manifest.get("same_input_guest_phase_and_camera_as_native_proven") is not False
            or manifest.get("original_vs_native_final_RGBA_parity_proven") is not False
            or handoff.get("schema")!=
                "qa08-original-native-channel5-coldata-source-handoff/1"
            or handoff.get("original_native_AOT_run")!=38504531564
            or handoff.get("native_PPU_2P_guest_frame")!=2208
            or handoff.get("identical_original_guest_CRC_records")!=2473
            or handoff.get("downloaded_zip_sha256")!=
                "2716fc6a21b7ac75a05b9ce26d270b7bf0c1e575e75e74e550665b2a899e5302"
            or len(native_p7)!=WIDTH*HEIGHT*4):
        raise ValueError("independent original/native 2P witness identity absent")
    refs=manifest.get("source_original_frames")
    if not isinstance(refs,list) or len(refs)!=37:
        raise ValueError("source-frame manifest missing exact sequence")
    results=[]
    for i,entry in enumerate(refs):
        frame=2188+i
        if (entry.get("original_Snesref_callback_frame_zero_based")!=frame
            or entry.get("corresponding_original_retro_run_one_based")!=frame+1):
            raise ValueError("forged original framebuffer callback/retro_run frame")
        source=(original_window/f"frame_{frame:06d}_256x224.raw").read_bytes()
        if (len(source)!=WIDTH*HEIGHT*4 or
            hashlib.sha256(source).hexdigest()!=entry.get("raw_B_G_R_X_SHA256")):
            raise ValueError("original frame did not match real source PPU image hash")
        row={"original_callback_frame":frame,"original_run_frame":frame+1,"regions":{}}
        for name,(left,top,right,bottom) in REGION.items():
            equal=0;total=(right-left)*(bottom-top);sad=0
            for y in range(top,bottom):
                for x in range(left,right):
                    off=4*(WIDTH*y+x)
                    b,g,r=source[off:off+3]
                    nr,ng,nb=native_p7[off:off+3]
                    if b==nb and g==ng and r==nr:equal+=1
                    sad+=abs(r-nr)+abs(g-ng)+abs(b-nb)
            row["regions"][name]={
                "equal_rgb_pixels":equal,"region_pixels":total,
                "mean_RGB_channel_absolute_difference":round(sad/(3*total),5),
                "exact_pixel_fraction":round(equal/total,8)}
        results.append(row)
    ranked=sorted(results,key=lambda r:(
        -r["regions"]["upper_play"]["exact_pixel_fraction"]
         -r["regions"]["lower_play"]["exact_pixel_fraction"],
        r["regions"]["full"]["mean_RGB_channel_absolute_difference"],
        r["original_callback_frame"]))
    return {
        "schema":"qa08-original-native-source-size-2P-frame-similarity-candidate/1",
        "original_emulator_source_window":[2188,2224],
        "native_guest_frame":2208,
        "native_original_source_image_P7_SHA256":REFERENCE_SHA,
        "source_pixels_compared_without_scaling_or_crop":True,
        "unmodified_source_original_core_route_required":True,
        "original_native_exact_gameplay_state_and_2P_camera_alignment_proven":False,
        "original_native_final_RGB_composition_parity_proven":False,
        "best_visual_frame_only_unverified_hypothesis":ranked[0]["original_callback_frame"],
        "all_source_frame_similarity_by_original_callback":results,
        "sorted_candidate_frames":[r["original_callback_frame"] for r in ranked[:10]],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("original-window","original-manifest","native-256-p7","native-evidence","out"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    report=rank(a.original_window,read_json(a.original_manifest),
                load_native(a.native_256_p7),read_json(a.native_evidence))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("QA08_VISUAL_PHASE_ALIGNMENT_CANDIDATES_ONLY "
          f"top_callback={report['best_visual_frame_only_unverified_hypothesis']} "
          "guest_input_parity=unproved")

if __name__=="__main__":main()
