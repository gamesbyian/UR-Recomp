#!/usr/bin/env python3
"""Bounded 1P transition/race/result original PPU sources in REAL Windows PE.

One already-built UniracersSNESRecomp Windows executable, one original USA
1P input route, 5,447 actual native guest simulations, no game/state/HD
changes. The same existing post-PPU callback observes at most 261 selected
16-frame slots from guest1280..5440. It does not invent uncaptured images,
align missing frames, record a second renderer, or claim final art/release QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from baldosa_windows_native_pause_route import run_route

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FIRST,LAST,STEP=1280,5440,16
SOURCE_HEADER=(b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
               b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
REPORT_SCHEMA="qa08-bounded-windows-original-1p-transition-raster-coverage/1"
LOG=re.compile(r"^UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=(\d+) "
               r"logical=256x224 saved=1 "
               r"source=post-original-ppu-before-present$",re.M)


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def inspect(folder:Path,log:str,crc:list[str])->dict:
    if len(crc)!=5447 or any(not re.fullmatch(r"0x[0-9a-fA-F]{8}",v) for v in crc):
        raise ValueError("authentic complete 5447-frame native 1P guest trace absent")
    samples=[int(x) for x in LOG.findall(log)]
    if not samples or len(samples)!=len(set(samples)):
        raise ValueError("no unique real PPU source callback")
    if "UR_QA08_WINDOWS_SOURCE_REJECT" in log:
        raise ValueError("oneplayer observer rejected repeated/unsafe capture")
    seen={}
    for p in folder.glob("*"):
        m=re.fullmatch(r"ur-baldosa-original-source-(\d{6})\.pam",p.name)
        if not m or not p.is_file():
            raise ValueError("unexpected output in isolated oneplayer PPU directory")
        frame=int(m[1])
        if frame<FIRST or frame>LAST or (frame-FIRST)%STEP:
            raise ValueError("source frame outside exact bounded 16-frame schedule")
        raw=p.read_bytes()
        if len(raw)!=len(SOURCE_HEADER)+256*224*4 or not raw.startswith(SOURCE_HEADER):
            raise ValueError("captured source is not unmasked original 256x224 RGBA")
        if frame in seen:
            raise ValueError("duplicate source slot")
        seen[frame]=sha(raw)
    if set(samples)!=set(seen):
        raise ValueError("callback journal and source frames differ")
    # Presence is a source-only observation, never synthesize gaps. The three
    # scene regions come from actual 1P input script and runtime milestones:
    # NMI mode changes to race at 1369, GO at 1720 and menu return at 5147.
    regions={
        "race_entry_and_countdown": [f for f in seen if 1280<=f<=1744],
        "moving_race_and_camera": [f for f in seen if 1760<=f<=5104],
        "finish_result_return_menu": [f for f in seen if 5120<=f<=LAST],
    }
    if any(len(v)<2 for v in regions.values()):
        raise ValueError("oneplayer source cannot support all three scene regions")
    return {
        "schema":REPORT_SCHEMA,
        "logical_source_geometry":[256,224],
        "pixel_layout":"unmasked 32-bit RGBA P7 sampled after original native PPU",
        "original_input_route_native_simulations":len(crc),
        "native_guest_CRC_source_sha256":sha(
            ("\n".join(x.lower() for x in crc)+"\n").encode("ascii")),
        "callback_frame_selection_window":[FIRST,LAST,STEP],
        "possible_callbacks":(LAST-FIRST)//STEP+1,
        "actual_source_callback_count":len(seen),
        "observed_regions":{k:sorted(v) for k,v in regions.items()},
        "unobserved_callback_slots":[f for f in range(FIRST,LAST+1,STEP) if f not in seen],
        "complete_source_RGBA_P7_sha256_by_frame":{str(k):v for k,v in sorted(seen.items())},
        "guest_result_at_5147_script_return_not_independently_parity_proven":True,
        "same_original_snes9x_raster_parity_proven":False,
        "CPU_camera_input_phase_and_1P_complete_event_proven":False,
        "HD_art_owner_likeness_approved":False,
        "release_quality_ledger_admitted":False,
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for s in ("exe","rom","script","out"):
        ap.add_argument("--"+s,type=Path,required=True)
    ap.add_argument("--timeout",type=int,default=300)
    a=ap.parse_args()
    if sha(a.rom.read_bytes())!=ROM_SHA:
        ap.error("not authentic USA source ROM")
    if a.out.exists():
        ap.error("source output directory already exists")
    a.out.mkdir(parents=True)
    source=a.out/"source"
    source.mkdir()
    keys={
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(source.resolve()),
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"oneplayer-coverage",
    }
    previous={k:os.environ.get(k) for k in keys}
    os.environ.update(keys)
    try:
        crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                           a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for k,v in previous.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    evidence=inspect(source,log,crcs)
    evidence["exact_executable_sha256"]=sha(a.exe.read_bytes())
    evidence["exact_original_1P_input_route_sha256"]=sha(a.script.read_bytes())
    (a.out/"qa08-windows-original-oneplayer-coverage.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_ONEPLAYER_REAL_PPU_COVERAGE",
          "actual_callbacks="+str(evidence["actual_source_callback_count"]),
          "selected_slots="+str(evidence["possible_callbacks"]),
          "release_approved=0")


if __name__=="__main__":
    main()
