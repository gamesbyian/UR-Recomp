#!/usr/bin/env python3
"""Decode source-backed medal OAM *candidates*, not final OBJ pixel ownership.

Two adjacent original Snes9x source-end OAM memories are independent from the
2014 Snes9x vs compiled Windows sparse 2P result raster producer archives.
All three complete ZIPs and per-image hashes must match literal source bytes.
Identified OAM rectangles only nominate scanline source pixels for an original/
native per-line OBJ-priority/colour-math probe. Never apply a sprite fix here.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import zipfile
try:
    from tools import qa08_verify_full_raster_residual_partition as core
except ImportError:
    import qa08_verify_full_raster_residual_partition as core

OAM_ZIP="d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8"
OAM_SHA={
    5183:"a9384c981763b175c9286fc06cd49f5cc183a5fdd6fd5f7920819f3d1300b5df",
    5184:"0107b6bde5aa41a234dc99fd24f9fae3de4ff718d757994bfbee996c88b6ff33",
}
SLOTS=(96,97,98,99,112,113,114)
MEDAL_SLOTS=(112,113,114)
SIDE_SLOTS=(96,97,98,99)
RECT_SIZE=16
EXPECTED_MASK="8b83bed21e2ff70ca279f993f4256e1edd64ad8f1edb657ee87554527e0594be"


def decode(data:bytes,index:int)->dict:
    if len(data)!=544 or not 0<=index<128:
        raise ValueError("original OAM must be exactly 512+32 bytes; slot 0..127")
    xlow,y,tile,attributes=data[4*index:4*index+4]
    hi=(data[512+(index//4)] >> ((index%4)*2))&3
    x=xlow+(256 if hi&1 else 0)
    if x>=256:
        x-=512
    return {
       "slot":index,"x_signed9":x,"y_mod256":y,"tile":tile,
       "attr":f"{attributes:02x}",
       "OBJ_palette":(attributes>>1)&7,
       "OBJ_priority":(attributes>>4)&3,
       "large_sprite_bit":(hi>>1)&1,
    }


def candidate_contains(sprite:dict,x:int,y:int)->bool:
    # OBSEL source size_select 3 and zero large-size bits: 16x16 slots.
    return (sprite["x_signed9"]<=x<sprite["x_signed9"]+RECT_SIZE
        and ((y-sprite["y_mod256"])&255)<RECT_SIZE)


def inspect(oam_archive:Path,original_archive:Path,windows_archive:Path)->dict:
    core.check(core.sha(oam_archive.read_bytes()),OAM_ZIP,"genuine original OAM source ZIP")
    cfg=core.PINS["twoplayer"]
    core.check(core.sha(original_archive.read_bytes()),cfg["original"],"original full 2P ZIP")
    core.check(core.sha(windows_archive.read_bytes()),cfg["windows"],"actual Windows full 2P ZIP")
    memories={}
    with zipfile.ZipFile(oam_archive) as z:
        if len(z.namelist())!=len(set(z.namelist())):
            raise ValueError("duplicate original Snes9x OAM archive names")
        for frame,name in ((5183,"qa08_results_previous"),(5184,"qa08_results_cgram")):
            info=json.loads(z.read(f"registers/{name}.info.json"))
            core.check(info["frame"],frame,"original OAM snapshot field number")
            mem=z.read(f"registers/{name}.oam.bin")
            core.check(core.sha(mem),OAM_SHA[frame],"original 544-byte OAM identity")
            memories[frame]=mem
        regs=json.loads(z.read("registers/qa08_results_cgram.regs.json"))
        core.check(regs["ppu"]["obj"]["size_select"],3,"source OBJ size selection")
        core.check(regs["ppu"]["obj"]["first_sprite"],0,"source OAM first sprite")
    slots={i:decode(memories[5184],i) for i in SLOTS}
    for i in SLOTS:
        core.check(decode(memories[5183],i),slots[i],
                   f"original 5183/5184 stable effective candidate bytes slot {i}")
        core.check(slots[i]["large_sprite_bit"],0,f"16x16 candidate slot {i}")
        core.check(slots[i]["OBJ_priority"],1,f"palette-specific priority slot {i}")
    for i,y,palette in ((112,91,5),(113,115,6),(114,139,7)):
        core.check((slots[i]["x_signed9"],slots[i]["y_mod256"],slots[i]["OBJ_palette"]),
                   (200,y,palette),f"medal source OAM {i}")
    for i,y in ((96,112),(97,88),(98,112),(99,88)):
        core.check((slots[i]["x_signed9"],slots[i]["y_mod256"],slots[i]["OBJ_palette"]),
                   (219,y,5),f"adjacent source OAM {i}")
    with zipfile.ZipFile(original_archive) as orig,zipfile.ZipFile(windows_archive) as win:
        orig_manifest=json.loads(orig.read(cfg["orig_json"]))
        native_manifest=json.loads(win.read(cfg["win_json"]))
        core.check(orig_manifest["unaltered_USA_ROM_sha256"],core.USA,"source original USA ROM")
        core.check(native_manifest["original_USA_ROM_sha256"],core.USA,"source native USA ROM")
        src_ids={int(row["real_original_snes9x_callback_frame"]):
                 row["original_unchanged_BGRX_sha256"]
                 for row in orig_manifest["each_authentic_callback"]}
        nat_ids=native_manifest["source_frame_P7_SHA256_by_guest"]
        result=[]
        for guest in core.MEDALS:
            callback=guest-1
            raw=orig.read(f"frames/frame_{callback:06d}_256x224.raw")
            p7=win.read(f"source/ur-baldosa-original-source-{guest:06d}.pam")
            core.check(core.sha(raw),src_ids.get(callback),f"original pixel {callback}")
            core.check(core.sha(p7),nat_ids.get(str(guest)),f"native pixel {guest}")
            if not p7.startswith(core.HEADER) or len(p7)!=len(core.HEADER)+core.PX*4:
                raise ValueError(f"native source {guest} cropped or corrupt")
            measured=core.compare(raw,p7[len(core.HEADER):])
            core.check(measured["wrong"],296,f"complete medal raster {guest}")
            core.check(core.sha(measured["mask"]),EXPECTED_MASK,f"pixel mask {guest}")
            counts=Counter()
            for index,pixel in enumerate(measured["mask"]):
                if not pixel:
                    continue
                x,y=index%core.W,index//core.W
                match_a=[i for i in MEDAL_SLOTS if candidate_contains(slots[i],x,y)]
                match_b=[i for i in SIDE_SLOTS if candidate_contains(slots[i],x,y)]
                if bool(match_a)==bool(match_b):
                    raise ValueError("wrong pixel outside/disputed source OAM rectangle")
                counts["medal" if match_a else "adjacent"]+=1
            core.check(dict(counts),{"medal":278,"adjacent":18},
                       f"two source OAM rectangle groups {guest}")
            result.append({"native_guest":guest,"original_callback":callback,
                           "wrong_RGB5_pixels":296,"medal_rectangle_pixels":278,
                           "adjacent_sprite_rectangle_pixels":18})
    return {
       "schema":"qa08-original-oam-static-candidates-to-real-2p-raster/1",
       "source_original_OAM_archive_SHA256":OAM_ZIP,
       "original_OAM_memory_SHA256_by_field":{str(k):v for k,v in OAM_SHA.items()},
       "original_native_2p_source_archive_sha256":{
            "original":cfg["original"],"Windows":cfg["windows"]},
       "original_OAM_fields":[5183,5184],
       "pixel_source_original_callbacks_precommitted_f_minus_one":True,
       "pixel_geometry":[core.W,core.H],
       "original_OBJ_size_select":3,"nominal_small_obj_size":[16,16],
       "actual_original_snapshot_slot_candidates":[slots[i] for i in SLOTS],
       "distinct_source_result_raster_frames_verified":len(result),
       "each_frame_pixels_by_nominal_OAM_rectangles":{
           "source_medal_slots_112_114":278,"adjacent_slots_96_99":18,
           "total_bad_pixels":296},
       "result_medal_mismatch_mask_SHA256":EXPECTED_MASK,
       "per_frame_source_qualified_counts":result,
       "original_5184_and_native_4032_same_CPU_or_PPU_frame_phase_proven":False,
       "snapshot_rectangle_implies_effective_scanline_OBJ_owner":False,
       "source_palette_priority_arithmetic_corrected_or_admitted":False,
       "original_vs_native_sampled_raster_release_accepted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for label in ("original-oam","original-2p","windows-2p","out"):
        p.add_argument("--"+label,required=True,type=Path)
    a=p.parse_args()
    report=inspect(a.original_oam,a.original_2p,a.windows_2p)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_SNES_OAM_CANDIDATE original_source_2=1 true_frames=21 "
          "medal_278=1 adjacent_18=1 ownership_admitted=0")


if __name__=="__main__":
    main()
