#!/usr/bin/env python3
"""Exact original Snes9x completed-field read-only medal OAM/PPU captures.

No original-core, guest, controller route, HDMA, raster or gameplay edits.
Extend the previously verified source-only 5183/results and 4015 blackout
snesref frontend observer in its *disposable* pinned checkout. Copy actual
PPU OAM/CGRAM/registers at original completed callback fields 1279,4031,4175
(the predetermined original-side frame IDs for native1280,4032,4176).
End-of-field OAM is not proof of effective sprite ownership mid-frame.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools import qa08_snesref_original_blackout_host_patch as previous
except ImportError:
    import qa08_snesref_original_blackout_host_patch as previous

MARK="UR_QA08_ORIGINAL_MEDAL_MATCHING_FIELDS"
ADDED=r"""        /* UR_QA08_ORIGINAL_MEDAL_MATCHING_FIELDS: exactly three
         * original completed fields, not fabricated same-line OAM. */
        if (getenv("UR_QA08_ORIGINAL_MEDAL_FIELDS")) {
            if (g_frame == 1280) do_dump("qa08_arrow_1280");
            if (g_frame == 4032) do_dump("qa08_medal_4032");
            if (g_frame == 4176) do_dump("qa08_medal_4176");
        }
"""
AFTER=previous.HOOK_AFTER.replace("        trace_tick();",ADDED+"        trace_tick();")
if AFTER==previous.HOOK_AFTER or AFTER.count(MARK)!=1:
    raise RuntimeError("lost pinned existing snesref field-loop anchor")

def patch_source(source:str)->str:
    if MARK in source:
        if source.count(AFTER)!=1 or source.count(MARK)!=1:
            raise ValueError("partial or tampered original-medal observer")
        return source
    if (source.count(previous.HOOK_AFTER)!=1 or
        source.count(previous.WRITE_HISTORY)!=1 or
        "static void do_dump(const char* tag) {" not in source or
        "p_retro_run();" not in source):
        raise ValueError("original blackout/results read-only prerequisites changed")
    return source.replace(previous.HOOK_AFTER,AFTER,1)

def apply(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if (previous.base.rev(game)!=previous.base.GAME or
        previous.base.rev(game/"snesrecomp")!=previous.base.CORE):
        raise ValueError("foreign original reference or SNESRecomp source pin")
    path=game/previous.base.RELATIVE
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
        f=apply(a.game,write=a.apply_readonly_capture)
    except (OSError,ValueError) as exc:
        p.exit(2,f"QA08_ORIGINAL_MEDAL_SOURCE_REJECTED: {exc}\n")
    print("QA08_ORIGINAL_MEDAL_SOURCE",f,"staged="+str(int(a.apply_readonly_capture)),
          "original_script_modified=0 actual_scanline_OAM_ownership_proven=0")

if __name__=="__main__":
    main()
