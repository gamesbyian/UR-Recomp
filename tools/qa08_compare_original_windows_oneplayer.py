#!/usr/bin/env python3
"""Strict source-size original Snes9x vs real pinned Windows 1P RGB5 ranking.

Scientific positive OR negative. Enforces genuine immutable 1P routes,
original emulator callback bytes, exact guest2208 source RGBA and complete
actual input/guest route receipt. Does not silently align camera or clocks,
mask pixels, crop 224→216, replace Original sprites, or grant release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_original_oneplayer_source_manifest import (
        FIRST,LAST,SCHEMA as ORIGINAL_SCHEMA,ROM_SHA,
    )
    from tools.qa08_windows_oneplayer_source_capture import (
        EXE_SHA,HEADER,FRAMES,
    )
except ImportError:
    from qa08_original_oneplayer_source_manifest import (
        FIRST,LAST,SCHEMA as ORIGINAL_SCHEMA,ROM_SHA,
    )
    from qa08_windows_oneplayer_source_capture import (
        EXE_SHA,HEADER,FRAMES,
    )

W,H=256,224
PX=W*H
WINDOW=range(FIRST,LAST+1)
SCHEMA="qa08-real-original-snes9x-vs-exact-windows-1p-rgb5-window/1"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def no_turbo(script:bytes)->bytes:
    return b"".join(x for x in script.splitlines(keepends=True)
                    if not x.startswith(b"turbo "))


def read_native(path:Path)->bytes:
    raw=path.read_bytes()
    if len(raw)!=len(HEADER)+PX*4 or not raw.startswith(HEADER):
        raise ValueError("actual Windows 1P PPU source cropped or invalid")
    return raw[len(HEADER):]


def compare(source_BGRX:bytes,native_RGBA:bytes)->dict:
    if len(source_BGRX)!=PX*4 or len(native_RGBA)!=PX*4:
        raise ValueError("requires complete 256x224 original/native source image")
    wrong=0
    by_row={}
    examples=[]
    for p in range(PX):
        pos=p*4
        blue,green,red,_=source_BGRX[pos:pos+4]
        green5=green>>3
        normalized=(red,(green5<<3)|(green5>>2),blue)
        actual=tuple(native_RGBA[pos:pos+3])
        if normalized!=actual:
            wrong+=1
            y=p//W
            by_row[y]=by_row.get(y,0)+1
            if len(examples)<8:
                examples.append({"x":p%W,"y":y,
                                 "original_rgb5_expanded":normalized,
                                 "windows_source_rgb":actual})
    return {"same_RGB5_pixels":PX-wrong,"wrong_RGB5_pixels":wrong,
            "wrong_pixels_by_row":by_row,"first_eight_wrong":examples}


def analyze(original_dir:Path,win_dir:Path,route:Path)->dict:
    original=json.loads((original_dir/"qa08-original-1p-source.json").read_text())
    windows=json.loads((win_dir/"qa08-windows-1p-source.json").read_text())
    raw_route=route.read_bytes()
    original_script=original_dir/"qa08-original-1p.script"
    if (original.get("schema")!=ORIGINAL_SCHEMA
        or original.get("original_USA_ROM_sha256")!=ROM_SHA
        or original.get("source_geometry")!=[W,H]
        or original.get("callback_count")!=len(WINDOW)
        or original.get("actual_original_callback_range")!=[FIRST,LAST]
        or original.get("release_approved") is not False):
        raise ValueError("missing authentic original Snes9x 1P callback producer")
    if (sha(raw_route)!=windows.get("native_input_script_sha256")
        or sha(no_turbo(raw_route))!=original.get(
            "unchanged_original_route_no_turbo_SHA256")
        or no_turbo(raw_route)!=original_script.read_bytes()):
        raise ValueError("two observed original/native routes differ in source input")
    if (windows.get("schema")!="qa08-windows-real-1p-original-source-observer/1"
        or windows.get("actual_windows_binary_sha256")!=EXE_SHA
        or windows.get("original_USA_ROM_sha256")!=ROM_SHA
        or windows.get("guest2208_captured_in_source") is not True
        or windows.get("source_geometry")!=[W,H]
        or windows.get("release_gate_approved") is not False):
        raise ValueError("Windows source was not the exact independently pinned binary")
    source=win_dir/"source"/"ur-baldosa-original-source-002208.pam"
    native=read_native(source)
    if (sha(source.read_bytes())!=windows.get(
        "unmodified_source_P7_sha256_by_guest_frame",{}).get("2208")):
        # JSON numeric keys become string keys; only actual frame2208 counts.
        raise ValueError("actual Windows source PPU raw bytes do not match capture")
    originals=original.get("actual_source_frames")
    if not isinstance(originals,list) or len(originals)!=len(WINDOW):
        raise ValueError("original source 65-frame manifest incomplete")
    rankings=[]
    observed_original_hashes=set()
    for frame,row in zip(WINDOW,originals):
        if (row.get("original_callback_frame_zero_based")!=frame
            or row.get("original_retro_run_one_based")!=frame+1):
            raise ValueError("original callback frame identity mislabelled")
        path=original_dir/"frames"/f"frame_{frame:06d}_256x224.raw"
        raw=path.read_bytes()
        if sha(raw)!=row.get("unmodified_BGRX8888_sha256"):
            raise ValueError("original callback SHA does not match genuine producer")
        observed_original_hashes.add(sha(raw))
        result=compare(raw,native)
        rankings.append({"original_callback":frame,
                         "original_run_frame":frame+1,
                         "same_RGB5_pixels":result["same_RGB5_pixels"],
                         "wrong_RGB5_pixels":result["wrong_RGB5_pixels"],
                         "wrong_pixels_by_row":result["wrong_pixels_by_row"],
                         "first_eight_wrong":result["first_eight_wrong"]})
    if len(observed_original_hashes)<8:
        raise ValueError("original 1P sample window appears held/duplicated")
    best=sorted(rankings,key=lambda r:(-r["same_RGB5_pixels"],r["original_callback"]))
    return {
        "schema":SCHEMA,
        "status":("actual_source_pixel_exact_sample" if best[0]["wrong_RGB5_pixels"]==0
                  else "valid_authentic_moving_1p_source_strict_divergence"),
        "real_windows_binary_sha256":EXE_SHA,
        "actual_windows_guest_frame":2208,
        "original_USA_ROM_sha256":ROM_SHA,
        "unmodified_shared_route_sha256":sha(raw_route),
        "original_raster_source_size":[W,H],
        "genuine_original_callbacks":len(rankings),
        "native_guest_CRC_records":windows["actual_guest_frames_simulated"],
        "native_guest_CRC_sha256":windows["guest_CRC_lowercase_sha256"],
        "actual_windows_1p_frame2208_P7_sha256":sha(source.read_bytes()),
        "original_callback_best_by_RGB5_pixels":best[0]["original_callback"],
        "best_original_callback_ranking_margin":(
            best[0]["same_RGB5_pixels"]-best[1]["same_RGB5_pixels"]),
        "original_callback_2207_prespecified_comparison":rankings[2207-FIRST],
        "best_pixel_comparison":best[0],
        "all_original_callback_scores":rankings,
        "same_CPU_camera_input_phase_proven":False,
        "continuous_1P_event_result_and_persistence_accepted":False,
        "no_216_high_crop_or_masking":True,
        "Windows_original_7_6_PAR_and_widescreen_4x_acceptance_separate":True,
        "current_remastered_racer_art_owner_approved":False,
        "release_quality_ledger_gate_admitted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-dir",required=True,type=Path)
    p.add_argument("--windows-dir",required=True,type=Path)
    p.add_argument("--route",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=analyze(a.original_dir,a.windows_dir,a.route)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("QA08_REAL_ORIGINAL_WIN_1P_SRC status="+result["status"],
          "native_guest=2208","best_original_callback="+
          str(result["original_callback_best_by_RGB5_pixels"]),
          "wrong="+str(result["best_pixel_comparison"]["wrong_RGB5_pixels"]),
          "release_gate=unaccepted")


if __name__=="__main__":
    main()
