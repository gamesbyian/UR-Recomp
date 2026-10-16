#!/usr/bin/env python3
"""Adjudicate 2P results grayscale by authentic original/native raw RGB5 sources.

Three immutable historical, complete per-archive SHA-bound sources: original
2014 Snes9x 263 full frame BGRX callbacks, compiled real Windows Uniracers
263 full frame P7 RGBA callbacks, and exact 112-frame original PPU port journal.
No palette recolouring, no frame shifting, cropping, hiding, interpolation,
new emulator execution, CPU changes, or inferred release acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
WINDOWS_ZIP="f01ab5a4888c227f306a0b9cd89e67710a4b41cad4c22867072280a17811fa82"
SOURCE_PPU_ZIP="d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8"
WINDOWS_EXE="8c5b05e382d41e3226e6d975e23ec4aee4b7dd7b8b497dfd2efd7c59eae0e33d"
GUEST_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
ORIG_CGRAM="e8cdbe60"
NEXT_CGRAM="898ece20"
SCHEMA="qa08-actual-2P-original-native-phase-registered-raw-gray-pixel-classifier/1"
GUEST_FRAMES=range(1280,5473,16)
ANOMALY_FRAMES=list(range(4064,5409,112))
P7=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
GEOMETRY_BYTES=256*224*4
GRAY_ROTATION={(123,132),(132,140),(140,165),(165,123)}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def validate_archive(path:Path,expected:str)->zipfile.ZipFile:
    if sha(path.read_bytes())!=expected:
        raise ValueError("archive ZIP identity differs from authentic source")
    return zipfile.ZipFile(path)

def tally(source:bytes,native:bytes)->dict:
    if len(source)!=GEOMETRY_BYTES or len(native)!=GEOMETRY_BYTES:
        raise ValueError("only full 256x224 unmasked 4-channel images admissible")
    bad=Counter()
    first_other=None
    for i in range(0,GEOMETRY_BYTES,4):
        b,g,r=source[i:i+3]
        green5=g>>3
        green=(green5<<3)|(green5>>2)
        rn,gn,bn=native[i:i+3]
        if (r,green,b)==(rn,gn,bn):
            continue
        if r==green==b and rn==gn==bn and (rn,r) in GRAY_ROTATION:
            bad[(rn,r)]+=1
        else:
            bad["other"]+=1
            if first_other is None:
                first_other=[(i//4)%256,(i//4)//256]
    return {
        "total_wrong_RGB5_pixels":sum(bad.values()),
        "four_state_gray_rotation_wrong_pixels":sum(bad[x] for x in GRAY_ROTATION),
        "outside_four_state_rotation_wrong_pixels":bad["other"],
        "gray_rotation_counts":{f"{a}->{b}":bad[(a,b)] for a,b in sorted(GRAY_ROTATION)},
        "first_remaining_other_pixel":first_other,
    }

def classify(original:zipfile.ZipFile,native:zipfile.ZipFile,ppu:zipfile.ZipFile)->dict:
    om=json.loads(original.read("qa08-original-2p-fullroute.json"))
    nm=json.loads(native.read("qa08-windows-2p-fullroute.json"))
    source=json.loads(ppu.read("qa08-results-port-preceding-frame.json"))
    if (om["actual_callbacks_captured"]!=263 or
        om["actual_script_quit_frame"]!=5484 or
        om["native_unmasked_geometry"]!=[256,224] or
        nm["actual_source_count"]!=263 or nm["source_geometry"]!=[256,224] or
        nm["actual_windows_PE_sha256"]!=WINDOWS_EXE or
        nm["actual_native_guest_CRC_sha256"]!=GUEST_CRC or
        nm["actual_native_simulations"]!=5484 or
        source["263_original_unmasked_BGRX_frames_identical_to_prior_original"] is not True or
        source["source_5184_cgram_fnv1a"]!=ORIG_CGRAM or
        source["source_prior_112_frame_CGRAM_write_history"]["source_port_write_count"]!=192):
        raise ValueError("original/native independently qualified frame or guest sources missing")
    originals={r["real_original_snes9x_callback_frame"]:r["original_unchanged_BGRX_sha256"]
               for r in om["each_authentic_callback"]}
    native_hashes=nm["source_frame_P7_SHA256_by_guest"]
    for f in GUEST_FRAMES:
        o=original.read(f"frames/frame_{f-1:06d}_256x224.raw")
        w=native.read(f"source/ur-baldosa-original-source-{f:06d}.pam")
        if (len(o)!=GEOMETRY_BYTES or sha(o)!=originals[f-1] or
            not w.startswith(P7) or len(w)!=len(P7)+GEOMETRY_BYTES or
            sha(w)!=native_hashes[str(f)]):
            raise ValueError(f"original or native source image drift at guest {f}")
    native_registers=nm["read_only_native_PPU_registers"]["per_line_native_PPU_state"]
    observed={}
    for row in native_registers:
        f=row["actual_native_snes_frame"]
        if 5170<=f<=5190:
            observed.setdefault(f,{})[row["ppu_line"]]=row
    if (any(set(observed[f])!={1,112,114} for f in range(5170,5191))
        or len({observed[5184][y]["cgram_full_512_byte_FNV1a"] for y in (1,112,114)})!=1):
        raise ValueError("real native PPU state lacks three same-frame line samples")
    slots=lambda frame:observed[frame][1]["real_native_CGRAM_slots_6c_to_6f"]
    before=slots(5183)
    after=slots(5184)
    if (observed[5183][1]["cgram_full_512_byte_FNV1a"]!=ORIG_CGRAM or
        observed[5184][1]["cgram_full_512_byte_FNV1a"]!=NEXT_CGRAM or
        before!={"6c":"56b5","6d":"4a52","6e":"4631","6f":"4210"} or
        after!={"6c":"4a52","6d":"4631","6e":"4210","6f":"56b5"}):
        raise ValueError("native raw CGRAM four-slot transition contradicts source history")
    samples=[]
    for frame in ANOMALY_FRAMES:
        o=original.read(f"frames/frame_{frame-1:06d}_256x224.raw")
        n=native.read(f"source/ur-baldosa-original-source-{frame:06d}.pam")[len(P7):]
        samples.append({"native_guest_frame":frame,
                        "original_video_callback":frame-1,
                        **tally(o,n)})
    gray=sum(x["four_state_gray_rotation_wrong_pixels"] for x in samples)
    other=sum(x["outside_four_state_rotation_wrong_pixels"] for x in samples)
    if (gray,other)!=(318775,1184):
        raise ValueError(f"actual raw grayscale rotation witness changed: {gray}+{other}")
    return {
        "schema":SCHEMA,
        "status":"real_windows_four_slot_one_frame_phase_advanced_pixel_impact_measured",
        "original_source_archive_zip_sha256":ORIGINAL_ZIP,
        "real_windows_archive_zip_sha256":WINDOWS_ZIP,
        "original_112_frame_ppu_archive_zip_sha256":SOURCE_PPU_ZIP,
        "actual_windows_executable_sha256":WINDOWS_EXE,
        "actual_Windows_2P_guest_CRC_SHA256":GUEST_CRC,
        "actual_original_callbacks_validated":263,
        "actual_native_callbacks_validated":263,
        "full_unmasked_original_native_source_geometry":[256,224],
        "source_callback_to_windows_frame":"original callback=Windows guest minus one, no temporal search",
        "source_original_PPU_CGRAM_5183_5184":"e8cdbe60",
        "actual_native_PPU_CGRAM_5183":"e8cdbe60",
        "actual_native_PPU_CGRAM_5184":"898ece20",
        "native_15bit_palette_words_before":before,
        "native_15bit_palette_words_after":after,
        "original_last_actual_palette_write_frame":5178,
        "native_observed_palette_state_change_frame":5184,
        "original_source_palette_cycle_length_frames":28,
        "native_source_phase_offset_hypothesis":"native visible palette next cycle state by 5184; exact data-port writer phase still unverified",
        "sampling_interval_frames":16,
        "repeated_mismatch_interval_frames":112,
        "native_source_sampled_results_gray_mismatch_frames":ANOMALY_FRAMES,
        "source_rgb5_rotation_mismatch_pixels":gray,
        "source_rgb5_non_rotation_mismatch_pixels_in_those_frames":other,
        "total_2P_wrong_RGB5_pixels_in_accepted_full_263_frame_baseline":385373,
        "fraction_of_full_baseline_errors_explained_by_grayscale_rotation":gray/385373,
        "authentic_source_results_rgb5_mismatch_breakdown":samples,
        "native_actual_data_port_CPU_DMA_writer_phase_verified":False,
        "guest_clock_CPU_APU_changes_admitted":False,
        "raster_or_palette_fix_admitted":False,
        "QA08_10_and_release_gate_admitted":False,
        "HD_racer_aesthetic_approval":False,
    }

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-archive",required=True,type=Path)
    p.add_argument("--windows-archive",required=True,type=Path)
    p.add_argument("--original-ppu-archive",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    with validate_archive(a.original_archive,ORIGINAL_ZIP) as o, \
         validate_archive(a.windows_archive,WINDOWS_ZIP) as w, \
         validate_archive(a.original_ppu_archive,SOURCE_PPU_ZIP) as ppu:
        receipt=classify(o,w,ppu)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("QA08_REAL_WINDOWS_RAW_CGRAM_PHASE exact_2P=203/263",
          "gray_mismatch_pixels=318775", "writer_timing=unverified", "release=0")

if __name__=="__main__":
    main()
