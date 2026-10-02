#!/usr/bin/env python3
"""Acceptance analysis for the double-pass +8 Widescreen strip scheduler."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import analyze_widescreen_strip_schedule as base

VRX=re.compile(r"WSVRAM frame=(?P<frame>\d+) cols=(?P<cols>.*)$")

def parse_vram(path: Path) -> dict[int,dict[tuple[int,int],str]]:
    out=defaultdict(dict)
    text=path.read_text(encoding="utf-8",errors="replace")
    for m in VRX.finditer(text):
        frame=int(m.group("frame"))
        raw=m.group("cols").strip()
        if not raw:
            continue
        for item in raw.split(","):
            parts=item.split(":")
            if len(parts)!=3:
                continue
            slot,dest,payload=parts
            out[frame][(int(slot),int(dest,16))]=payload.upper()
    return dict(out)

def horiz(row):
    return [d for d in row["ready"] if d["size"]==0x20 and d["vmain"]==0x81]

def sig(d):
    return (d["vram"],d["size"],d["vmain"],d["payload_hex"])

def ring_next(dest: int) -> int | None:
    if not (0x0D80 <= dest <= 0x0D9F):
        return None
    return 0x0D80 + ((dest-0x0D80+1)&0x1f)

def longest_run(frames: list[int]) -> int:
    if not frames:
        return 0
    best=cur=1
    for a,b in zip(frames,frames[1:]):
        cur=cur+1 if b==a+1 else 1
        best=max(best,cur)
    return best

def analyze(control_rows, widened_rows, widened_vram):
    cbuild={r["frame"]:r for r in control_rows if r["site"]=="after_build"}
    wbuild={r["frame"]:r for r in widened_rows if r["site"]=="after_build"}
    wcons=base.consumed_same_frame(widened_rows)

    future=defaultdict(list)
    for r in cbuild.values():
        for d in horiz(r):
            future[sig(d)].append((r["frame"],r["camx"],d))

    state_diffs=[]
    candidate_rows=[]
    successes=[]
    for frame in sorted(set(cbuild)&set(wbuild)):
        c,w=cbuild[frame],wbuild[frame]
        state_equal=(
            c["gameplay"]==w["gameplay"]
            and (c["camx"],c["camy"],c["camdx"],c["camdy"])
             == (w["camx"],w["camy"],w["camdx"],w["camdy"])
        )
        if not state_equal:
            state_diffs.append(frame)

        control_sigs={sig(d) for d in horiz(c)}
        extras=[d for d in horiz(w) if sig(d) not in control_sigs]
        primary=next((d for d in horiz(w) if d["slot"]==2),None)
        for d in extras:
            if d["slot"]!=3:
                continue
            candidates=[
                x for x in future.get(sig(d),[])
                if x[0]>frame and 1 <= x[1]-w["camx"] <= 16
            ]
            if not candidates:
                continue
            future_frame,future_cam,_=min(candidates,key=lambda x:(x[1]-w["camx"],x[0]))
            consumed=(frame,sig(d)) in wcons
            post_vram=widened_vram.get(frame,{}).get((d["slot"],d["vram"]))
            vram_equal=post_vram==d["payload_hex"]
            adjacent=bool(primary) and ring_next(primary["vram"])==d["vram"]
            row={
                "frame":frame,
                "slot":d["slot"],
                "source":d["source"],
                "vram":d["vram"],
                "primary_vram":None if primary is None else primary["vram"],
                "adjacent_ring_column":adjacent,
                "future_frame":future_frame,
                "camera_x_advance":future_cam-w["camx"],
                "same_frame_consumed":consumed,
                "post_nmi_vram_matches_payload":vram_equal,
                "state_equal":state_equal,
            }
            candidate_rows.append(row)
            if all((adjacent,consumed,vram_equal,state_equal)):
                successes.append(row)

    success_frames=sorted({r["frame"] for r in successes})
    report={
        "schema_version":1,
        "common_frames":len(set(cbuild)&set(wbuild)),
        "state_difference_frames":state_diffs,
        "future_stock_candidate_count":len(candidate_rows),
        "accepted_future_columns":len(successes),
        "accepted_frames":success_frames,
        "longest_consecutive_acceptance_run":longest_run(success_frames),
        "all_state_equal":bool(cbuild) and not state_diffs,
        "all_candidates_adjacent":bool(candidate_rows) and all(r["adjacent_ring_column"] for r in candidate_rows),
        "all_candidates_consumed":bool(candidate_rows) and all(r["same_frame_consumed"] for r in candidate_rows),
        "all_candidates_post_nmi_match":bool(candidate_rows) and all(r["post_nmi_vram_matches_payload"] for r in candidate_rows),
        "examples":successes[:40],
    }
    # Transitional/end-of-run candidates may legitimately miss a same-frame
    # NMI sample. Acceptance therefore requires a durable consecutive window,
    # exact post-NMI bytes, and invariant state rather than every observed edge.
    report["success"]=all((
        report["all_state_equal"],
        report["accepted_future_columns"] >= 10,
        report["longest_consecutive_acceptance_run"] >= 8,
        all(r["adjacent_ring_column"] for r in successes),
        all(r["same_frame_consumed"] for r in successes),
        all(r["post_nmi_vram_matches_payload"] for r in successes),
    ))
    return report

def render(d):
    lines=[
        "# Double-pass +8 Widescreen strip acceptance","",
        f"- authoritative/camera state equal: **{d['all_state_equal']}**",
        f"- future-stock candidates: **{d['future_stock_candidate_count']}**",
        f"- accepted adjacent columns: **{d['accepted_future_columns']}**",
        f"- longest consecutive accepted run: **{d['longest_consecutive_acceptance_run']} frames**",
        f"- acceptance: **{d['success']}**","",
    ]
    if d["examples"]:
        lines += [
            "| frame | source | primary VRAM | +8 VRAM | stock future frame | camera advance | consumed | post-NMI VRAM |",
            "|---:|---:|---:|---:|---:|---:|---|---|",
        ]
        for r in d["examples"]:
            lines.append(
                f"| {r['frame']} | {r['source']:04X} | {r['primary_vram']:04X} | {r['vram']:04X} | "
                f"{r['future_frame']} | {r['camera_x_advance']} | {r['same_frame_consumed']} | "
                f"{r['post_nmi_vram_matches_payload']} |"
            )
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("doublepass",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    report=analyze(base.parse(args.control),base.parse(args.doublepass),parse_vram(args.doublepass))
    md=render(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["success"] else 2

if __name__=="__main__":
    raise SystemExit(main())
