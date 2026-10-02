#!/usr/bin/env python3
"""Localize A59E preparation writes to edge/count state and the 32-byte strip buffer."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

RX=re.compile(
    r"WSA59E frame=(?P<frame>\d+) pc=(?P<pc>[0-9A-Fa-f]{6}) "
    r"op=(?P<op>[0-9A-Fa-f]{2}) b1=(?P<b1>[0-9A-Fa-f]{2}) b2=(?P<b2>[0-9A-Fa-f]{2}) "
    r"a=(?P<a>[0-9A-Fa-f]{4}) x=(?P<x>[0-9A-Fa-f]{4}) y=(?P<y>[0-9A-Fa-f]{4}) "
    r"d=(?P<d>[0-9A-Fa-f]{4}) p=(?P<p>[0-9A-Fa-f]{4}) "
    r"e0505=(?P<e0505>[0-9A-Fa-f]{4}) e0521=(?P<e0521>[0-9A-Fa-f]{4}) "
    r"c052B=(?P<c052b>[0-9A-Fa-f]{4}) s0433=(?P<payload>[0-9A-Fa-f]{64})"
)

def parse(path: Path) -> list[dict]:
    rows=[]
    text=path.read_text(encoding="utf-8",errors="replace")
    for m in RX.finditer(text):
        g=m.groupdict()
        row={k:int(v,16) for k,v in g.items() if k!="payload"}
        row["payload"]=g["payload"].upper()
        rows.append(row)
    if not rows:
        raise SystemExit("no WSA59E rows")
    return rows

def analyze(rows: list[dict]) -> dict:
    by_frame=defaultdict(list)
    for r in rows:
        by_frame[r["frame"]].append(r)

    frame_reports=[]
    transitions=[]
    for frame,seq in sorted(by_frame.items()):
        fr={"frame":frame,"edge_changes":[],"count_changes":[],"payload_changes":[]}
        for i in range(1,len(seq)):
            prev,cur=seq[i-1],seq[i]
            if cur["e0505"]!=prev["e0505"] or cur["e0521"]!=prev["e0521"]:
                item={
                    "from_pc":prev["pc"],"from_pc_hex":f"{prev['pc']:06X}",
                    "to_pc":cur["pc"],"to_pc_hex":f"{cur['pc']:06X}",
                    "edge_0505_before":prev["e0505"],"edge_0505_after":cur["e0505"],
                    "edge_0521_before":prev["e0521"],"edge_0521_after":cur["e0521"],
                    "trigger_opcode":prev["op"],"trigger_opcode_hex":f"{prev['op']:02X}",
                    "trigger_operand":[prev["b1"],prev["b2"]],
                }
                fr["edge_changes"].append(item); transitions.append(("edge",item))
            if cur["c052b"]!=prev["c052b"]:
                item={
                    "from_pc":prev["pc"],"from_pc_hex":f"{prev['pc']:06X}",
                    "to_pc":cur["pc"],"to_pc_hex":f"{cur['pc']:06X}",
                    "before":prev["c052b"],"after":cur["c052b"],
                    "trigger_opcode":prev["op"],"trigger_opcode_hex":f"{prev['op']:02X}",
                    "trigger_operand":[prev["b1"],prev["b2"]],
                }
                fr["count_changes"].append(item); transitions.append(("count",item))
            if cur["payload"]!=prev["payload"]:
                first=next((j for j,(a,b) in enumerate(zip(bytes.fromhex(prev["payload"]),bytes.fromhex(cur["payload"]))) if a!=b),None)
                item={
                    "from_pc":prev["pc"],"from_pc_hex":f"{prev['pc']:06X}",
                    "to_pc":cur["pc"],"to_pc_hex":f"{cur['pc']:06X}",
                    "first_changed_byte":first,
                    "before":prev["payload"],"after":cur["payload"],
                    "trigger_opcode":prev["op"],"trigger_opcode_hex":f"{prev['op']:02X}",
                    "trigger_operand":[prev["b1"],prev["b2"]],
                }
                fr["payload_changes"].append(item); transitions.append(("payload",item))
        frame_reports.append(fr)

    def modes(kind):
        counts={}
        for k,item in transitions:
            if k!=kind: continue
            key=(item["from_pc"],item["to_pc"])
            counts[key]=counts.get(key,0)+1
        return [
            {"from_pc":a,"from_pc_hex":f"{a:06X}","to_pc":b,"to_pc_hex":f"{b:06X}","frames":n}
            for (a,b),n in sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))
        ]

    edge_modes=modes("edge"); count_modes=modes("count"); payload_modes=modes("payload")
    return {
        "schema_version":1,
        "frames_observed":len(by_frame),
        "edge_transition_sites":edge_modes,
        "count_transition_sites":count_modes,
        "payload_transition_sites":payload_modes,
        "frames":frame_reports,
        "stable_edge_site":edge_modes[0] if edge_modes else None,
        "stable_count_site":count_modes[0] if count_modes else None,
        "stable_payload_site":payload_modes[0] if payload_modes else None,
    }

def render(d):
    lines=["# A59E strip-preparation instruction trace","",
           f"- frames observed: **{d['frames_observed']}**"]
    for label,key in (("edge","stable_edge_site"),("count","stable_count_site"),("payload","stable_payload_site")):
        x=d[key]
        lines.append(
            f"- stable {label} transition: **{x['from_pc_hex']} -> {x['to_pc_hex']}** ({x['frames']} frames)"
            if x else f"- stable {label} transition: **none**"
        )
    lines += ["","| frame | edge transitions | count transitions | payload transitions |",
              "|---:|---:|---:|---:|"]
    for f in d["frames"]:
        lines.append(f"| {f['frame']} | {len(f['edge_changes'])} | {len(f['count_changes'])} | {len(f['payload_changes'])} |")
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    d=analyze(parse(args.log))
    md=render(d)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if d["stable_edge_site"] and d["stable_payload_site"] else 2

if __name__=="__main__":
    raise SystemExit(main())
