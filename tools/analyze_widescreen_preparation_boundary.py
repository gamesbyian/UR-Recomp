#!/usr/bin/env python3
"""Locate the post-camera, pre-edge scheduling boundary inside 81:A52F..A59D."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

RX = re.compile(
    r"WSBND frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) "
    r"pc=(?P<pc>[0-9A-Fa-f]{6}) camx=(?P<camx>\d+) camy=(?P<camy>\d+) "
    r"camdx=(?P<camdx>-?\d+) camdy=(?P<camdy>-?\d+) "
    r"edgex=(?P<edgex>\d+) edgex2=(?P<edgex2>\d+) edgey=(?P<edgey>\d+) edgey2=(?P<edgey2>\d+) "
    r"cnt=(?P<c0>\d+),(?P<c1>\d+),(?P<c2>\d+),(?P<c3>\d+)"
)

EDGE_KEYS = ("edgex","edgex2","edgey","edgey2","c0","c1","c2","c3")

def parse(path: Path) -> list[dict]:
    rows=[]
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        m=RX.search(line)
        if not m:
            continue
        g=m.groupdict()
        row={k:int(v,16) if k=="pc" else int(v) for k,v in g.items()}
        rows.append(row)
    if not rows:
        raise SystemExit("no WSBND observations")
    return rows

def analyze(rows: list[dict]) -> dict:
    by_frame=defaultdict(list)
    for row in rows:
        by_frame[row["frame"]].append(row)

    candidates=[]
    for frame, seq in sorted(by_frame.items()):
        if len(seq) < 3 or max(r["camdx"] for r in seq) <= 0:
            continue
        last_cam_change_index=None
        first_edge_change_index=None
        for i in range(1,len(seq)):
            if seq[i]["camx"] != seq[i-1]["camx"]:
                last_cam_change_index=i
        if last_cam_change_index is None:
            continue
        baseline={k:seq[last_cam_change_index][k] for k in EDGE_KEYS}
        for i in range(last_cam_change_index+1,len(seq)):
            if any(seq[i][k] != baseline[k] for k in EDGE_KEYS):
                first_edge_change_index=i
                break
        if first_edge_change_index is None:
            continue
        hook=seq[last_cam_change_index]
        first_edge=seq[first_edge_change_index]
        later_cam_change=any(
            seq[i]["camx"] != hook["camx"]
            for i in range(last_cam_change_index+1,len(seq))
        )
        candidates.append({
            "frame":frame,
            "candidate_hook_pc":hook["pc"],
            "candidate_hook_pc_hex":f"{hook['pc']:06X}",
            "camera_x_after_update":hook["camx"],
            "camera_dx":hook["camdx"],
            "first_edge_change_pc":first_edge["pc"],
            "first_edge_change_pc_hex":f"{first_edge['pc']:06X}",
            "edge_state_before":baseline,
            "edge_state_after":{k:first_edge[k] for k in EDGE_KEYS},
            "later_camera_x_change":later_cam_change,
        })

    stable={}
    for c in candidates:
        key=(c["candidate_hook_pc"],c["first_edge_change_pc"],c["later_camera_x_change"])
        stable[key]=stable.get(key,0)+1
    ranked=sorted(stable.items(), key=lambda kv:(-kv[1],kv[0]))
    best=None
    if ranked:
        (hook,edge,later),count=ranked[0]
        best={
            "candidate_hook_pc":hook,
            "candidate_hook_pc_hex":f"{hook:06X}",
            "first_edge_change_pc":edge,
            "first_edge_change_pc_hex":f"{edge:06X}",
            "supporting_frames":count,
            "later_camera_x_change":later,
        }
    return {
        "schema_version":1,
        "frames_observed":len(by_frame),
        "candidate_frames":candidates,
        "stable_boundary":best,
        "boundary_isolation_supported":bool(best) and not best["later_camera_x_change"],
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    report=analyze(parse(args.log))
    best=report["stable_boundary"]
    lines=["# Camera-to-strip preparation boundary",""]
    if best:
        lines += [
            f"- candidate post-camera hook: **{best['candidate_hook_pc_hex']}**",
            f"- first subsequent edge/count change: **{best['first_edge_change_pc_hex']}**",
            f"- supporting moving frames: **{best['supporting_frames']}**",
            f"- later camera-X change after hook: **{best['later_camera_x_change']}**",
            "",
        ]
    else:
        lines += ["- no stable boundary recovered",""]
    payload=json.dumps(report,indent=2)+"\n"
    md="\n".join(lines)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["boundary_isolation_supported"] else 2

if __name__=="__main__":
    raise SystemExit(main())
