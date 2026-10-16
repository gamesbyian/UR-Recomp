#!/usr/bin/env python3
"""QA-08: independently decode pinned original 2014 finish PPU BG/OBJ depths.

Three unmodified archived sources are required: original Snes9x 263-frame
images, one original-only read-only Snes9x callback/depth snapshot, and
independent real Windows main/sub colour-math verification. The original
Snes9x Mode 1 depth arithmetic is pinned to its actual gfx.cpp, not to the
native Baldosa enum. No game, emulator, source picture, or renderer is run,
patched, masked, shifted, cropped or recoloured here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

WIDTH,HEIGHT=256,224
CORPUS_SHA="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
ORIGINAL_PROBE_SHA="02a3237db4af8d11341ef18c7b4be51838f9fd18b6bad9875daa42c7b5bf9f32"
LIVE_FULL_ADD_SHA="4ef58031129c1b48d9bded18c661ef6286f4a0fdf3b2cd24b140b2b9fee4c444"
GUESTS=(3792,3872)
CALLBACKS=(3791,3871)
ORIGINAL_RGB=(49,24,0)
NATIVE_RGB=(57,24,0)
WIN32_PE="4373e112e24e79c05dcaa4b2f8a9dcd7e2046337a2d27f4bf482d7bcca6d5a89"


def decode_mode1_depth(row:dict)->dict:
    if any(row.get(k) is None for k in (
        "callback","cpu_frame","total_emulated","x","y","RGB565",
        "main_depth","sub_depth","sub_RGB565","bgmode",
        "brightness","blank","TM","TS","CGWSEL","CGADSUB",
        "CGRAM_1B","CGRAM_C6","width","height")):
        raise ValueError("incomplete original 2014 Snes9x pixel-depth witness")
    cb=int(row["callback"])
    if (cb not in CALLBACKS or int(row["cpu_frame"])!=cb or
        int(row["total_emulated"])!=cb+1 or
        (int(row["x"]),int(row["y"]))!=(121,165) or
        (int(row["width"]),int(row["height"]))!=(WIDTH,HEIGHT) or
        int(row["bgmode"])!=1 or int(row["brightness"])!=7 or
        int(row["blank"])!=0 or row["RGB565"].lower()!="30c0" or
        row["sub_RGB565"].lower()!="00c0" or
        row["TM"].lower()!="17" or row["TS"].lower()!="10" or
        row["CGWSEL"].lower()!="02" or row["CGADSUB"].lower()!="04" or
        row["CGRAM_1B"].lower()!="000d" or
        row["CGRAM_C6"].lower()!="04e1"):
        raise ValueError("original effective framebuffer/PPU source not authenticated")
    # Pinned original gfx.cpp RenderScreen(!sub) selects D=32 and BG3
    # Mode 1 high priority Z=D+17 =>49. Other main candidates cannot
    # yield this Z (BG1 high47, BG2 high46, OBJ priority3 at most48).
    main_z=int(row["main_depth"])
    main_D=32
    high_BG3_z=main_D+17
    if main_z!=high_BG3_z or not (int(row["TM"],16)&0x04):
        raise ValueError("not original 2014 high-priority main BG3")
    # Original RenderScreen(sub) derives D=(CGWSEL&2)<<4.
    # DrawOBJS(D+4) gives sprite Z2=D+4+priority*4; TS=0x10 only
    # enables OBJ on subscreen, so this is an unambiguous live winner.
    sub_D=(int(row["CGWSEL"],16)&2)<<4
    sub_z=int(row["sub_depth"])
    if not int(row["TS"],16)==0x10 or not (sub_z>=sub_D+4 and (sub_z-sub_D-4)%4==0):
        raise ValueError("not original subscreen OBJ geometry/depth")
    obj_priority=(sub_z-sub_D-4)//4
    if obj_priority!=2:
        raise ValueError("original sprite is not source depth priority 2")
    return {
        "original_video_callback":cb,"native_registered_guest":cb+1,
        "actual_original_source_xy":[121,165],
        "original_2014_final_packed_RGB565":"30c0",
        "original_2014_raw_screen_8bit_RGB":[*ORIGINAL_RGB],
        "main_layer":"BG3","main_bg3_high_priority":True,
        "main_depth":main_z,"sub_layer":"OBJ",
        "sub_obj_priority":obj_priority,"sub_depth":sub_z,
        "subscreen_packed_RGB565":"00c0",
        "original_CGRAM_BG3_index_1b":"000d",
        "original_CGRAM_OBJ_index_c6":"04e1",
        "original_full_add_CGADSUB_hex":"04",
        "brightness_7_of_15":True,
    }


def check_archives(original_zip:Path,original_probe_zip:Path,
                   native_verdict_zip:Path)->dict:
    def archive(path:Path,want:str)->zipfile.ZipFile:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=want:
            raise ValueError("authentic source ZIP identity changed")
        return zipfile.ZipFile(path)
    with archive(original_zip,CORPUS_SHA) as original, archive(original_probe_zip,ORIGINAL_PROBE_SHA) as probe, archive(native_verdict_zip,LIVE_FULL_ADD_SHA) as native:
        o=json.loads(original.read("qa08-original-2p-fullroute.json"))
        p=json.loads(probe.read("new-original-2p-manifest.json"))
        a=json.loads(probe.read("original-finish-source-layers.json"))
        n=json.loads(native.read("full-add-verdict.json"))
        if (o.get("schema")!="qa08-original-pinned-snes9x-authentic-2p-fullroute-raster/1"
            or p.get("schema")!=o["schema"]
            or o.get("capture_selection")!=[1279,5471,16]
            or p.get("capture_selection")!=o["capture_selection"]
            or o.get("actual_callbacks_captured")!=p.get("actual_callbacks_captured")
            or o["actual_callbacks_captured"]!=263):
            raise ValueError("original source image manifest does not match immutable baseline")
        old=o["each_authentic_callback"]
        new=p["each_authentic_callback"]
        if len(old)!=len(new) or old!=new:
            raise ValueError("original 263 post-PPU image hashes changed or frame order shifted")
        if (a.get("schema")!="qa08-original-2014-snes9x-two-pixel-real-ppu-buffer-owners/1"
            or a.get("original_rebuilt_exact_pinned_libretro_source_fully_same_263_images") is not True
            or a.get("actual_original_video_callbacks")!=list(CALLBACKS)
            or a.get("renderer_or_game_state_modified_by_observer") is not False):
            raise ValueError("not independently reproduced original Snes9x callback owners")
        decoded=[decode_mode1_depth(row) for row in a["original_source_PPU_buffer_observations"]]
        if [d["original_video_callback"] for d in decoded]!=list(CALLBACKS):
            raise ValueError("original on-pixel depth callbacks duplicate or absent")
        manifest={v["real_original_snes9x_callback_frame"]:v for v in old}
        for cb in CALLBACKS:
            raw=original.read(f"frames/frame_{cb:06d}_256x224.raw")
            if len(raw)!=WIDTH*HEIGHT*4 or hashlib.sha256(raw).hexdigest()!=manifest[cb]["original_unchanged_BGRX_sha256"]:
                raise ValueError("original per-pixel frame SHA invalid")
            blue,green,red,_=raw[(165*WIDTH+121)*4:(165*WIDTH+122)*4]
            if (red,((green>>3)<<3)|((green>>3)>>2),blue)!=ORIGINAL_RGB:
                raise ValueError("actual original source colour changed")
        if (n.get("schema")!="qa08-genuine-windows-live-finish-BG3-OBJ-full-add-source-comparison/1"
            or n.get("status")!="same_effective_native_BG3_OBJ_addition_both_frames_source_colours_exactly_reproduced"
            or n.get("latest_native_PE_sha256")!=WIN32_PE
            or n.get("all_263_new_native_frame_hashes_equal_prior_source") is not True
            or len(n.get("two_live_native_finish_pixels",[]))!=2
            or [r["native_guest"] for r in n["two_live_native_finish_pixels"]]!=list(GUESTS)):
            raise ValueError("not independently source-qualified new Win32 layer witnesses")
        for d,pixel in zip(decoded,n["two_live_native_finish_pixels"]):
            if (d["native_registered_guest"]!=pixel["native_guest"] or
                pixel["native_main"]!="BG3" or pixel["native_sub"]!="OBJ" or
                pixel["native_main_RGB5"]!=[13,0,0] or pixel["native_sub_RGB5"]!=[1,7,1] or
                pixel["native_postmath_RGB5"]!=[14,7,1] or
                pixel["live_CGADSUB"]!="04" or pixel["live_INIDISP"]!="07" or
                pixel["actual_compiled_Windows_RGB8"]!=list(NATIVE_RGB) or
                pixel["actual_reference_original_RGB8"]!=list(ORIGINAL_RGB)):
                raise ValueError("source original and Win32 live on-pixel owners conflict")
    return {
        "schema":"qa08-original-2014-and-live-native-finish-BG3-OBJ-full-add-direct-corroboration/1",
        "status":"original_and_native_two_exact_finish_BG3_OBJ_full_add_winners_independently_decoded",
        "original_2014_Snes9x_unmodified_263_frames":263,
        "original_original_2014_all_263_PPU_images_byte_hash_identical":True,
        "original_source_PPU_callback_registered_native_guest_minus_one":True,
        "source_pixel_xy":[121,165],
        "original_Snes9x_mode1_main_BG3_high_priority_sub_OBJ_priority2":True,
        "source_original_and_native_same_effective_local_layer_labels":True,
        "source_original_and_native_same_CGRAM_1b_C6_words":True,
        "source_original_and_native_same_full_ADD_brightness7":True,
        "source_original_packed_RGB565":"30c0",
        "strict_original_RGB8":[*ORIGINAL_RGB],"strict_native_RGB8":[*NATIVE_RGB],
        "two_authenticated_original_and_native_effective_pixels":decoded,
        "former_half_add_original_source_hypothesis_refuted":True,
        "historical_Snes9x_vs_native_brightness_order_isolated_here":True,
        "source_raster_original_vs_Windows_RGB5_mismatches_still_two":True,
        "actual_physical_SNES_DAC_stage_and_pixel_output_proven":False,
        "original_and_native_guest_instruction_NMI_timing_equivalence_proven":False,
        "full_2P_transition_and_result_sprite_source_accepted":False,
        "renderer_pixel_patch_authorized":False,
        "QA08_QA10_physical_7to6_4x_342wide_HD_art_release_credit":False,
        "original_source_zip_sha256":CORPUS_SHA,
        "original_readonly_depth_probe_zip_sha256":ORIGINAL_PROBE_SHA,
        "Windows_fulladd_source_verdict_zip_sha256":LIVE_FULL_ADD_SHA,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("original","original-probe","native-verdict","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    result=check_archives(a.original,a.original_probe,a.native_verdict)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_BOTH_PPU_SOURCE_OWNERS original_BG3_OBJ=2 native_BG3_OBJ=2 original_images_unchanged=263 physical=UNPROVEN renderer_fix=FORBIDDEN")


if __name__=="__main__":
    main()
