#!/usr/bin/env python3
"""Reject a final-RGB5-only palette fix using exact Snes9x/Win32 source."""
from __future__ import annotations
from collections import Counter
import argparse, json
from pathlib import Path
try:
    from tools.qa08_result_grey_phase_archive_check import loaded, PIXELS
except ImportError:
    from qa08_result_grey_phase_archive_check import loaded, PIXELS

def pixel(raw: bytes, index: int, original: bool) -> int:
    p=index*4
    if original:
        r,g,b=raw[p+2]>>3,raw[p+1]>>3,raw[p]>>3
    else:
        r,g,b=raw[p]>>3,raw[p+1]>>3,raw[p+2]>>3
    return (r<<10)|(g<<5)|b

def targets(original: bytes, native: bytes, native_colour: int)->Counter:
    if len(original)!=PIXELS*4 or len(native)!=PIXELS*4:
        raise ValueError("original or Windows raster cropped")
    return Counter(pixel(original,k,True) for k in range(PIXELS)
                   if pixel(native,k,False)==native_colour)

def diagnose(original: dict[int,bytes], native: dict[int,bytes])->dict:
    a,b=original[3680],native[3680]
    matches=targets(a,b,0x10c6)
    if matches!={0x10c6:1341,0x14e7:1737}:
        raise ValueError("authentic finish colour map source census drift")
    witness=[]
    for x,actual,reference in [(96,0x10c6,0x14e7),(97,0x10c6,0x10c6),
                               (92,0x1908,0x1d08),(93,0x1908,0x1908)]:
        o=pixel(a,x,True); n=pixel(b,x,False)
        if o!=reference or n!=actual:
            raise ValueError("authentic same-line neighbouring pixel drift")
        witness.append({"xy":[x,0],"native_RGB5":f"{n:04x}",
                        "original_RGB5":f"{o:04x}"})
    r=targets(original[4064],native[4064],0x4631)
    if r!={0x4631:79,0x5294:7900}:
        raise ValueError("real sampled result grey source census drift")
    if any(pixel(original[1856],k,True)!=pixel(native[1856],k,False)
           for k in range(PIXELS)):
        raise ValueError("known original/Win32 GO pixel exact control drift")
    return {
      "schema":"qa08-rf017-no-single-valued-finish-RGB5-only-LUT/1",
      "strict_263_original_and_native_source_SHA_authenticated":True,
      "authentic_control_1856_exact_RGB5_pixels":PIXELS,
      "source_finish_callback":3679,"native_finish_guest":3680,
      "native_colour_10c6_original_target_histogram":
          {f"{k:04x}":v for k,v in sorted(matches.items())},
      "adjacent_same_line_colour_contradictions":witness,
      "source_result_callback":4063,"native_result_guest":4064,
      "native_4631_original_targets":
          {f"{k:04x}":v for k,v in sorted(r.items())},
      "single_valued_native_RGB5_colour_LUT_per_scanline_possible":False,
      "layer_priority_window_or_field_source_cause_proven":False,
      "CPU_APU_PPU_game_or_output_modified":False,"QA08_QA10_release":False
    }


FINISH_FIELDS=range(3648,3873,16)
def rgb8_finish_transfer(original:dict[int,bytes],native:dict[int,bytes])->dict:
    """Exact source pixels; native RGB8 triplets vs original normalized RGB5.

    A successful observational transfer is NOT a valid engine patch or an
    approved postprocess. Inspect lost channel info before touching PPU math.
    """
    from collections import defaultdict
    joint=defaultdict(Counter)
    chan=[defaultdict(Counter) for _ in range(3)]
    wrong=0
    samples=0
    for frame in FINISH_FIELDS:
        a,b=original[frame],native[frame]
        if len(a)!=PIXELS*4 or len(b)!=PIXELS*4:
            raise ValueError("finish source raster cropped or absent")
        for off in range(0,PIXELS*4,4):
            reference=(a[off+2]>>3,a[off+1]>>3,a[off]>>3)
            source=(b[off],b[off+1],b[off+2])
            joint[source][reference]+=1
            for c in range(3):chan[c][source[c]][reference[c]]+=1
            wrong+=any((source[c]>>3)!=reference[c] for c in range(3))
            samples+=1
    conflicts={colour:dict(c) for colour,c in joint.items() if len(c)>1}
    if conflicts:
        raise ValueError("native full RGB8 triple is not source-deterministic")
    red_53=chan[0][53]
    if samples!=15*PIXELS or wrong!=90890 or len(joint)!=71 or (
       dict(red_53)!={6:2,7:23724} or
       any(len(c)!=1 for c in chan[1].values()) or
       any(len(c)!=1 for c in chan[2].values())):
        raise ValueError("pinned authentic full finish RGB8/source5 source census drift")
    if len([x for x in chan[0].values() if len(x)>1])!=1:
        raise ValueError("native red-channel source information ambiguity drift")
    return {
      "source_finish_native_guests":list(FINISH_FIELDS),
      "real_256x224_pixels_per_frame":PIXELS,
      "all_15_finish_true_source_pixels_examined":samples,
      "wrong_native_vs_original_RGB5":wrong,
      "unique_native_full_RGB8_colours":len(joint),
      "full_native_RGB8_triplet_multiple_original_RGB5_targets":0,
      "native_red_8bit_53_original_red5_split":
           {str(k):v for k,v in sorted(red_53.items())},
      "native_channel_RGB8_single_value_ambiguities":
           {colour:sum(len(v)>1 for v in mapping.values())
            for colour,mapping in zip(("red","green","blue"),chan)},
      "triplet_observational_transfer_authorized_as_PPU_fix":False,
      "physical_SNESC_DAC_or_2014_brightness_order_equivalent":False,
      "all_263_existing_source_frame_hashes_authenticated":True,
      "QA08_QA10_or_release_passed":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-bundle",type=Path,required=True)
    p.add_argument("--windows-source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    original,native=loaded(a.original_bundle,a.windows_source)
    report=diagnose(original,native)
    report["full_finish_RGB8_observed_transfer"]=rgb8_finish_transfer(original,native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("QA08_FINISH_PALETTE_LUT_IMPOSSIBLE",
          "source_frames=263 controls=57344 guest_changed=0 release=0")
if __name__=="__main__":main()
