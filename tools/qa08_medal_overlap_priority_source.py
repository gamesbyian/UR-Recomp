#!/usr/bin/env python3
"""Independent seven-slot priority composition of authentic 2P medal pixels.

Counterfactual ONLY: original complete indexed VRAM and actual Win32 OAM
name and slot precedence, against source Win32 effective pixel observation.
Does not assume genuine Win32 current VRAM equals original. Actual Win32 live
VRAM readback is a separate graphics candidate/acceptance requirement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
try:
    from tools import qa08_medal_original_vram_native_oam_counterfactual as base
except ImportError:
    import qa08_medal_original_vram_native_oam_counterfactual as base

ROWS=((207,91,112,None),(205,115,113,None),(205,139,114,None),
      (225,96,97,99),(225,120,96,98))
EXPECTED=(0,4,6,14,14)
SOURCE_ORIGINAL_GOLD=(15,15)
NATIVE_GUESTS=(4032,4176)


def read_source(original:Path,native:Path,indexed:Path)->dict:
    # Verify immutable external producers before interpreting any source word.
    proof=base.verify(original,indexed,native)
    if proof["conditional_original_VRAM_matching_pairs"]!=6:
        raise ValueError("old source single-slot correction not reproduced")
    with zipfile.ZipFile(original) as z,zipfile.ZipFile(native) as w:
        samples=json.loads(w.read("qa08-native-effective-pixel-owner.json"))
        by_oam={(p["native_guest"],p["raster_y"],p["x"],p["OAM_slot"]):p
                for p in samples["native_OAM_in_effect_on_selected_lines"]}
        by_pixel={(p["native_guest"],p["raster_y"],p["x"]):p
                  for p in samples["native_real_PPU_resolved_pixels"]}
        if (len(by_oam)!=70 or len(by_pixel)!=11 or
            samples["independently_source_qualified_native_scanline_OAM_snapshots"]!=70):
            raise ValueError("native source PPU priority and OAM 70-slot registry drifted")
        observations=[]
        for cb,guest in base.PAIRS:
            prefix=f"registers/qa08_medal_{guest}"
            vram=z.read(prefix+".vram.bin")
            orig_oam=z.read(prefix+".oam.bin")
            regs=json.loads(z.read(prefix+".regs.json"))
            cfg=regs["ppu"]["obj"]
            if (len(vram)!=65536 or len(orig_oam)!=544 or
                regs["frame_tag"]!=guest or cfg["obsel"]!="63" or
                cfg["name_base"]!="C000" or cfg["name_select"]!="0000"):
                raise ValueError("original source VRAM/OBSEL/host label drifted")
            for i,(x,y,first,gold) in enumerate(ROWS):
                contenders=[first]+([gold] if gold is not None else [])
                result=[]
                for slot in contenders:
                    v=by_oam.get((guest,y,x,slot))
                    if v is None: raise ValueError("actual native OAM scanline sprite missing")
                    o0=int(v["native_scanline_oam_xy"],16)
                    o1=int(v["native_scanline_oam_tile_attr"],16)
                    native_name=o1&511
                    o=orig_oam[4*slot:4*slot+4]
                    original_name=o[2]|((o[3]&1)<<8)
                    if ((o0&255)!=o[0] or (o0>>8)!=o[1] or
                        (o1&0xfe00)!=((o[2]|o[3]<<8)&0xfe00)):
                        raise ValueError("original/native sprite XY flip priority palette changed")
                    col=x-o[0];row=(y-o[1])&255
                    if not (0<=col<16 and 0<=row<16):
                        raise ValueError("reported overlap is not inside source sprite rectangle")
                    idx=base.indexed(vram,native_name,0xc000,0,col,row,
                                     hf=bool(o1&0x4000),vf=bool(o1&0x8000))
                    old_idx=base.indexed(vram,original_name,0xc000,0,col,row,
                                         hf=bool(o1&0x4000),vf=bool(o1&0x8000))
                    result.append({
                      "oam_slot":slot,"original_name9":f"{original_name:03x}",
                      "real_native_name9":f"{native_name:03x}",
                      "source_original_4bit_index":old_idx,
                      "source_original_VRAM_at_native_name_index":idx,
                      "opaque_at_source_original_VRAM":bool(idx),
                    })
                # SNES OBJ: lower-numbered OAM wins if its nonzero source
                # pixel overlaps. Native PPU processes OAM in reverse and
                # lower slots overwrite higher (source ppu.c 2955-2975).
                predicted=next((t["source_original_VRAM_at_native_name_index"]
                                for t in result if t["opaque_at_source_original_VRAM"]),0)
                actual=by_pixel[(guest,y,x)]
                if (i==0 and actual["resolved_main_layer"]!=0 or
                    i!=0 and actual["resolved_main_layer"]!=4):
                    raise ValueError("native main BG1/OBJ owner is not original source comparison")
                actual_obj_idx=(int(actual["native_effective_OBJ_CGRAM_slot"],16)&15
                                if actual["resolved_main_layer"]==4 else 0)
                if predicted!=EXPECTED[i] or actual_obj_idx!=EXPECTED[i]:
                    raise ValueError("source OAM priority-index prediction mismatches compiled Windows")
                if gold is not None and (
                    result[0]["source_original_4bit_index"]!=0 or
                    result[1]["source_original_4bit_index"]!=15 or
                    result[0]["source_original_VRAM_at_native_name_index"]!=14 or
                    result[1]["source_original_VRAM_at_native_name_index"]!=15 or
                    result[0]["real_native_name9"]!="1ce"):
                    raise ValueError("gold overlapping OAM opaque source tile relationship changed")
                observations.append({
                  "original_callback":cb,"native_guest":guest,"xy":[x,y],
                  "source_original_VRAM_and_native_OAM_contenders_lower_slot_first":result,
                  "source_originalVRAM_with_native_OAM_priority_predicted_final_4bpp_index":predicted,
                  "actual_Win32_effective_OBJ_index_or_0_for_BG1":actual_obj_idx,
                  "actual_Win32_BG1_or_OBJ_main_layer":actual["resolved_main_layer"],
                  "counterfactual_equal_actual_Windows_source_RGB_index":True,
                  "native_VRAM_actual_content_equal_original_proven":False
                })
        if len(observations)!=10 or [
            v["source_originalVRAM_with_native_OAM_priority_predicted_final_4bpp_index"]
            for v in observations] != list(EXPECTED)*2:
            raise ValueError("not all ten independent medal positions source-explained")
        return {
          "schema":"qa08-2P-ten-medal-source-OAM-overlap-priority-counterfactual/1",
          "status":"10_of_10_RGB4_indices_conditionally_reproduced_with_originalVRAM_and_actual_nativeOAM",
          "source_actual_native_guest_frames":[4032,4176],
          "source_original_video_callbacks":[4031,4175],
          "actual_source_comparison_10_pairs":observations,
          "actual_native_observed_source_4bit_indices_all10":list(EXPECTED)*2,
          "conditional_original_VRAM_nativeOAM_priority_prediction_all10":list(EXPECTED)*2,
          "total_samples":10,"conditional_matches":10,
          "previous_single_selected_slot_only_matches":6,
          "four_gold_pixel_source_occlusion_now_conditionally_explained":True,
          "source_native_2p_frame_guest_CRC_unchanged":True,
          "full_original_source_14_OBJ_index_FNV_revalidated":True,
          "native_actual_live_guest_or_renderVram_content_verified":False,
          "native_renderer_writes_to_source_pixels":False,
          "actual_native_OAM_priority_and_sprite_overlaps_true_to_PPU_core_source":True,
          "actual_CPU_NMI_two_frame_OAM_writer_phase_proven":False,
          "normal_medal_all_296_pixel_source_priority_explained":False,
          "corrective_renderer_or_global_OAM_tile_patch_authorized":False,
          "QA08_QA10_release_and_HDart_visual_approval":False,
          "provenance_original_archive_sha256":base.PIN["registered"],
          "provenance_original_indexed14_archive_sha256":base.PIN["indexed"],
          "provenance_compiled_real_Windows_archive_sha256":base.PIN["native"]
        }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("original","native","indexed","out"):
        ap.add_argument("--"+name,required=True,type=Path)
    a=ap.parse_args()
    result=read_source(a.original,a.native,a.indexed)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_MEDAL_OVERLAP_10_OF_10 ORIGINAL_VRAM_NATIVE_OAM_PRIORITY=CONDITIONAL native_vram=UNKNOWN no_patch=1")


if __name__=="__main__":
    main()
