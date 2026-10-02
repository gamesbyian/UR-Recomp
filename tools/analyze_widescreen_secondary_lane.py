#!/usr/bin/env python3
"""Evaluate the secondary horizontal edge/count pair as a +8 strip lane."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import analyze_widescreen_strip_schedule as base

def horiz(row):
    return [d for d in row["ready"] if d["size"]==0x20 and d["vmain"]==0x81]

def sig(d):
    return (d["vram"],d["size"],d["vmain"],d["payload_hex"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("secondary",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()

    cr=base.parse(args.control)
    wr=base.parse(args.secondary)
    cbuild={r["frame"]:r for r in cr if r["site"]=="after_build"}
    wbuild={r["frame"]:r for r in wr if r["site"]=="after_build"}
    ccons=base.consumed_same_frame(cr)
    wcons=base.consumed_same_frame(wr)

    future=defaultdict(list)
    for r in cbuild.values():
        for d in horiz(r):
            future[sig(d)].append((r["frame"],r["camx"],d))

    rows=[]
    state_diffs=[]
    successful=[]
    for frame in sorted(set(cbuild)&set(wbuild)):
        c,w=cbuild[frame],wbuild[frame]
        state_equal=(
            c["gameplay"]==w["gameplay"]
            and (c["camx"],c["camy"],c["camdx"],c["camdy"])
             == (w["camx"],w["camy"],w["camdx"],w["camdy"])
        )
        if not state_equal:
            state_diffs.append(frame)

        cs={sig(d) for d in horiz(c)}
        extras=[d for d in horiz(w) if sig(d) not in cs]
        matches=[]
        for d in extras:
            s=sig(d)
            candidates=[
                x for x in future.get(s,[])
                if x[0] > frame and 1 <= x[1]-w["camx"] <= 16
            ]
            if candidates:
                ff,fcam,_=min(candidates,key=lambda x:(x[1]-w["camx"],x[0]))
                consumed=(frame,s) in wcons
                matches.append({
                    "slot":d["slot"],"vram":d["vram"],"source":d["source"],
                    "future_frame":ff,"camera_x_advance":fcam-w["camx"],
                    "same_frame_consumed":consumed,
                })
                if consumed and state_equal:
                    successful.append((frame,d,ff,fcam-w["camx"]))
        rows.append({
            "frame":frame,"state_equal":state_equal,
            "extra_descriptors":extras,"future_matches":matches,
        })

    report={
        "schema_version":1,
        "common_frames":len(rows),
        "state_difference_frames":state_diffs,
        "all_state_equal":bool(rows) and not state_diffs,
        "frames_with_extra_horizontal_descriptor":sum(bool(r["extra_descriptors"]) for r in rows),
        "future_stock_match_frames":sum(bool(r["future_matches"]) for r in rows),
        "successful_future_stock_matches":len(successful),
        "success":bool(successful) and not state_diffs,
        "examples":[{
            "frame":f,"slot":d["slot"],"vram":d["vram"],"source":d["source"],
            "future_frame":ff,"camera_x_advance":adv
        } for f,d,ff,adv in successful[:40]],
    }
    if report["success"]:
        report["classification"]="secondary-lane-prepares-future-stock-column"
    elif report["frames_with_extra_horizontal_descriptor"]:
        report["classification"]="secondary-lane-active-but-wrong-data"
    else:
        report["classification"]="secondary-lane-not-materialized"

    lines=["# Secondary horizontal-lane discriminator","",
           f"- classification: **{report['classification']}**",
           f"- state equal: **{report['all_state_equal']}**",
           f"- frames with extra horizontal descriptor: **{report['frames_with_extra_horizontal_descriptor']}**",
           f"- future-stock match frames: **{report['future_stock_match_frames']}**",
           f"- successful same-frame-consumed future matches: **{report['successful_future_stock_matches']}**",""]
    if successful:
        lines += ["| frame | slot | VRAM | source | future frame | camera advance |",
                  "|---:|---:|---:|---:|---:|---:|"]
        for f,d,ff,adv in successful[:40]:
            lines.append(f"| {f} | {d['slot']} | {d['vram']:04X} | {d['source']:04X} | {ff} | {adv} |")
    md="\n".join(lines)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["all_state_equal"] else 2

if __name__=="__main__":
    raise SystemExit(main())
