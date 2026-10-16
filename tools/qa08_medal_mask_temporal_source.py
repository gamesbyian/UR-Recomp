#!/usr/bin/env python3
"""QA-08: archived 2P result-medal mask, temporal transparency discrimination.

Uses only authentic immutable 2014 Snes9x full-route source video and the
actual Win32 Original P7 full-route source, both SHA-pinned inside the 90-day
retained archive. No emulator, rendered rerun, synthetic frame, temporal
alignment, spatial shift, background masking or colour correction. It records
source-pixel mismatch locations and original-vs-native colour changes, not
proof of *why* any OBJ/background layer won or of completed USA events.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

ORIG_SHA="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
WIN_SHA="4f766de13c702a108279293df4613538d8b49cbd1ecbc0876533c5f01f09293c"
FULL_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
SOURCE_SIZE=(256,224)
HEADER=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
NON_GRAY=(4032,4080,4128,4224,4272,4320,4368,4416,4464,4560,4608,4656,
          4704,4752,4800,4896,4944,4992,5040,5088,5136)
GRAY=(4176,4512,4848,5184)
COORD_COUNT=256*224

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def bgrx_to_rgb5_expanded(src:bytes)->bytes:
    if len(src)!=COORD_COUNT*4:
        raise ValueError("requires complete original 256x224 BGRX source field")
    out=bytearray(COORD_COUNT*3)
    for p in range(COORD_COUNT):
        i=p*4;j=p*3
        blue,green,red=src[i:i+3]
        out[j]=red
        green5=green>>3
        out[j+1]=(green5<<3)|(green5>>2)
        out[j+2]=blue
    return bytes(out)


def read_source(o:zipfile.ZipFile,w:zipfile.ZipFile,guest:int,
                om:dict,wm:dict)->tuple[bytes,bytes]:
    if guest<1280 or guest>5472 or guest%16:
        raise ValueError("not one predeclared original/native callback pair")
    callback=guest-1
    original=o.read(f"frames/frame_{callback:06d}_256x224.raw")
    if (len(original)!=COORD_COUNT*4 or
        sha(original)!=om[callback]["original_unchanged_BGRX_sha256"]):
        raise ValueError("immutable original source image hash changed")
    native=w.read(f"source/ur-baldosa-original-source-{guest:06d}.pam")
    if (not native.startswith(HEADER) or len(native)!=len(HEADER)+COORD_COUNT*4 or
        sha(native)!=wm[str(guest)]):
        raise ValueError("actual Win32 P7 original logical field drifted")
    rgba=native[len(HEADER):]
    rgb=bytearray(COORD_COUNT*3)
    for p in range(COORD_COUNT):
        rgb[3*p:3*p+3]=rgba[4*p:4*p+3]
    return bgrx_to_rgb5_expanded(original),bytes(rgb)


def differing_pixels(a:bytes,b:bytes)->set[int]:
    if len(a)!=len(b) or len(a)!=COORD_COUNT*3:
        raise ValueError("full original/native 256x224 24-bit RGB5 field required")
    return {p for p in range(COORD_COUNT)
            if a[3*p:3*p+3]!=b[3*p:3*p+3]}


def components_of_mask(points:set[int])->list[dict]:
    """Eight-connected strictly mismatching source coordinates, never mask input."""
    pending=set(points);groups=[]
    while pending:
        first=pending.pop();todo=[first];group=[first]
        while todo:
            n=todo.pop();x,y=n%256,n//256
            for yy in range(max(0,y-1),min(224,y+2)):
                for xx in range(max(0,x-1),min(256,x+2)):
                    candidate=yy*256+xx
                    if candidate in pending:
                        pending.remove(candidate);todo.append(candidate);group.append(candidate)
        ys=[z//256 for z in group];xs=[z%256 for z in group]
        groups.append({"pixels":len(group),"bbox_xyxy":[min(xs),min(ys),max(xs),max(ys)]})
    return sorted(groups,key=lambda j:(-j["pixels"],j["bbox_xyxy"]))


def analyze(original_zip:Path,win_zip:Path)->dict:
    if sha(original_zip.read_bytes())!=ORIG_SHA or sha(win_zip.read_bytes())!=WIN_SHA:
        raise ValueError("not original/pinned genuine native 2P source archives")
    with zipfile.ZipFile(original_zip) as o,zipfile.ZipFile(win_zip) as w:
        original=json.loads(o.read("qa08-original-2p-fullroute.json"))
        native=json.loads(w.read("qa08-windows-2p-fullroute.json"))
        if (original.get("actual_callbacks_captured")!=263
            or original.get("capture_selection")!=[1279,5471,16]
            or original.get("native_unmasked_geometry")!=[256,224]
            or native.get("actual_source_count")!=263
            or native.get("source_frames_expected_and_observed")!=[1280,5472,16]
            or native.get("source_geometry")!=[256,224]
            or native.get("actual_native_guest_CRC_sha256")!=FULL_CRC):
            raise ValueError("original/native source manifest or unchanged guest CRC wrong")
        om={r["real_original_snes9x_callback_frame"]:r for r in
            original["each_authentic_callback"]}
        wm=native["source_frame_P7_SHA256_by_guest"]
        if len(om)!=263 or len(wm)!=263:
            raise ValueError("missing full 263-image provenance")
        sample_frames={guest:read_source(o,w,guest,om,wm) for guest in
                       sorted(set(NON_GRAY+GRAY))}
    masks={guest:differing_pixels(*pair) for guest,pair in sample_frames.items()}
    canonical=masks[NON_GRAY[0]]
    if (len(canonical)!=296 or any(masks[guest]!=canonical for guest in NON_GRAY)):
        raise ValueError("21 real result-medal frames have nonpersistent wrong-pixel mask")
    xs=[z%256 for z in canonical];ys=[z//256 for z in canonical]
    bbox=[min(xs),min(ys),max(xs),max(ys)]
    if bbox!=[202,91,227,153]:
        raise ValueError("real on-screen medal mask not source-position authentic")
    comps=components_of_mask(canonical)
    if sorted([x["pixels"] for x in comps],reverse=True)!=[93,92,87,9,9,2,1,1,1,1]:
        raise ValueError("original/native medal mismatch connected regions drifted")
    changes=Counter()
    candidates=sorted(canonical)
    for p in candidates:
        def rgb_at(guest:int,which:int)->bytes:
            return sample_frames[guest][which][p*3:p*3+3]
        a0=rgb_at(NON_GRAY[0],0);b0=rgb_at(NON_GRAY[0],1)
        orig_static=all(rgb_at(f,0)==a0 for f in NON_GRAY)
        win_static=all(rgb_at(f,1)==b0 for f in NON_GRAY)
        changes[("original_static" if orig_static else "original_changes",
                 "win_static" if win_static else "win_changes")]+=1
    stat={
        "both_static":changes[("original_static","win_static")],
        "original_changes_win_static":changes[("original_changes","win_static")],
        "original_static_win_changes":changes[("original_static","win_changes")],
        "both_change":changes[("original_changes","win_changes")],
    }
    if stat!={"both_static":249,"original_changes_win_static":41,
              "original_static_win_changes":6,"both_change":0}:
        raise ValueError("source-qualified medal compositing/phase colour stability changed")
    gray_other={}
    for f in GRAY:
        if not canonical.issubset(masks[f]):
            raise ValueError("four original/native grey-phase fields lost the 296 medal pixels")
        gray_other[str(f)]={"total_incorrect_RGB5_pixels":len(masks[f]),
                            "canonical_medal_pixels":296,
                            "wrong_outside_medal_mask":len(masks[f]-canonical)}
    if [gray_other[str(f)]["wrong_outside_medal_mask"] for f in GRAY]!=[24415,24481,24626,24336]:
        raise ValueError("four independently source-captured gray-phase outer mask shifted")
    return {
        "schema":"qa08-source-original-native-two-player-medal-mask-temporal-colours/1",
        "source_2014_Snes9x_original_ZIP_SHA256":ORIG_SHA,
        "source_actual_Windows_PPU_ZIP_SHA256":WIN_SHA,
        "unmodified_full_5484_guest_CRC_SHA256":FULL_CRC,
        "source_size":[256,224],
        "frame_pairing":"original video callback = native guest minus one; no frame search",
        "pixel_colour_normalization":"historical Snes9x G6 to G5 only",
        "source_non_gray_sampled_guest_frames":[*NON_GRAY],
        "non_gray_21_full_source_frames_each_296_wrong_pixels":True,
        "persistent_medal_mask_pixels":296,
        "medal_mask_bbox_xyxy":bbox,
        "eight_connected_wrong_pixel_components":comps,
        "original_vs_native_21_frame_temporal_colour_stability":stat,
        "gray_phase_sampled_guest_frames":[*GRAY],
        "gray_phase_persistent_medal_mask_present_in_all_four":True,
        "gray_phase_wrong_pixels_outside_fixed_medal_mask":gray_other,
        "total_25_selected_medal_mask_wrong_source_pixels":25*296,
        "not_a_single_global_RGB_recolour_test":True,
        "original_effective_medal_OBJ_BG_window_priority_proven":False,
        "CPU_PPU_cause_or_SNES_DAC_stage_proven":False,
        "visual_source_resampled_or_modified":False,
        "release_QA08_QA10_approved":False,
        "next_discriminator":"join exact original Snes9x callback4031/4175 live medal PPU depth/OAM and already accepted native Win32 owner pixels at native4032/4176; do not apply global palette, ±2 tile correction or time shift"
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original-zip","windows-zip","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.original_zip,a.windows_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_MEDAL_296 mask=296 samples=21+4 original_changes_native_static=41 original_static_native_changes=6 no_new_sprite_edit=1")


if __name__=="__main__":
    main()
