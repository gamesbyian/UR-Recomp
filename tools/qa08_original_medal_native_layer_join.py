#!/usr/bin/env python3
"""QA-08 exact original/native two-player result medals: layer winners and OAM.

One 2014 Snes9x callback probe, one independent authentic original 263-frame
corpus, one real compiled Win32 same-process PPU/OAM source corpus. SHA-pinned
archive-only, no emulator process, guest edits, palette remap, tile patch,
pixel tolerance or frame search. Ten original/native corresponding pixels and
fourteen unique OAM slots only; remaining 296-pixel medal mask is independent.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
LIVE_WIN_ZIP="f467aaafc193e0b8e56934e6f505c10d60c3a4a1afa8727ffa376e5cdf7d53de"
ORIGINAL_MEDAL_ZIP="05c82ce0131594ce5f2a4e2de6a3d4328bc80e8eb599cda618ea32c1685c25c2"
GUEST_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
PAIRS=((4031,4032),(4175,4176))
PIXELS=((207,91),(205,115),(205,139),(225,96),(225,120))
SLOTS=(96,97,98,99,112,113,114)
EXPECTED_NAME_DELTA={96:2,97:2,98:0,99:0,112:-2,113:-2,114:-2}
ORIG_OWNER=(4,4,0,4,4)
NATIVE_OWNER=(0,4,4,4,4)
PAM=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"


def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def decode_original_mode3_main_depth(value:int,tm:int)->str:
    """Pinned Snes9x 2014 gfx.cpp: D32; OBJ p1 Z40, BG1 low D+7=39."""
    if (tm&0x11)!=0x11:
        raise ValueError("original BG1/OBJ main screen disabled")
    if value==40: return "OBJ priority1"
    if value==39: return "BG1 low priority"
    raise ValueError("unexpected original 2014 medal PPU main Z depth")


def original_rgb5(raw:bytes,x:int,y:int)->list[int]:
    if len(raw)!=256*224*4: raise ValueError("not full original 256x224 callback")
    idx=(y*256+x)*4
    blue,green,red,_=raw[idx:idx+4]
    q=green>>3
    return [red,(q<<3)|(q>>2),blue]


def assess(original_zip:Path,native_zip:Path,original_probe_zip:Path)->dict:
    expected=((original_zip,ORIGINAL_ZIP),(native_zip,LIVE_WIN_ZIP),
              (original_probe_zip,ORIGINAL_MEDAL_ZIP))
    if any(sha(p.read_bytes())!=digest for p,digest in expected):
        raise ValueError("forged/stale original/native medal source archive")
    with (zipfile.ZipFile(original_zip) as o,
          zipfile.ZipFile(native_zip) as w,
          zipfile.ZipFile(original_probe_zip) as p):
        om=json.loads(o.read("qa08-original-2p-fullroute.json"))
        nm=json.loads(w.read("qa08-windows-2p-fullroute.json"))
        native=json.loads(w.read("qa08-native-effective-pixel-owner.json"))
        original=json.loads(p.read("qa08-original-live-medal-pixels.json"))
        fresh=json.loads(p.read("new-original-2p-manifest.json"))
        if (om.get("actual_callbacks_captured")!=263 or
            fresh.get("actual_callbacks_captured")!=263 or
            fresh.get("each_authentic_callback")!=om.get("each_authentic_callback") or
            original.get("original_263_callback_images_exact_against_untouched_source") is not True or
            original.get("actual_original_video_callbacks")!=[4031,4175] or
            original.get("native_correctly_registered_guest_frames")!=[4032,4176] or
            original.get("observed_original_pixel_coordinates")!=[list(k) for k in PIXELS] or
            nm.get("actual_native_guest_CRC_sha256")!=GUEST_CRC or
            nm.get("actual_source_count")!=263 or
            native.get("independently_source_qualified_native_pixels")!=11 or
            native.get("independently_source_qualified_native_scanline_OAM_snapshots")!=70 or
            native.get("verified_same_actual_Windows_executable")!=nm.get("actual_windows_PE_sha256")):
            raise ValueError("source producer, 263-frame registry, or Win32 guest CRC drift")
        proof={i["real_original_snes9x_callback_frame"]:i for i in om["each_authentic_callback"]}
        orig_pix=original.get("original_pixels",[])
        orig_oam=original.get("original_oam_slots",[])
        live_pixels=native.get("native_real_PPU_resolved_pixels",[])
        live_oam=native.get("native_OAM_in_effect_on_selected_lines",[])
        if len(orig_pix)!=10 or len(orig_oam)!=14 or len(live_pixels)!=11 or len(live_oam)!=70:
            raise ValueError("incomplete bounded real source witness")
        joined=[];joined_oam=[]
        for idx,(cb,guest) in enumerate(PAIRS):
            raw=o.read(f"frames/frame_{cb:06d}_256x224.raw")
            if sha(raw)!=proof[cb]["original_unchanged_BGRX_sha256"]:
                raise ValueError("modified original screenshot on medal callback")
            p7=w.read(f"source/ur-baldosa-original-source-{guest:06d}.pam")
            if (not p7.startswith(PAM) or len(p7)!=len(PAM)+256*224*4 or
                sha(p7)!=nm["source_frame_P7_SHA256_by_guest"][str(guest)]):
                raise ValueError("modified real Windows P7 source frame")
            source=[x for x in orig_pix if int(x["callback"])==cb]
            same=[x for x in live_pixels if x["native_guest"]==guest]
            if len(source)!=5 or len(same)!=5:
                raise ValueError("missing five registered original/native medal pixels")
            so={(int(x["x"]),int(x["y"])):x for x in source}
            sn={(int(x["x"]),int(x["raster_y"])):x for x in same}
            if set(so)!=set(sn)!=set(PIXELS) or set(so)!=set(PIXELS) or len(so)!=5 or len(sn)!=5:
                raise ValueError("forged/duplicated original/native medal sample positions")
            for pi,(x,y) in enumerate(PIXELS):
                old,new=so[x,y],sn[x,y]
                zmain=int(old["main_depth"])
                if (int(old["cpu_frame"])!=cb or int(old["total_emulated"])!=guest or
                    int(old["brightness"])!=14 or old["CGADSUB"].lower()!="7f" or
                    int(old["bgmode"])!=3 or int(old["TM"],16)!=0x13 or
                    int(old["TS"],16)!=0x10 or
                    int(old["sub_depth"]) not in (1,40) or
                    zmain!=(39 if pi==2 else 40)):
                    raise ValueError("original source PPU medal priority/callback drift")
                old_owner=4 if zmain==40 else 0
                if old_owner!=ORIG_OWNER[pi] or new["resolved_main_layer"]!=NATIVE_OWNER[pi]:
                    raise ValueError("unexpected original/native medal winner classification")
                if (new["cgadsub"]!="7f" or new["inidisp"]!="0e" or
                    new["original_2014_snes9x_RGB5_expanded"]!=original_rgb5(raw,x,y)):
                    raise ValueError("authentic source RGB5, math or brightness drift")
                ix=(y*256+x)*4
                actual=list(p7[len(PAM)+ix:len(PAM)+ix+3])
                if new["native_rgb8_original_PPU"]!=actual:
                    raise ValueError("actual native source pixel contradicts layer witness")
                joined.append({
                    "original_callback":cb,"native_guest":guest,"xy":[x,y],
                    "original_2014_main_z":zmain,
                    "source_original_main_winner":decode_original_mode3_main_depth(
                        zmain,int(old["TM"],16)),
                    "real_Windows_main_winner":("BG1" if new["resolved_main_layer"]==0 else "OBJ"),
                    "source_original_main_z_vs_native_layer_equivalent":old_owner==new["resolved_main_layer"],
                    "actual_original_RGB5_expanded":original_rgb5(raw,x,y),
                    "actual_Windows_RGB8":actual,
                    "original_sub_z":int(old["sub_depth"]),
                    "native_sub_layer":new["resolved_sub_layer"],
                    "original_exact_observer_ppu_brightness":14,
                    "Windows_exact_observer_ppu_brightness":14,
                    "source_animation_or_CPU_instruction_phase_equivalence_proven":False
                })
            old_o={int(v["slot"]):v for v in orig_oam if int(v["callback"])==cb}
            native_o=[v for v in live_oam if v["native_guest"]==guest]
            if set(old_o)!=set(SLOTS) or len(native_o)!=35:
                raise ValueError("no seven authentically corresponding medal OAM slots")
            for slot in SLOTS:
                orig=old_o[slot]
                observed={v["native_scanline_oam_tile_attr"] for v in native_o if v["OAM_slot"]==slot}
                xy={v["native_scanline_oam_xy"] for v in native_o if v["OAM_slot"]==slot}
                if len(observed)!=1 or len(xy)!=1:
                    raise ValueError("native OAM tile data varies across five measured scanlines")
                attr=int(next(iter(observed)),16)
                tile=attr&0x1ff
                oldtile=int(orig["tile"],16)
                if ((tile-oldtile)!=EXPECTED_NAME_DELTA[slot] or
                    ((attr>>9)&7)!=int(orig["palette"]) or
                    ((attr>>12)&3)!=int(orig["priority"])):
                    raise ValueError("original/native sprite tile/priority/palette change unqualified")
                address=int(next(iter(xy)),16)
                if (address&255)!=(int(orig["x"])&255) or
                    (address>>8)!=(int(orig["y"])&255)):
                    raise ValueError("original/native medal sprite XY changed")
                joined_oam.append({
                    "original_callback":cb,"native_guest":guest,"slot":slot,
                    "original_Snes9x_tile":f"{oldtile:03x}",
                    "real_native_OAM_tile":f"{tile:03x}",
                    "native_minus_original_tile":tile-oldtile,
                    "source_original_and_native_sprite_xy_palette_priority_identical":True
                })
    changed=[x for x in joined if not x["source_original_main_z_vs_native_layer_equivalent"]]
    if len(changed)!=4 or [(x["native_guest"],x["xy"]) for x in changed]!=[
        (4032,[207,91]),(4032,[205,139]),(4176,[207,91]),(4176,[205,139])]:
        raise ValueError("live original/native result sprite priority disagreement changed")
    return {
        "schema":"qa08-independent-original-Snes9x-native-Win32-two-medal-effective-layers-and-OAM/1",
        "source_original_263_frame_archive_sha256":ORIGINAL_ZIP,
        "source_native_263_frame_archive_sha256":LIVE_WIN_ZIP,
        "source_original_new_PPU_depth_archive_sha256":ORIGINAL_MEDAL_ZIP,
        "full_guest_5484_CRC_sha256":GUEST_CRC,
        "actual_2014_original_video_callbacks":[4031,4175],
        "real_Windows_registered_guests":[4032,4176],
        "total_genuine_corresponding_source_pixels":len(joined),
        "number_of_original_native_main_layer_disagreements":len(changed),
        "two_distinct_coordinates_with_repeat_main_layer_disagreement":[[207,91],[205,139]],
        "source_original_native_pixel_winner_pairs":joined,
        "source_original_native_corresponding_OAM_slots":joined_oam,
        "OAM_slot_count_verified":14,
        "tile_index_delta_by_slot":{str(k):v for k,v in EXPECTED_NAME_DELTA.items()},
        "original_and_native_263_complete_source_image_hashes_checked":True,
        "authentic_original_effective_PPU_priority_for_selected_10_pixels_proven":True,
        "whole_296_pixel_mask_effective_priority_proven":False,
        "proven_root_cause_CPU_to_OAM_writer_phase":False,
        "proven_renderer_OCclusion_bug":False,
        "global_sprite_tile_plus_minus_two_patch_authorized":False,
        "source_frame_shift_or_palette_recolour_authorized":False,
        "QA08_QA10_physical_release_and_HDart_accepted":False,
        "next_discriminator":"source-qualify underlying authentic sprite tile words/VRAM writers and BG/window effective winners before attributing OAM delta to CPU phase versus renderer"
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original","native","original-medal","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    result=assess(a.original,a.native,a.original_medal)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_MEDAL_REAL_ORIGINAL_NATIVE owners=10 changed=4 matched_OAM=14 original_images=263 native_images=263 no_patch=1")


if __name__=="__main__":
    main()
