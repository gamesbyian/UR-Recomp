#!/usr/bin/env python3
"""Strict real original/native 2P source-size RGB pixel seam regression.

Requires *two independently executed, exact-SHA archived* emulator builds.
Original Snes9x RGB565 uses green6; native Baldosa source PPU RGB8 is
expanded green5. Normalize ONLY the demonstrated 6->5 green quantization.
No same-input ROM/guest-WRAM parity, hardware correctness or 342-wide crop
is asserted from framebuffer agreement.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP_SHA="6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3"
NATIVE_ZIP_SHA="2716fc6a21b7ac75a05b9ce26d270b7bf0c1e575e75e74e550665b2a899e5302"
ORIGINAL_MANIFEST_SHA="29856fa4f13bfc679b60240de80bd48b8c035801b56e0fbb3e17472a06836787"
ORIGINAL_2207_SHA="e76c6010b3fb339ecbdae2fec985a00019345723cdff122d9bbc78d71481c8aa"
NATIVE_P7_SHA="a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
INPUT_SHA="94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
WRAM_SHA="9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6"
ORIGINAL_WINDOW_SCHEMA="qa08-source-original-2P-37-full-PPU-raster-frames-2188-2224/1"
NATIVE_PATH="baldosa-fixed-source/ur-baldosa-original-source-002208.pam"
W,H=256,224


def sha(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()


def strict_json(data: bytes) -> dict:
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:
                raise ValueError("duplicate original/native attestation field")
            out[k]=v
        return out
    res=json.loads(data,object_pairs_hook=unique)
    if not isinstance(res,dict):
        raise ValueError("incorrect source manifest")
    return res


def rgb5_match(original:bytes,native:bytes,*,with_rows:bool=False)->dict:
    if len(original)!=W*H*4 or len(native)!=W*H*4:
        raise ValueError("source 256x224 frame byte count differs")
    identical=0
    bad=Counter()
    green_conversion=Counter()
    for y in range(H):
        for x in range(W):
            i=4*(y*W+x)
            b,g,r,zero=original[i:i+4]
            nr,ng,nb,_=native[i:i+4]
            if zero!=0:
                raise ValueError("original BGRX source has unexpected fourth component")
            green6=g>>2
            if ((green6<<2)|(green6>>4))!=g:
                raise ValueError("original screenshot is not Snes9x RGB565 expanded green6")
            green5=green6>>1
            normalized=(green5<<3)|(green5>>2)
            if normalized==ng:
                green_conversion[g]=normalized
            if (r,normalized,b)==(nr,ng,nb):
                identical+=1
            else:
                bad[y]+=1
    result={"identical_RGB5_expanded_pixels":identical,
            "total_pixels":W*H,
            "different_pixels":W*H-identical}
    if with_rows:
        result["different_pixels_by_original_output_row"]=[
            {"row":y,"different":count} for y,count in sorted(bad.items())]
        result["Snes9x_green6_RGB8_to_native_green5_RGB8_unique_conversions"]=[
            {"Snes9x_RGB8_green6":x,"native_RGB8_green5":green_conversion[x]}
            for x in sorted(green_conversion)]
    return result


def check(original_zip_path:Path,native_zip_path:Path)->dict:
    original_raw=original_zip_path.read_bytes()
    native_raw=native_zip_path.read_bytes()
    if sha(original_raw)!=ORIGINAL_ZIP_SHA or sha(native_raw)!=NATIVE_ZIP_SHA:
        raise ValueError("original or native source archive exact content SHA differs")
    with zipfile.ZipFile(original_zip_path) as oz,zipfile.ZipFile(native_zip_path) as nz:
        manifest_raw=oz.read("qa08-original-37frame-window.json")
        manifest=strict_json(manifest_raw)
        receipt=strict_json(oz.read("qa08-original-opcode-receipt.json"))
        info=strict_json(oz.read("qa08-original-opcode-dumps/go.info.json"))
        if (sha(manifest_raw)!=ORIGINAL_MANIFEST_SHA or
                manifest.get("schema")!=ORIGINAL_WINDOW_SCHEMA or
                manifest.get("full_256x224_original_frames")!=37 or
                manifest.get("original_ROM_SHA256")!=ROM_SHA or
                manifest.get("original_script_SHA256")!=INPUT_SHA or
                manifest.get("original_t480_WRAM_SHA256")!=WRAM_SHA or
                manifest.get("same_input_guest_phase_and_camera_as_native_proven") is not False or
                receipt.get("USA_ROM_SHA256")!=ROM_SHA or
                receipt.get("original_script_SHA256")!=INPUT_SHA or
                receipt.get("original_t480_WRAM_SHA256")!=WRAM_SHA or
                receipt.get("actual_executed_original_instruction_count")!=55 or
                receipt.get("source_65816_writer_PCs")!=18 or
                receipt.get("second_camera_0DDB")!=1 or
                receipt.get("in_race_0313")!=1 or
                receipt.get("native_same_input_frame_parity_proven") is not False or
                info.get("frame")!=1989 or
                info.get("fb_core_pixel_format")!="RGB565" or
                info.get("fb_width")!=256 or info.get("fb_height")!=224 or
                info.get("layer_mask")!="1F" or
                info.get("no_colormath") is not False or
                info.get("no_clip") is not False):
            raise ValueError("original Snes9x source route, pixel format or image manifest not admitted")
        np7=nz.read(NATIVE_PATH)
        head,sep,native=np7.partition(b"ENDHDR\n")
        if (sha(np7)!=NATIVE_P7_SHA or
                not sep or
                head!=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\n"):
            raise ValueError("authentic native 256x224 2P original-source P7 absent")
        rows=manifest.get("source_original_frames")
        if not isinstance(rows,list) or len(rows)!=37:
            raise ValueError("missing source original 37-frame manifest")
        totals=[]
        for i,record in enumerate(rows):
            fr=2188+i
            if (record.get("original_Snesref_callback_frame_zero_based")!=fr or
                    record.get("corresponding_original_retro_run_one_based")!=fr+1):
                raise ValueError("false original callback to script frame registration")
            path=f"qa08-original-source-window/frame_{fr:06d}_256x224.raw"
            frame=oz.read(path)
            if sha(frame)!=record.get("raw_B_G_R_X_SHA256"):
                raise ValueError("actual original 2P frame byte hash diverges")
            actual=rgb5_match(frame,native,with_rows=fr==2207)
            totals.append({"original_callback_frame":fr,
                           "original_retro_run_frame":fr+1,
                           **actual})
        best=sorted(totals,key=lambda r:(-r["identical_RGB5_expanded_pixels"],r["original_callback_frame"]))
        top=best[0]
        if (top["original_callback_frame"]!=2207 or
                top["identical_RGB5_expanded_pixels"]!=56832 or
                top["different_pixels"]!=512 or
                top["different_pixels_by_original_output_row"]!=[
                    {"row":111,"different":256},{"row":113,"different":256}] or
                sha(oz.read("qa08-original-source-window/frame_002207_256x224.raw"))!=ORIGINAL_2207_SHA or
                best[1]["identical_RGB5_expanded_pixels"]>=top["identical_RGB5_expanded_pixels"]-10000):
            raise ValueError("genuine original/native 2P split-band pixel alignment differs")
        original=oz.read("qa08-original-source-window/frame_002207_256x224.raw")
        black=lambda pic,y:all(
            (pic[(y*W+x)*4] ==0 and pic[(y*W+x)*4+1] ==0 and
             pic[(y*W+x)*4+2] ==0)
            for x in range(W))
        if not (black(original,111) and black(original,112)
                and black(native,112) and black(native,113)):
            raise ValueError("original/native two-row forced-black split evidence changed")
        return {
            "schema":"qa08-original-Snes9x-vs-native-2P-exact-seam-pixel-discriminator/1",
            "status":"independent-original-native-source-frame-RGB5-equality-except-two-complete-seam-rows",
            "original_Snes9x_source_run":38543766102,
            "original_Snes9x_source_artifact":11884155561,
            "original_archive_SHA256":ORIGINAL_ZIP_SHA,
            "native_source_run":38504531564,
            "native_source_artifact":11867072862,
            "native_archive_SHA256":NATIVE_ZIP_SHA,
            "original_callback_frame":2207,
            "original_retro_run_frame":2208,
            "native_guest_frame":2208,
            "original_256x224_raw_RGB_source_SHA256":ORIGINAL_2207_SHA,
            "native_256x224_original_source_P7_SHA256":NATIVE_P7_SHA,
            "original_Snes9x_video_RGB565_native_pixel_RGB5_conversion":"only green6 down to 5 bits then standard five-bit expansion",
            "pixels_original_native_identical_after_justified_green_conversion":56832,
            "pixels_in_original_source":57344,
            "different_RGB_pixels":512,
            "original_native_mismatch_rows_full_256px_each":[111,113],
            "original_forced_blank_rows":[111,112],
            "native_forced_blank_rows":[112,113],
            "verified_complete_original_frame_candidate_margin_over_second":top["identical_RGB5_expanded_pixels"]-best[1]["identical_RGB5_expanded_pixels"],
            "next_best_original_callback_frame":best[1]["original_callback_frame"],
            "complete_original_scene_time_alignment_from_pixel_data":True,
            "full_original_native_Wram_input_route_and_camera_parity_proven":False,
            "physical_hardware_HBlank_timing_proven":False,
            "source_frame_342wide_PPU_cropped_or_compared":False,
            "remastered_racer_likeness_approved":False,
            "source_per_frame_pixel_matches":[{"original_callback_frame":r["original_callback_frame"],
                                               "exact_after_normalization":r["identical_RGB5_expanded_pixels"]}
                                              for r in totals],
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip",type=Path,required=True)
    p.add_argument("--native-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=check(a.original_zip,a.native_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("QA08_ORIGINAL_NATIVE_EXACT_2P_PIXEL_SEAM_ACCEPTED "
          "normalized_identical=56832/57344 seam_mismatch_rows=111,113 "
          "physical_timing=unproven")

if __name__=="__main__": main()
