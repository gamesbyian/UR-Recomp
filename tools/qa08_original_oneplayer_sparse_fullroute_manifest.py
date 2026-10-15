#!/usr/bin/env python3
"""One authentic sparse full-route 1P Snes9x Original raster source record.

Same pinned USA/2014 Snes9x/snesref and original 1P input script as the
accepted 65-callback moving-window run. A single original guest execution
samples exactly callback 1279..5439 step16, including course entry, moving
camera, finish/result and return. No invented frames, camera registration,
original instruction/timing patches or release credit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FIRST,LAST,STEP=1279,5439,16
SIZE=256*224*4
SCHEMA="qa08-original-snes9x-authentic-oneplayer-sparse-full-route-source/1"


def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def observe(folder:Path,script:Path,log:Path,rom:Path,core:Path)->dict:
    if sha(rom.read_bytes())!=ROM_SHA:
        raise ValueError("not exact original USA retail ROM")
    raw_script=script.read_bytes()
    if (b"turbo on" in raw_script or b"\r" in raw_script
        or b"until16 0053 == 8610" not in raw_script
        or b"press right 1200" not in raw_script):
        raise ValueError("original action route mutated or encoded incorrectly")
    log_raw=log.read_bytes()
    quit_records=re.findall(rb"(?m)^script f=(\d+) quit\s*$",log_raw)
    if len(quit_records)!=1 or int(quit_records[0])!=5447:
        raise ValueError("original 1P source did not finish expected input route")
    frames=list(range(FIRST,LAST+1,STEP))
    expected={f"frame_{f:06d}_256x224.raw" for f in frames}
    actual={p.name for p in folder.iterdir() if p.is_file()}
    if actual!=expected:
        raise ValueError("missing or unsolicited Snes9x source callback")
    hashes=[]
    for callback in frames:
        raw=(folder/f"frame_{callback:06d}_256x224.raw").read_bytes()
        if len(raw)!=SIZE:
            raise ValueError("original PPU BGRX cropped or invalid")
        hashes.append({"original_callback":callback,"original_1based_run_frame":callback+1,
                       "actual_unmodified_BGRX_sha256":sha(raw)})
    unique=len({x["actual_unmodified_BGRX_sha256"] for x in hashes})
    if unique<100:
        raise ValueError("insufficient distinct original 1P scenes/camera movement")
    cohorts={
      "menu_to_race": [f for f in frames if f<=1759],
      "race_cameras_and_movement":[f for f in frames if 1775<=f<=5103],
      "finish_and_menu_return":[f for f in frames if f>=5119],
    }
    if any(len(x)<10 for x in cohorts.values()):
        raise ValueError("source window excludes transition or result vicinity")
    return {
      "schema":SCHEMA,
      "source_producer":"independent pinned original Snes9x libretro via snesref",
      "USA_ROM_sha256":ROM_SHA,
      "original_emulator_core_binary_sha256":sha(core.read_bytes()),
      "source_original_route_LF_without_turbo_sha256":sha(raw_script),
      "source_script_log_sha256":sha(log_raw),
      "original_script_exit_guest_frame":5447,
      "sampled_original_callback_selection":[FIRST,LAST,STEP],
      "requested_original_callbacks":len(frames),
      "observed_original_distinct_raster_hashes":unique,
      "source_pixel_geometry":[256,224],
      "source_pixel_format":"genuine Snes9x expanded RGB565 BGRX8888",
      "actual_original_source_scene_frame_numbers":cohorts,
      "all_original_source_frame_hashes":hashes,
      "no_cropping_spatial_rebase_or_frame_synthesis":True,
      "native_window_camera_CPU_phase_equal_proven":False,
      "source_frames_not_player_output_or_result_authority":True,
      "release_approved":False,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("frames","script","log","rom","core","out"):
        parser.add_argument("--"+key,required=True,type=Path)
    a=parser.parse_args()
    evidence=observe(a.frames,a.script,a.log,a.rom,a.core)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("QA08_ORIGINAL_SPARSE_1P_SOURCE",
          "frames="+str(evidence["requested_original_callbacks"]),
          "unique="+str(evidence["observed_original_distinct_raster_hashes"]),
          "result_proven=0")


if __name__=="__main__":
    main()
