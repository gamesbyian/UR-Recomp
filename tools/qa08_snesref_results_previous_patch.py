#!/usr/bin/env python3
"""Stage one opt-in read-only 5183 PPU dump in the pinned original snesref host.

The authentic Snes9x script must remain byte-for-byte unchanged. Do not split
press: each command adds a trailing idle frame. This stages in a disposable
game/663816 reference checkout only; no shared SNESRecomp or guest edits.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess

GAME="10b864b9d14a7b7416dd909eb7b054c88faef101"
CORE="075fbe4c8e0d97b0013be541795c39cb644a9709"
RELATIVE=Path("snesrecomp/tools/snesref/frontend.cpp")
MARK="UR_QA08_SNESREF_RESULTS_PREVIOUS"
BEFORE="""        p_retro_run();
        g_frame++;
        trace_tick();"""
AFTER="""        p_retro_run();
        g_frame++;
        /* UR_QA08_SNESREF_RESULTS_PREVIOUS: actual completed original frame,
         * no input-script boundary, render substitution or core writes.
         * Disabled in normal reference usage; original PPU 263-frame raster
         * must replay byte-exact against independent unmodified Snes9x. */
        if (g_frame == 5183 && getenv("UR_QA08_SNESREF_RESULTS_PREVIOUS")) {
            do_dump("qa08_results_previous");
        }
        trace_tick();"""

def patch_source(source:str)->str:
    if MARK in source:
        if source.count(MARK)!=1 or source.count(AFTER)!=1:
            raise ValueError("source witness marker/body drift")
        return source
    if source.count(BEFORE)!=1 or "static void do_dump(const char* tag)" not in source:
        raise ValueError("original snesref frame/dump sequencing unexpected")
    return source.replace(BEFORE,AFTER,1)

def rev(path:Path)->str:
    return subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
                          check=True,capture_output=True,text=True).stdout.strip()

def apply(game:Path,write:bool=False)->Path:
    game=game.resolve()
    if rev(game)!=GAME or rev(game/"snesrecomp")!=CORE:
        raise ValueError("unrecognized original reference/core pin")
    path=game/RELATIVE
    old=path.read_text(encoding="utf-8")
    new=patch_source(old)
    if write and old!=new:
        path.write_text(new,encoding="utf-8")
    return path

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-readonly-capture",action="store_true")
    a=p.parse_args()
    try:
        path=apply(a.game,write=a.apply_readonly_capture)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        p.exit(2,f"QA08_SOURCE_HOST_PREVIOUS_REJECTED: {exc}\n")
    print(f"QA08_SOURCE_HOST_PREVIOUS file={path} staged={int(a.apply_readonly_capture)} original_route_unchanged=1 raster_acceptance=0")

if __name__=="__main__":
    main()
