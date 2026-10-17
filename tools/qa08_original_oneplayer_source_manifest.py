#!/usr/bin/env python3
"""Admit only a real, complete original Snes9x 1P moving callback window.

Pure source observer and manifest. Original route, ROM and binary remain
unaltered; no still image is synthesized, shifted, downscaled or admitted as
SNES hardware truth. This producer is NOT the independent comparator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FIRST,LAST=2176,2240
FRAME_BYTES=256*224*4
SCHEMA="qa08-original-snes9x-real-1p-raster-callback-window/1"


def sha(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def observe(frames:Path,script:Path,log:Path,rom:Path,core:Path)->dict:
    if sha(rom.read_bytes())!=ROM_SHA:
        raise ValueError("original USA retail ROM fingerprint changed")
    script_bytes=script.read_bytes()
    if b"turbo on" in script_bytes.lower() or b"until16 0053 == 8610" not in script_bytes:
        raise ValueError("original 1P route not exact stock input grammar")
    log_bytes=log.read_bytes()
    ticks=re.findall(rb"(?m)^script f=(\d+) quit\s*$",log_bytes)
    if len(ticks)!=1 or int(ticks[0])<LAST+1:
        raise ValueError("original core did not finish genuine 1P route")
    expected={f"frame_{f:06d}_256x224.raw" for f in range(FIRST,LAST+1)}
    actual={x.name for x in frames.iterdir() if x.is_file()}
    if actual!=expected:
        raise ValueError("missing/extra original video callback data")
    records=[]
    for frame in range(FIRST,LAST+1):
        raw=(frames/f"frame_{frame:06d}_256x224.raw").read_bytes()
        if len(raw)!=FRAME_BYTES:
            raise ValueError("real original core reported invalid 256x224 BGRX callback")
        records.append({
            "original_callback_frame_zero_based":frame,
            "original_retro_run_one_based":frame+1,
            "unmodified_BGRX8888_sha256":sha(raw)
        })
    if len({r["unmodified_BGRX8888_sha256"] for r in records})<8:
        raise ValueError("unmoving/truncated original 1P video evidence")
    first=(frames/f"frame_{FIRST:06d}_256x224.raw").read_bytes()
    last=(frames/f"frame_{LAST:06d}_256x224.raw").read_bytes()
    pixel_changes=sum(first[i:i+3]!=last[i:i+3]
                      for i in range(0,FRAME_BYTES,4))
    if pixel_changes<1000:
        raise ValueError("original callback window insufficient moving visual content")
    return {
        "schema":SCHEMA,
        "original_system":"Snes9x libretro through pinned snesref",
        "original_USA_ROM_sha256":ROM_SHA,
        "original_core_binary_sha256":sha(core.read_bytes()),
        "unchanged_original_route_no_turbo_SHA256":sha(script_bytes),
        "original_script_log_sha256":sha(log_bytes),
        "observed_original_run_quit_frame":int(ticks[0]),
        "source_geometry":[256,224],
        "raw_layout":"BGRX8888 (Snes9x expanded RGB565)",
        "actual_original_callback_range":[FIRST,LAST],
        "callback_count":len(records),
        "distinct_callback_sources":len({r["unmodified_BGRX8888_sha256"] for r in records}),
        "endpoint_changed_full_rgb_pixels":pixel_changes,
        "actual_source_frames":records,
        "same_CPU_camera_controller_phase_as_native_proven":False,
        "no_framebuffer_synthesis_crop_resize":True,
        "release_approved":False
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("frames","script","log","rom","core","out"):
        ap.add_argument("--"+name,required=True,type=Path)
    a=ap.parse_args()
    result=observe(a.frames,a.script,a.log,a.rom,a.core)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("QA08_ORIGINAL_1P_REAL_CALLBACKS",
          result["callback_count"],
          "moving_pixels",result["endpoint_changed_full_rgb_pixels"],
          "release_approved=0")


if __name__=="__main__":
    main()
