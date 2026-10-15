#!/usr/bin/env python3
"""Compare 263 ORIGINAL 2014 Snes9x 2P source rasters to real Windows 2P PPU.

No temporal search, phase shift, 216-high crop, layer mask or fake event
acceptance. Original callback f-1 against actual title PPU guest frame f,
including moving both-player split, raster transitions, finish and menu
return. Entire 57,344 RGB5 pixels; only SNES 6-bit green to native 5-bit.
Frame and input route source hashes are mandatory. A discrepancy is a
reproducible result, not a workflow-exit exception.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from qa08_compare_original_windows_oneplayer import (
    compare,no_turbo,verify_windows_checkout_script,
)

SCHEMA="qa08-exact-original-to-native-windows-2p-rgb5-sparse-fullroute/1"
ORIGINAL_SCHEMA="qa08-original-pinned-snes9x-authentic-2p-fullroute-raster/1"
WINDOWS_SCHEMA="qa08-real-windows-2p-split-fullroute-source-20261015/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
HEADER=(b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
W,H=256,224
FIRST,LAST,STEP=1280,5472,16
NUM=(LAST-FIRST)//STEP+1


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def inspect(original_dir:Path,win_dir:Path,route:Path)->dict:
    orig=json.loads((original_dir/"qa08-original-2p-fullroute.json").read_text())
    native=json.loads((win_dir/"qa08-windows-2p-fullroute.json").read_text())
    original_route=(original_dir/"original.script").read_bytes()
    script=route.read_bytes()
    if (orig.get("schema")!=ORIGINAL_SCHEMA or
        orig.get("unaltered_USA_ROM_sha256")!=ROM_SHA or
        orig.get("actual_script_quit_frame")!=5484 or
        orig.get("capture_selection")!=[FIRST-1,LAST-1,STEP] or
        orig.get("actual_callbacks_captured")!=NUM or
        orig.get("original_script_finished_after_result_return") is not True or
        orig.get("release_quality_ledger_accepted") is not False):
        raise ValueError("original Snes9x 2P source authority invalid or incomplete")
    if (original_route!=no_turbo(script) or
        sha(original_route)!=orig.get("exact_original_two_pad_route_LF_without_turbo_sha256")):
        raise ValueError("real source original 2P buttons/timing differ from Windows")
    checkout=verify_windows_checkout_script(
        script,native.get("actual_two_pad_route_sha256",""))
    if (native.get("schema")!=WINDOWS_SCHEMA or
        native.get("source_geometry")!=[W,H] or
        native.get("original_USA_ROM_sha256")!=ROM_SHA or
        native.get("source_frames_expected_and_observed")!=[FIRST,LAST,STEP] or
        native.get("actual_source_count")!=NUM or
        not (LAST<native.get("actual_native_simulations",0)<9505) or
        native.get("original_snes9x_PPU_frame_RGB5_parity_unadjudicated") is not True or
        native.get("release_quality_ledger_admitted") is not False):
        raise ValueError("authentic native two-pad source, exit or negative status invalid")
    manifest=orig.get("each_authentic_callback")
    native_hashes=native.get("source_frame_P7_SHA256_by_guest")
    if not isinstance(manifest,list) or len(manifest)!=NUM or not isinstance(native_hashes,dict):
        raise ValueError("source frame manifest incomplete")
    observed={
        p.name for p in (win_dir/"source").iterdir() if p.is_file()
    }
    required={
        f"ur-baldosa-original-source-{n:06d}.pam" for n in range(FIRST,LAST+1,STEP)
    }
    if observed!=required:
        raise ValueError("2P native source output missing, duplicated or added")
    rows=[]
    for index,guest in enumerate(range(FIRST,LAST+1,STEP)):
        callback=guest-1
        m=manifest[index]
        if (m.get("real_original_snes9x_callback_frame")!=callback or
            m.get("original_1based_frame")!=callback+1):
            raise ValueError("original Snes9x frame numbering invalid")
        ref=(original_dir/"frames"/f"frame_{callback:06d}_256x224.raw").read_bytes()
        if len(ref)!=W*H*4 or sha(ref)!=m.get("original_unchanged_BGRX_sha256"):
            raise ValueError("original 2P Snes9x callback corrupted or cropped")
        file=(win_dir/"source"/f"ur-baldosa-original-source-{guest:06d}.pam")
        p7=file.read_bytes()
        if (len(p7)!=len(HEADER)+W*H*4 or not p7.startswith(HEADER)
            or sha(p7)!=native_hashes.get(str(guest))):
            raise ValueError("native Windows PPU callback mismatched, cropped or replaced")
        result=compare(ref,p7[len(HEADER):])
        rows.append({
            "original_snes9x_callback":callback,
            "real_windows_guest":guest,
            "original_unchanged_BGRX_sha256":sha(ref),
            "native_unchanged_P7_sha256":sha(p7),
            "wrong_RGB5_pixels":result["wrong_RGB5_pixels"],
            "wrong_RGB5_pixels_per_row":result["wrong_pixels_by_row"],
            "first_eight_wrong":result["first_eight_wrong"],
        })
    groups={
        "pre_GO_and_countdown":[r for r in rows if r["real_windows_guest"]<2016],
        "moving_split_screen":[r for r in rows if 2016<=r["real_windows_guest"]<5136],
        "finish_result_and_menu_return":[r for r in rows if r["real_windows_guest"]>=5136],
    }
    if [len(v) for v in groups.values()]!=[46,195,22]:
        raise ValueError("predeclared three-scene original/source windows differ")
    divergent=next((r for r in rows if r["wrong_RGB5_pixels"]>0),None)
    return {
        "schema":SCHEMA,
        "status":"exact_2P_sparse_source" if divergent is None
                 else "real_2P_original_vs_Windows_strict_RGB5_divergence",
        "original_ROM_sha256":ROM_SHA,
        "actual_original_source_callback_count":NUM,
        "actual_native_source_callback_count":NUM,
        "original_Windows_source_route_EOL":checkout,
        "full_logical_pixel_geometry":[W,H],
        "authentic_native_guest_simulations":native["actual_native_simulations"],
        "native_guest_CRC_sha256":native["actual_native_guest_CRC_sha256"],
        "actual_native_Windows_executable_sha256":native["actual_windows_PE_sha256"],
        "all_2P_source_pixels_compared":NUM*W*H,
        "strict_exact_2P_sampled_frames":sum(r["wrong_RGB5_pixels"]==0 for r in rows),
        "strict_divergent_2P_sampled_frames":sum(r["wrong_RGB5_pixels"]>0 for r in rows),
        "total_original_vs_windows_incorrect_RGB5_pixels":sum(r["wrong_RGB5_pixels"] for r in rows),
        "earliest_real_divergent_guest":divergent["real_windows_guest"] if divergent else None,
        "source_scene_groups":{
            name:{
                "real_frames":len(v),
                "exact_frames":sum(r["wrong_RGB5_pixels"]==0 for r in v),
                "wrong_pixels":sum(r["wrong_RGB5_pixels"] for r in v),
            } for name,v in groups.items()
        },
        "unmasked_original_256x224_RGB5_presentation_only":True,
        "continuous_executed_guest_CPU_camera_input_phase_independently_proven":False,
        "split_OAM_HDMA_registrations_independently_proven":False,
        "physical_4x_widescreen_HD_art_release_accepted":False,
        "release_quality_ledger_accepted":False,
        "full_original_to_native_source_comparisons":rows,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("original-dir","windows-dir","route","out"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    evidence=inspect(a.original_dir,a.windows_dir,a.route)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_ORIGINAL_WIN_2P_FULLROUTE",evidence["status"],
          "exact="+str(evidence["strict_exact_2P_sampled_frames"]),
          "wrong="+str(evidence["total_original_vs_windows_incorrect_RGB5_pixels"]),
          "release=0")


if __name__=="__main__":
    main()
