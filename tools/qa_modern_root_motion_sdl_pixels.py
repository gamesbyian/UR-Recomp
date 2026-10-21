#!/usr/bin/env python3
"""Exact native SDL P7 A/B test for Modern root marker motion and reduced motion.

The Windows game is run four times in independent clean-process roots, on
the same real exact executable/ROM/source, with its existing opt-in
UR_MODERN_MENU_TEST_TICK60 clock. No new simulated renderer, guest clock,
or gameplay change. Only the narrow source blue selection marker is allowed
to change when the 60Hz host presentation tick changes; reduced-motion output
must be pixel-identical across the two ticks. These are HOST SDL pixels, not
physical monitor, eye-test, or original asset-likeness approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

P7=re.compile(rb"\AP7\nWIDTH 1280\nHEIGHT 720\nDEPTH 4\n"
              rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
EXPECTED=(1280,720)
MARKER_ROI=(36,183,152,306)
MAX_CHANGED=2048


class MotionPixelAuditError(ValueError):
    pass


def raster(path: Path) -> tuple[bytes,str]:
    if not path.is_file() or path.is_symlink():
        raise MotionPixelAuditError("real native readback absent or redirected: "+str(path))
    raw=path.read_bytes()
    match=P7.match(raw)
    if match is None or len(raw)!=match.end()+EXPECTED[0]*EXPECTED[1]*4:
        raise MotionPixelAuditError("native SDL readback has wrong P7 header/size: "+str(path))
    return raw[match.end():],hashlib.sha256(raw).hexdigest()


def compare(
    normal_tick0: Path,normal_tick10: Path,
    reduced_tick0: Path,reduced_tick10: Path,
) -> dict:
    frames={name:raster(path) for name,path in (
        ("normal_tick0",normal_tick0),
        ("normal_tick10",normal_tick10),
        ("reduced_tick0",reduced_tick0),
        ("reduced_tick10",reduced_tick10))}
    neutral=frames["normal_tick0"][0]
    moving=frames["normal_tick10"][0]
    reduced_a=frames["reduced_tick0"][0]
    reduced_b=frames["reduced_tick10"][0]
    if reduced_a!=reduced_b:
        raise MotionPixelAuditError(
            "reduced-motion native SDL output changes with injected tick")
    w,h=EXPECTED
    changed=[]
    for index in range(w*h):
        offset=4*index
        if neutral[offset:offset+4]!=moving[offset:offset+4]:
            x,y=index%w,index//w
            changed.append((x,y))
            if len(changed)>MAX_CHANGED:
                raise MotionPixelAuditError("normal motion altered too much of root SDL frame")
    if not changed:
        raise MotionPixelAuditError("normal Modern root marker does not move between source phases")
    left,top,right,bottom=MARKER_ROI
    if any(not(left<=x<right and top<=y<bottom) for x,y in changed):
        raise MotionPixelAuditError("normal motion changed pixels outside narrow cursor marker ROI")
    return {
        "schema_version":1,
        "actual_native_final_sdl_output":[w,h],
        "normal_tick0_p7_sha256":frames["normal_tick0"][1],
        "normal_tick10_p7_sha256":frames["normal_tick10"][1],
        "reduced_tick0_p7_sha256":frames["reduced_tick0"][1],
        "reduced_tick10_p7_sha256":frames["reduced_tick10"][1],
        "normal_changed_pixel_count":len(changed),
        "normal_change_bounds":[min(x for x,y in changed),min(y for x,y in changed),
                                max(x for x,y in changed),max(y for x,y in changed)],
        "normal_motion_confined_to_source_selection_marker":True,
        "reduced_motion_all_p7_pixels_identical":True,
        "guest_authoritative_frames_changed":False,
        "human_visual_approved":False,
        "hardware_approved":False,
        "release_gate_credit":0,
    }


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("normal_tick0","normal_tick10","reduced_tick0","reduced_tick10"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    p.add_argument("--report",type=Path)
    opts=p.parse_args()
    try:
        result=compare(opts.normal_tick0,opts.normal_tick10,
                       opts.reduced_tick0,opts.reduced_tick10)
        if opts.report:
            if opts.report.exists() or opts.report.is_symlink():
                raise MotionPixelAuditError("report already exists")
            opts.report.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        return 0
    except (MotionPixelAuditError,OSError) as exc:
        print("MODERN_ROOT_SDL_MOTION_EVIDENCE_REJECTED:",exc)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
