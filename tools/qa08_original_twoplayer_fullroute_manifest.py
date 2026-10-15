#!/usr/bin/env python3
"""One immutable original Snes9x 2P full-route source reference.

Run the already pinned USA retail 2014 Snes9x core and original Baldosa
race_2p.txt script once to its *actual* final quit. Sample exact raw
256x224 BGRX every 16 frames across menus, split-screen movement and
post-finish menu return. No changes to CPU/APU, OAM/HDMA, Modern, SRM,
guest or input; no guessed frame count, fabricated viewport, source crop,
time shift or performance-volume CI campaign.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FIRST,STEP,MAX=1279,16,9503
SIZE=256*224*4
SCHEMA="qa08-original-pinned-snes9x-authentic-2p-fullroute-raster/1"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def callback_numbers(actual_quit:int)->list[int]:
    if actual_quit<3500 or actual_quit>MAX+1:
        raise ValueError("2P script quit outside supported original full-route bound")
    return list(range(FIRST,min(actual_quit-1,MAX)+1,STEP))


def observe(frames:Path,script:Path,log:Path,rom:Path,core:Path)->dict:
    if sha(rom.read_bytes())!=ROM:
        raise ValueError("not exact USA retail ROM")
    route=script.read_bytes()
    if (b"\r" in route or b"turbo on" in route
        or route.count(b"until16 0053 == F60C")!=2
        or route.count(b"until16 0053 == 8610")!=1
        or b"p2:right" not in route or b"p2:down" not in route
        or b"press right+p2:right 1500" not in route):
        raise ValueError("original two-pad race route altered, turboed or misencoded")
    log_bytes=log.read_bytes()
    records=re.findall(rb"(?m)^script f=(\d+) quit\s*$",log_bytes)
    if len(records)!=1:
        raise ValueError("original 2P source never completed its real input script")
    quit_frame=int(records[0])
    samples=callback_numbers(quit_frame)
    wanted={f"frame_{k:06d}_256x224.raw" for k in samples}
    observed={p.name for p in frames.iterdir() if p.is_file()}
    if wanted!=observed:
        raise ValueError("original Snes9x 2P video callback missing/unsolicited")
    hashes=[]
    for f in samples:
        raw=(frames/f"frame_{f:06d}_256x224.raw").read_bytes()
        if len(raw)!=SIZE:
            raise ValueError("original 2P source raster wrong size or cropped")
        hashes.append({
            "real_original_snes9x_callback_frame":f,
            "original_1based_frame":f+1,
            "original_unchanged_BGRX_sha256":sha(raw),
        })
    unique=len({x["original_unchanged_BGRX_sha256"] for x in hashes})
    if unique<100:
        raise ValueError("genuine 2P route lacked independently moving source scenes")
    menu=[x for x in samples if x<2000]
    moving=[x for x in samples if 2000<=x<quit_frame-350]
    terminal=[x for x in samples if x>=quit_frame-350]
    if min(len(menu),len(moving),len(terminal))<10:
        raise ValueError("2P source capture skipped menus, movement or terminal region")
    return {
      "schema":SCHEMA,
      "real_original_source_emulator":"pinned Snes9x libretro via snesref",
      "unaltered_USA_ROM_sha256":ROM,
      "original_core_binary_sha256":sha(core.read_bytes()),
      "exact_original_two_pad_route_LF_without_turbo_sha256":sha(route),
      "actual_original_script_log_sha256":sha(log_bytes),
      "actual_script_quit_frame":quit_frame,
      "original_script_finished_after_result_return":True,
      "capture_selection":[FIRST,samples[-1],STEP],
      "native_unmasked_geometry":[256,224],
      "native_raw_encoding":"unaltered Snes9x BGRX8888 expanded RGB565",
      "actual_callbacks_captured":len(hashes),
      "distinct_raster_SHA256_images":unique,
      "scene_windows":{
          "pre_go_and_countdown":menu,
          "moving_2p_split_race":moving,
          "finish_result_and_menu_return":terminal,
      },
      "each_authentic_callback":hashes,
      "not_a_proof_of_native_65816_camera_input_phase":True,
      "not_a_proof_of_complete_original_to_windows_2P_parity":True,
      "no_cropped_216_high_or_synthesized_video":True,
      "release_quality_ledger_accepted":False,
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ("frames","script","log","rom","core","out"):
        ap.add_argument("--"+key,required=True,type=Path)
    a=ap.parse_args()
    result=observe(a.frames,a.script,a.log,a.rom,a.core)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("QA08_2P_ORIGINAL_GENUINE_FULLROUTE",
        "callback_count="+str(result["actual_callbacks_captured"]),
        "distinct="+str(result["distinct_raster_SHA256_images"]),
        "quit="+str(result["actual_script_quit_frame"]),
        "results_native_parity=UNVERIFIED release_approved=0")


if __name__=="__main__":
    main()
