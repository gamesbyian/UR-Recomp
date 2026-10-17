#!/usr/bin/env python3
"""QA-08: source-qualified 2P finish palette/half-math counterfactual.

Inputs are a verified 512-byte original Snes9x CGRAM captured at guest 3683
(finish fade) and the separate exact original/real Win32 source pixel receipt
for 3792 and 3872. Do NOT assert that the earlier palette is unchanged at
either later visible PPU pixel, or that main BG/sub OBJ wins in the original.
Hypothesis: source main BG palette entry <128 and subscreen OBJ >=128,
half-add active, brightness=7. Enumerate all possible pairs, don't select one.
No emulation, game, sprite, renderer, timing or source-image modification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_CGRAM_SHA = "b7aca48a35b4152ea7ce9a17ed68a08c9eed1e583397508b197e29dc50f73067"
EXPECTED_REFERENCE_RGB8 = (49,24,0)
EXPECTED_NATIVE_RGB8 = (57,24,0)
BRIGHTNESS = 7
EXPECTED_SOURCE_PAIRS = ((23,153),(23,201),(56,226),(58,135))
REPORT_SCHEMA = "qa08-certified-2014-snes9x-original-vs-real-win32-two-rare-finish-pixels/1"


def rgb5(word:int)->tuple[int,int,int]:
    if not 0<=word<=32767:
        raise ValueError("outside SNES CGRAM 15-bit range")
    return word&31, (word>>5)&31, (word>>10)&31


def b5(channel:int,brightness:int)->int:
    if not 0<=channel<=31 or not 0<=brightness<=15:
        raise ValueError("invalid 5-bit channel / INIDISP brightness")
    return (channel*brightness+7)//15


def expand5(c:int)->int:
    return (c<<3)|(c>>2)


def original_brightness_then_half(main:tuple[int,int,int],
                                  sub:tuple[int,int,int],
                                  brightness:int)->tuple[int,int,int]:
    return tuple(expand5((b5(a,brightness)+b5(b,brightness))//2)
                 for a,b in zip(main,sub))


def native_half_then_output_brightness(main:tuple[int,int,int],
                                       sub:tuple[int,int,int],
                                       brightness:int)->tuple[int,int,int]:
    return tuple(expand5(b5((a+b)//2,brightness))
                 for a,b in zip(main,sub))


def analyze(cgram:bytes, prior:dict)->dict:
    if len(cgram)!=512 or hashlib.sha256(cgram).hexdigest()!=SOURCE_CGRAM_SHA:
        raise ValueError("unqualified independently original Snes9x finish CGRAM")
    proof=prior.get("proof",{})
    if (prior.get("schema")!=REPORT_SCHEMA
        or proof.get("number_of_original_source_pixels_with_that_colour_in_all_263_frames")!=2
        or proof.get("original_colour_global_positions")!=[[3792,121,165],[3872,121,165]]
        or proof.get("source_pixels_compared")!=15081472
        or proof.get("native_full_5484_guest_CRC_sha256")==False):
        # source script labels may be reproduced in a stale/altered report,
        # but the SHA-pinned original palette is a separate independent input.
        raise ValueError("unqualified rare original/native finish pixel receipt")
    original=prior.get("real_2014_original",{})
    native=prior.get("real_native_windows",{})
    if (original.get("whole_zip_sha256")!="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
        or native.get("exe_sha256")!="29431b073fd550e29b908f4e1d20fe9ee46b357b7a3e73b4fa21a224fa0dbf08"
        or native.get("full_5484_guest_CRC_sha256")!="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
        or any(s.get("original_RGB5_expanded")!=list(EXPECTED_REFERENCE_RGB8)
               or s.get("actual_windows_RGB8")!=list(EXPECTED_NATIVE_RGB8)
               for s in proof.get("finish_pixel_samples",[]))
        or len(proof.get("finish_pixel_samples",[]))!=2):
        raise ValueError("foreign original/native source or finish pixel colours")
    palette=[int.from_bytes(cgram[i:i+2],"little") for i in range(0,512,2)]
    if any(word>0x7fff for word in palette):
        raise ValueError("CGRAM has an invalid 16-bit high bit")
    options=[]
    for main in range(0,128):
        for obj in range(128,256):
            a,b=rgb5(palette[main]),rgb5(palette[obj])
            if (original_brightness_then_half(a,b,BRIGHTNESS)==EXPECTED_REFERENCE_RGB8
                and native_half_then_output_brightness(a,b,BRIGHTNESS)==EXPECTED_NATIVE_RGB8):
                options.append({
                    "candidate_BG_CGRAM_index":main,"candidate_OBJ_CGRAM_index":obj,
                    "historical_snapshot_BG_RGB5":[*a],"historical_snapshot_OBJ_RGB5":[*b],
                    "snapshot_BG_CGRAM_word":f"{palette[main]:04x}",
                    "snapshot_OBJ_CGRAM_word":f"{palette[obj]:04x}",
                    "original_emulator_pipeline_RGB8":[*EXPECTED_REFERENCE_RGB8],
                    "native_or_bsnes_pipeline_RGB8":[*EXPECTED_NATIVE_RGB8],
                })
    if tuple((r["candidate_BG_CGRAM_index"],r["candidate_OBJ_CGRAM_index"]) for r in options)!=EXPECTED_SOURCE_PAIRS:
        raise ValueError("pinned original CGRAM candidate enumeration changed")
    return {
        "schema":"qa08-source-pinned-prebrightness-postblend-finish-two-pixel-counterfactual/1",
        "original_cgram_snapshot_frame":3683,
        "original_cgram_sha256":SOURCE_CGRAM_SHA,
        "source_pixels_under_comparison_native_guests":[3792,3872],
        "source_original_reference_rgb5_expanded":[*EXPECTED_REFERENCE_RGB8],
        "source_actual_windows_rgb8":[*EXPECTED_NATIVE_RGB8],
        "assumed_INIDISP_brightness":BRIGHTNESS,
        "assumed_main_layer":"BG, CGRAM indices 0..127",
        "assumed_sub_layer":"OBJ, CGRAM indices 128..255",
        "assumed_colour_math":"half-add",
        "candidates_in_original_3683_palette":options,
        "candidate_index_pair_count":len(options),
        "original_CGRAM_preserved_to_guests_3792_and_3872_proven":False,
        "actual_native_main_and_sub_operand_at_both_pixels_proven":False,
        "original_same_scanline_PPU_priority_proven":False,
        "SNES_hardware_DAC_exactness_proven":False,
        "renderer_correction_authorized":False,
        "QA08_QA10_4x_widescreen_HD_art_release_accepted":False,
        "next_discriminator":"Read actual Windows native current PPU operands/CGADSUB/inidisp/OBJ palette at two exact pixels, then compare to original effective 2014 PPU ownership and independently implemented physical-style postblend model."
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("cgram","rare-report","out"):
        ap.add_argument("--"+name,required=True,type=Path)
    a=ap.parse_args()
    result=analyze(a.cgram.read_bytes(),json.loads(a.rare_report.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_FINISH_HALF_COLOR conditional_cgram=3683 candidates="+
          str(result["candidate_index_pair_count"])+" live_orig_owners=0 release=0")


if __name__=="__main__":
    main()
