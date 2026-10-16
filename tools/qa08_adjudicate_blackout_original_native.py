#!/usr/bin/env python3
"""Source-authentic real original/native 2P blackout RGB5 exact regression.

Read only three SHA-pinned historical archives: original Snes9x 263 BGRX
source callbacks, read-only original $2100 blackout journal, and actual
Windows source P7+INIDISP witness. No temporal search, 216-high crop,
screen mask, guest edit, brightness remap or renderer fabrication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
BLACKOUT_ZIP="8d7b3a65b8b40bb24ac39fb0b5c87c93d44cba3b6e189126f00604b5fa6818d6"
WINDOWS_ZIP="4b55a33917a5941e87d507ceb8af01391c01fc4574a2543fab3f0b3cf35402f0"
WINDOWS_GUEST_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
P7=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
PIXELS=256*224
SCENES={3984:0,4000:0,4016:54709,4032:296,4048:0,4064:24346,4080:296,4096:0}
SCHEMA="qa08-real-original-native-2P-blackout-forced-blank-RGB5-source/1"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def actual_pixels(source:bytes,native_p7:bytes)->int:
    if len(source)!=PIXELS*4 or not native_p7.startswith(P7) or len(native_p7)!=len(P7)+PIXELS*4:
        raise ValueError("not two full untouched 256x224 BGRX/P7 framebuffer sources")
    native=native_p7[len(P7):]
    wrong=0
    for index in range(0,PIXELS*4,4):
        blue,green,red,_=source[index:index+4]
        g5=green>>3
        old=(red,(g5<<3)|(g5>>2),blue)
        if old!=tuple(native[index:index+3]):
            wrong+=1
    return wrong


def checked(path:Path,sha256:str)->zipfile.ZipFile:
    if sha(path.read_bytes())!=sha256:
        raise ValueError("source archive not byte-identical to known original/Windows")
    return zipfile.ZipFile(path)


def inspect(original:zipfile.ZipFile,blackout:zipfile.ZipFile,win:zipfile.ZipFile)->dict:
    old=json.loads(original.read("qa08-original-2p-fullroute.json"))
    observed=json.loads(blackout.read("qa08-original-blackout-INIDISP-source.json"))
    native=json.loads(win.read("qa08-windows-2p-fullroute.json"))
    if (old.get("actual_callbacks_captured")!=263 or
        old.get("actual_script_quit_frame")!=5484 or
        observed.get("original_263_callbacks_byte_equal_to_untouched_Snes9x") is not True or
        observed.get("original_blackout_frame_all_57344_RGB_pixels_black") is not True or
        native.get("actual_native_simulations")!=5484 or
        native.get("actual_source_count")!=263 or
        native.get("source_geometry")!=[256,224] or
        native.get("actual_native_guest_CRC_sha256")!=WINDOWS_GUEST_CRC):
        raise ValueError("original/native 2P source frame and route authority incomplete")
    snaps=observed["source_original_blackout_register_snapshots"]
    if ([x["original_actual_source_dump_frame"] for x in snaps]!=[4015,4016,4017]
        or [x["original_input_port_INIDISP_2100_byte"] for x in snaps]!=["80","80","02"]
        or [x["original_source_PPU_forced_blank"] for x in snaps]!=[1,1,0]):
        raise ValueError("source Snes9x original INIDISP blackout transition changed")
    writes=observed["source_original_2100_write_journal"]["original_2100_actual_CPU_DMA_HDMA_beam_writes"]
    if ([(x["frame"],x["value"]) for x in writes] != list(zip(
        range(4017,4024),("02","04","06","08","0A","0C","0E"))) or
        any(x["source"]!="cpu" or x["v"]!=(230 if x["frame"]<4023 else 231)
            for x in writes)):
        raise ValueError("authentic original $2100 CPU beam V230/V231 ladder changed")
    byline=native["read_only_native_PPU_registers"]["per_line_native_PPU_state"]
    selected={}
    for f in (4015,4016,4017):
        lines=[row for row in byline if row["actual_native_snes_frame"]==f]
        if (len(lines)!=3 or set(x["ppu_line"] for x in lines)!={1,112,114} or
            len(set(x["inidisp"] for x in lines))!=1):
            raise ValueError("native PPU frame/scanline source witness incomplete")
        selected[f]=lines[0]["inidisp"]
    if selected!={4015:"80",4016:"02",4017:"04"}:
        raise ValueError("native PPU state no longer advances one image frame early")
    manifests={r["real_original_snes9x_callback_frame"]:r["original_unchanged_BGRX_sha256"]
               for r in old["each_authentic_callback"]}
    native_hashes=native["source_frame_P7_SHA256_by_guest"]
    if len(manifests)!=263 or len(native_hashes)!=263:
        raise ValueError("source/full native frame provenance incomplete")
    sampled=[]
    for native_f in range(1280,5473,16):
        callback=native_f-1
        original_pixels=original.read(f"frames/frame_{callback:06d}_256x224.raw")
        native_p7=win.read(f"source/ur-baldosa-original-source-{native_f:06d}.pam")
        if (sha(original_pixels)!=manifests.get(callback) or
            sha(native_p7)!=native_hashes.get(str(native_f))):
            raise ValueError(f"source original/native video file mutated at {native_f}")
        if native_f in SCENES:
            wrong=actual_pixels(original_pixels,native_p7)
            if wrong!=SCENES[native_f]:
                raise ValueError(f"original-vs-native RGB5 drift at {native_f}: {wrong}")
            sampled.append({"Windows_guest":native_f,"source_original_callback":callback,
                            "wrong_RGB5_pixels":wrong})
    original_black=original.read("frames/frame_004015_256x224.raw")
    if any(original_black):
        raise ValueError("original source blackout callback 4015 not uniformly black")
    return {
        "schema":SCHEMA,
        "source_original_archive_zip_sha256":ORIGINAL_ZIP,
        "source_original_blackout_register_archive_sha256":BLACKOUT_ZIP,
        "real_Windows_original_mode_PPU_archive_sha256":WINDOWS_ZIP,
        "real_windows_guest_CRC_5484_sha256":WINDOWS_GUEST_CRC,
        "all_263_real_original_and_Windows_fullsize_PPU_images_sha_authenticated":True,
        "source_original_video_callback_at_4015_full_black_pixels":PIXELS,
        "source_original_INIDISP_by_source_frame":{"4015":"80","4016":"80","4017":"02"},
        "original_real_CPU_2100_ramp_frames":list(range(4017,4024)),
        "original_real_CPU_2100_writes_at_vcounter":230,
        "native_real_PPU_INIDISP_by_Windows_frame":
            {str(f):v for f,v in sorted(selected.items())},
        "native_4016_incorrect_RGB5_pixels":SCENES[4016],
        "source_4016_blackout_transition_fraction_of_full_image":SCENES[4016]/PIXELS,
        "source_narrow_blackout_and_adjacent_video_control":sampled,
        "original_callback_equals_native_guest_minus_one_no_temporal_search":True,
        "source_exact_guest_CPU_instruction_phase_proven":False,
        "native_2100_port_writer_CPU_vs_raster_phase_proven":False,
        "graphics_field_brightness_fix_accepted":False,
        "release_and_HD_art_likeness_accepted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--blackout",type=Path,required=True)
    p.add_argument("--windows",type=Path,required=True)
    p.add_argument("--result",type=Path,required=True)
    a=p.parse_args()
    with checked(a.original,ORIGINAL_ZIP) as original, \
         checked(a.blackout,BLACKOUT_ZIP) as blackout, \
         checked(a.windows,WINDOWS_ZIP) as native:
        r=inspect(original,blackout,native)
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("QA08_SOURCE_NATIVE_BLACKOUT", "original=263", "Windows=263",
          "guest_4016_wrong_RGB5_pixels=54709", "clock_fix_and_release=unaccepted")


if __name__=="__main__":
    main()
