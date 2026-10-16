#!/usr/bin/env python3
"""QA-08: verify genuine 2P finish colour-math provenance across three archives.

Only archived original 2014 Snes9x, preceding validated Windows raster,
new same-process native PPU layer/OAM and independent original PPU palette.
No emulator, Win32 build, clocks, raster write, chosen frame shift or
hardware-accurate claim. The earlier half-add explanation is **refuted**
for this exact pixel because live CGADSUB=04 means full ADD, no halving.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
PREVIOUS_ZIP = "4f766de13c702a108279293df4613538d8b49cbd1ecbc0876533c5f01f09293c"
LIVE_ZIP = "f467aaafc193e0b8e56934e6f505c10d60c3a4a1afa8727ffa376e5cdf7d53de"
CG_SHA = "b7aca48a35b4152ea7ce9a17ed68a08c9eed1e583397508b197e29dc50f73067"
GUEST_CRC = "c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
LIVE_EXE = "4373e112e24e79c05dcaa4b2f8a9dcd7e2046337a2d27f4bf482d7bcca6d5a89"
ORIGINAL_RGB = (49,24,0)
NATIVE_RGB = (57,24,0)
MAIN = (13,0,0)
SUB = (1,7,1)
POST = (14,7,1)
FRAMES = (3792,3872)
W,H = 256,224
PAM_HEADER=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"


def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def brightness5(c:int, b:int)->int:
    if not 0<=c<=31 or not 0<=b<=15:
        raise ValueError("not SNES channel/brightness")
    return (c*b+7)//15


def expand5(x:int)->int:
    if not 0<=x<=31:
        raise ValueError("not RGB5")
    return (x<<3)|(x>>2)


def reference_palette_first_full_add(a:tuple[int,...],z:tuple[int,...],brightness:int)->tuple[int,...]:
    """Exact original 2014 palette-first *FULL* addition (not half)."""
    return tuple(expand5(min(31,brightness5(x,brightness)+brightness5(y,brightness)))
                 for x,y in zip(a,z))


def native_full_add_then_brightness(a:tuple[int,...],z:tuple[int,...],brightness:int)->tuple[int,...]:
    return tuple(expand5(brightness5(min(31,x+y),brightness)) for x,y in zip(a,z))


def validate_live(live:dict, original:dict, fresh:dict, old:dict, palette:bytes)->dict:
    if sha(palette)!=CG_SHA or len(palette)!=512:
        raise ValueError("not verified original 2014 finish CGRAM")
    if (original.get("schema")!="qa08-original-pinned-snes9x-authentic-2p-fullroute-raster/1"
        or original.get("actual_callbacks_captured")!=263
        or original.get("capture_selection")!=[1279,5471,16]):
        raise ValueError("not original 2014 unmasked source")
    if (fresh.get("schema")!="qa08-real-windows-2p-split-fullroute-source-20261015/1"
        or old.get("schema")!=fresh["schema"]
        or fresh.get("actual_native_guest_CRC_sha256")!=GUEST_CRC
        or old.get("actual_native_guest_CRC_sha256")!=GUEST_CRC
        or fresh.get("actual_native_simulations")!=old.get("actual_native_simulations") or
        fresh["actual_native_simulations"]!=5484
        or fresh.get("source_frame_P7_SHA256_by_guest")!=old.get("source_frame_P7_SHA256_by_guest")
        or fresh.get("actual_source_count")!=old.get("actual_source_count") or
        fresh["actual_source_count"]!=263
        or fresh.get("actual_windows_PE_sha256")!=LIVE_EXE
        or old.get("actual_windows_PE_sha256")==LIVE_EXE):
        raise ValueError("not one exact Win32 source/no-regression frame corpus")
    witnesses=live.get("bounded_two_finish_live_pixel_owners",{})
    rows=witnesses.get("read_only_native_live_PPU_effective_pixels",[])
    if (witnesses.get("schema")!="qa08-live-native-finishing-pixel-PPU-layer-observer/1"
        or len(rows)!=2
        or [p.get("native_guest") for p in rows]!=list(FRAMES)
        or live.get("independently_source_qualified_native_pixels")!=11
        or live.get("independently_source_qualified_native_scanline_OAM_snapshots")!=70
        or live.get("real_native_2p_guest_crc_sha256")!=GUEST_CRC
        or live.get("verified_same_actual_Windows_executable")!=LIVE_EXE):
        raise ValueError("native read-only PPU witness missing or foreign")
    palette_words=[int.from_bytes(palette[2*i:2*i+2],"little") for i in range(256)]
    def rgb5(w:int)->tuple[int,...]:
        return (w&31,(w>>5)&31,(w>>10)&31)
    if rgb5(palette_words[0x1b])!=MAIN or palette_words[0xc6]!=0x04e1 or rgb5(palette_words[0xc6])!=SUB:
        raise ValueError("original palette BG/OBJ snapshot not corresponding source")
    results=[]
    for p in rows:
        guest=p["native_guest"]
        if (p.get("original_video_callback")!=guest-1
            or (p.get("x"),p.get("y"))!=(121,165)
            or p.get("native_resolved_main_layer")!=2  # BG3
            or p.get("native_resolved_sub_layer")!=4    # OBJ
            or p.get("native_color_math_enabled")!=1
            or p.get("native_color_window_state")!=0
            or p.get("native_main_RGB5")!=list(MAIN)
            or p.get("native_sub_RGB5")!=list(SUB)
            or p.get("native_postmath_RGB5")!=list(POST)
            or p.get("native_actual_RGB8")!=list(NATIVE_RGB)
            or p.get("original_Snes9x_RGB5_expanded")!=list(ORIGINAL_RGB)
            or p.get("native_effective_obj_CGRAM_index")!="c6"
            or p.get("native_effective_obj_CGRAM_word")!="04e1"
            or p.get("cgadsub")!="04"
            or p.get("inidisp")!="07"
            or p.get("tm")!="17" or p.get("ts")!="10"
            or p.get("source_original_PPU_layers_proven") is not False):
            raise ValueError("on-raster native BG3/OBJ/add/brightness source does not match")
        b=int(p["inidisp"],16)&15
        flags=int(p["cgadsub"],16)
        if flags&0x80 or flags&0x40 or not (flags&0x04):
            raise ValueError("this is not SNES full-add BG3 colour math")
        if tuple(x+y for x,y in zip(MAIN,SUB))!=POST:
            raise ValueError("native post-math is not non-half addition")
        expected_source=reference_palette_first_full_add(MAIN,SUB,b)
        expected_native=native_full_add_then_brightness(MAIN,SUB,b)
        if expected_source!=ORIGINAL_RGB or expected_native!=NATIVE_RGB:
            raise ValueError("precise observed colours cannot be reconstructed")
        results.append({
            "native_guest":guest,"original_Snes9x_callback":guest-1,
            "source_pixel":[121,165],
            "native_main":"BG3","native_sub":"OBJ",
            "live_CGADSUB":p["cgadsub"],"live_INIDISP":p["inidisp"],
            "native_main_RGB5":list(MAIN),"native_sub_RGB5":list(SUB),
            "native_postmath_RGB5":list(POST),
            "reference_brightness_before_FULL_add_rgb8":list(expected_source),
            "native_FULL_add_before_output_brightness_rgb8":list(expected_native),
            "actual_reference_original_RGB8":list(ORIGINAL_RGB),
            "actual_compiled_Windows_RGB8":list(NATIVE_RGB),
            "genuine_ref_effective_BG3_OBJ_priority_proven":False,
            "source_backend_vs_physical_SNES_math_proven":False,
        })
    return {
        "schema":"qa08-genuine-windows-live-finish-BG3-OBJ-full-add-source-comparison/1",
        "status":"same_effective_native_BG3_OBJ_addition_both_frames_source_colours_exactly_reproduced",
        "original_2014_source_archive_sha256":ORIGINAL_ZIP,
        "previous_native_263_fullframe_archive_sha256":PREVIOUS_ZIP,
        "latest_native_263_fullframe_source_archive_sha256":LIVE_ZIP,
        "latest_native_PE_sha256":LIVE_EXE,
        "source_original_3683_CGRAM_sha256":CG_SHA,
        "source_original_palette_BG_index_1b_RGB5":list(MAIN),
        "source_original_palette_OBJ_index_c6_word":"04e1",
        "all_263_new_native_frame_hashes_equal_prior_source":True,
        "same_real_guest_CRC_5484":GUEST_CRC,
        "two_live_native_finish_pixels":results,
        "former_3683_snapshot_half_add_candidate_was_live_source_state":False,
        "formerly_assumed_half_colour_math_disproved_by_live_CGADSUB_04":True,
        "native_effective_Bg3_main_OBJ_sub_add_before_brightness_observed":True,
        "reference_original_effective_pixel_layers_observed":False,
        "original_emulator_DAC_hardware_equivalence_proven":False,
        "native_PPU_or_guest_modified_by_observer":False,
        "renderer_patch_authorized":False,
        "release_4x_342wide_HDart_QA08_10_accepted":False,
        "next_decision":"Original 2014 Snes9x effective BG3/OBJ pixel ownership or independent actual SNES output needed before a renderer change; preserve observed native full-add sequence."
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ("live","original","previous","palette","out"):
        ap.add_argument("--"+key,required=True,type=Path)
    a=ap.parse_args()
    def get(path:Path,expected_zip:str,manifest:str)->dict:
        if sha(path.read_bytes())!=expected_zip:
            raise ValueError("immutable source ZIP hash mismatch")
        with zipfile.ZipFile(path) as z:
            return json.loads(z.read(manifest))
    fresh=get(a.live,LIVE_ZIP,"qa08-windows-2p-fullroute.json")
    with zipfile.ZipFile(a.live) as z:
        live=json.loads(z.read("qa08-native-effective-pixel-owner.json"))
        for guest in FRAMES:
            p7=z.read(f"source/ur-baldosa-original-source-{guest:06d}.pam")
            if (not p7.startswith(PAM_HEADER) or len(p7)!=len(PAM_HEADER)+W*H*4 or
                sha(p7)!=fresh["source_frame_P7_SHA256_by_guest"][str(guest)]):
                raise ValueError("actual captured same-frame Windows P7 source image invalid")
    previous=get(a.previous,PREVIOUS_ZIP,"qa08-windows-2p-fullroute.json")
    orig=get(a.original,ORIGINAL_ZIP,"qa08-original-2p-fullroute.json")
    result=validate_live(live,orig,fresh,previous,a.palette.read_bytes())
    with zipfile.ZipFile(a.original) as z:
        manifest={v["real_original_snes9x_callback_frame"]:v for v in orig["each_authentic_callback"]}
        for guest in FRAMES:
            cb=guest-1
            raw=z.read(f"frames/frame_{cb:06d}_256x224.raw")
            if len(raw)!=W*H*4 or sha(raw)!=manifest[cb]["original_unchanged_BGRX_sha256"]:
                raise ValueError("original source callback missing or altered")
            p=(165*W+121)*4
            blue,green,red,_=raw[p:p+4]
            source=(red,((green>>3)<<3)|((green>>3)>>2),blue)
            if source!=ORIGINAL_RGB:
                raise ValueError("genuine original source pixel not RGB5 qualified")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_FINISH_FULL_ADD verified=2 live_BG3_OBJ=2 reference_pixels=2 native=2 old_half_theory=DISPROVEN release=0")


if __name__=="__main__":
    main()
