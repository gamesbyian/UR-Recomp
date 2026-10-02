#!/usr/bin/env python3
"""Compare stock vs entry-biased state immediately around the A531 helper."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import analyze_widescreen_preparation_boundary as boundary

HELP_RE=re.compile(r"WSHELP frame=(?P<frame>\d+) pc=(?P<pc>[0-9A-Fa-f]{6}) changes=(?P<changes>[^\n\r]*)")

def parse_help(path: Path) -> dict[int,dict[int,tuple[int,int]]]:
    text=path.read_text(encoding="utf-8",errors="replace")
    out={}
    for m in HELP_RE.finditer(text):
        changes={}
        raw=m.group("changes")
        for item in raw.split(","):
            if not item:
                continue
            addr,before,after=item.split(":")
            changes[int(addr,16)]=(int(before,16),int(after,16))
        out[int(m.group("frame"))]=changes
    return out

def row_map(rows: list[dict], pc: int) -> dict[int,dict]:
    return {r["frame"]:r for r in rows if r["pc"]==pc}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("entry_bias",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()

    cr=boundary.parse(args.control)
    wr=boundary.parse(args.entry_bias)
    c_after=row_map(cr,0x81A534)
    w_after=row_map(wr,0x81A534)
    c_call=row_map(cr,0x81A597)
    w_call=row_map(wr,0x81A597)
    hc=parse_help(args.control)
    hw=parse_help(args.entry_bias)

    frames=sorted(set(c_after)&set(w_after)&set(c_call)&set(w_call))
    register_diffs=[]
    call_diffs=[]
    memory_diffs=[]
    for frame in frames:
        reg={}
        for key in ("a","x","y","d","p"):
            if c_after[frame][key] != w_after[frame][key]:
                reg[key]={
                    "control":c_after[frame][key],
                    "entry_bias":w_after[frame][key],
                    "delta":(w_after[frame][key]-c_after[frame][key]) & 0xffff,
                }
        if reg:
            register_diffs.append({"frame":frame,"registers":reg})

        call={}
        for key in ("a","x","y","d","p"):
            if c_call[frame][key] != w_call[frame][key]:
                call[key]={
                    "control":c_call[frame][key],
                    "entry_bias":w_call[frame][key],
                    "delta":(w_call[frame][key]-c_call[frame][key]) & 0xffff,
                }
        if call:
            call_diffs.append({"frame":frame,"registers":call})

        addrs=sorted(set(hc.get(frame,{})) | set(hw.get(frame,{})))
        mem={}
        for addr in addrs:
            ca=hc.get(frame,{}).get(addr)
            wa=hw.get(frame,{}).get(addr)
            c_after_val=None if ca is None else ca[1]
            w_after_val=None if wa is None else wa[1]
            if c_after_val != w_after_val:
                mem[f"{addr:04X}"]={"control":c_after_val,"entry_bias":w_after_val}
        if mem:
            memory_diffs.append({"frame":frame,"addresses":mem})

    report={
        "schema_version":1,
        "frames_compared":len(frames),
        "helper_return_register_differences":register_diffs,
        "edge_helper_call_register_differences":call_diffs,
        "helper_output_memory_differences":memory_diffs,
    }
    lines=["# A531 helper staging discriminator","",
           f"- frames compared: **{len(frames)}**",
           f"- helper-return register-difference frames: **{len(register_diffs)}**",
           f"- edge-helper-call register-difference frames: **{len(call_diffs)}**",
           f"- helper-output memory-difference frames: **{len(memory_diffs)}**",""]
    if register_diffs:
        lines += ["First helper-return register difference:","",json.dumps(register_diffs[0],indent=2),""]
    if call_diffs:
        lines += ["First edge-helper-call register difference:","",json.dumps(call_diffs[0],indent=2),""]
    if memory_diffs:
        lines += ["First helper-output memory difference:","",json.dumps(memory_diffs[0],indent=2),""]
    payload=json.dumps(report,indent=2)+"\n"
    md="\n".join(lines)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if frames else 2

if __name__=="__main__":
    raise SystemExit(main())
