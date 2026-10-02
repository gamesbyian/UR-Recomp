#!/usr/bin/env python3
"""Classify the A59E->AB88 horizontal-count widening discriminator."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import analyze_widescreen_strip_schedule as base

def slot2(rows):
    out={}
    for r in rows:
        if r["site"]!="after_build":
            continue
        d=next((x for x in r["descriptors"] if x["slot"]==2),None)
        if d is not None:
            out[r["frame"]]={"row":r,"descriptor":d}
    return out

def analyze(control, widened):
    c=slot2(control); w=slot2(widened)
    common=sorted(set(c)&set(w))
    rows=[]
    state_diffs=[]
    changed=[]
    for frame in common:
        cr,wr=c[frame],w[frame]
        cd,wd=cr["descriptor"],wr["descriptor"]
        state_equal=(
            cr["row"]["gameplay"]==wr["row"]["gameplay"]
            and (cr["row"]["camx"],cr["row"]["camy"],cr["row"]["camdx"],cr["row"]["camdy"])
              == (wr["row"]["camx"],wr["row"]["camy"],wr["row"]["camdx"],wr["row"]["camdy"])
        )
        if not state_equal:
            state_diffs.append(frame)
        different=(cd["ready"],cd["vram"],cd["source"],cd["size"],cd["vmain"],cd["payload_hex"]) != (
            wd["ready"],wd["vram"],wd["source"],wd["size"],wd["vmain"],wd["payload_hex"])
        if different:
            changed.append(frame)
        rows.append({
            "frame":frame,
            "state_equal":state_equal,
            "control":cd,
            "count32":wd,
            "descriptor_changed":different,
            "size_delta":wd["size"]-cd["size"],
            "payload_prefix_matches_control":bool(cd["payload_hex"]) and wd["payload_hex"].startswith(cd["payload_hex"]),
        })
    size64=[r for r in rows if r["count32"]["ready"] and r["count32"]["size"]==0x40]
    report={
        "schema_version":1,
        "common_frames":len(common),
        "state_difference_frames":state_diffs,
        "descriptor_changed_frames":changed,
        "size64_frames":[r["frame"] for r in size64],
        "all_state_equal":bool(common) and not state_diffs,
        "builder_expands_count32_to_64_bytes":bool(size64),
        "rows":rows,
    }
    if not changed:
        report["classification"]="count-not-consumed-by-ab88"
    elif size64:
        report["classification"]="count-expands-single-descriptor"
    else:
        report["classification"]="count-changes-descriptor-other"
    return report

def render(d):
    lines=["# Widescreen horizontal-count discriminator","",
        f"- common frames: **{d['common_frames']}**",
        f"- authoritative/camera state equal: **{d['all_state_equal']}**",
        f"- descriptor changed frames: **{len(d['descriptor_changed_frames'])}**",
        f"- 64-byte slot-2 frames: **{len(d['size64_frames'])}**",
        f"- classification: **{d['classification']}**",""]
    lines += ["| frame | control size | count32 size | destination | payload prefix | state |",
              "|---:|---:|---:|---:|---|---|"]
    for r in [x for x in d["rows"] if x["descriptor_changed"]][:40]:
        lines.append(
            f"| {r['frame']} | {r['control']['size']} | {r['count32']['size']} | "
            f"{r['count32']['vram']:04X} | {r['payload_prefix_matches_control']} | "
            f"{'match' if r['state_equal'] else 'DIFF'} |"
        )
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("count32",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    d=analyze(base.parse(args.control),base.parse(args.count32))
    md=render(d)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if d["all_state_equal"] else 2

if __name__=="__main__":
    raise SystemExit(main())
