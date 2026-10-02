#!/usr/bin/env python3
"""Characterize the stock A597 edge-preparation helper and wrapper operands."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

TOOLS_DIR=Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0,str(TOOLS_DIR))
import analyze_widescreen_preparation_boundary as boundary

EDGE_RE=re.compile(
    r"WSEDGEHELP frame=(?P<frame>\d+) pc=(?P<pc>[0-9A-Fa-f]{6}) "
    r"changes=(?P<changes>[^\n\r]*)"
)

def parse_changes(raw: str) -> dict[int,tuple[int,int]]:
    out={}
    for item in raw.split(","):
        if not item:
            continue
        addr,before,after=item.split(":")
        out[int(addr,16)]=(int(before,16),int(after,16))
    return out

def parse_edge(path: Path) -> list[dict]:
    text=path.read_text(encoding="utf-8",errors="replace")
    rows=[]
    for m in EDGE_RE.finditer(text):
        rows.append({
            "frame":int(m.group("frame")),
            "pc":int(m.group("pc"),16),
            "changes":parse_changes(m.group("changes")),
        })
    if not rows:
        raise SystemExit("no WSEDGEHELP observations")
    return rows

def instruction_rows(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    frame=min(r["frame"] for r in rows)
    seq=[r for r in rows if r["frame"]==frame]
    out=[]
    for r in seq:
        item={
            "pc":r["pc"],
            "pc_hex":f"{r['pc']:06X}",
            "opcode":r["op"],
            "opcode_hex":f"{r['op']:02X}",
            "operand_bytes":[r["b1"],r["b2"]],
            "a":r["a"],"x":r["x"],"y":r["y"],
            "camx":r["camx"],"camy":r["camy"],
            "edgex":r["edgex"],"edgex2":r["edgex2"],
            "edgey":r["edgey"],"edgey2":r["edgey2"],
            "counts":[r["c0"],r["c1"],r["c2"],r["c3"]],
        }
        if r["op"]==0x20:
            target=r["b1"] | (r["b2"]<<8)
            item["jsr_target"]=0x810000|target
            item["jsr_target_hex"]=f"81:{target:04X}"
        elif r["op"] in {0xAD,0x6D,0x2D,0x8D,0xC9,0xA9}:
            item["operand_u16"]=r["b1"] | (r["b2"]<<8)
            item["operand_u16_hex"]=f"{item['operand_u16']:04X}"
        out.append(item)
    return out

def analyze(path: Path) -> dict:
    b=boundary.parse(path)
    e=parse_edge(path)
    instructions=instruction_rows(b)

    frequency=Counter()
    deltas={}
    examples={}
    for row in e:
        for addr,(before,after) in row["changes"].items():
            frequency[addr]+=1
            delta=(after-before)&0xff
            deltas.setdefault(addr,Counter())[delta]+=1
            examples.setdefault(addr,[]).append({
                "frame":row["frame"],"before":before,"after":after,"delta":delta
            })

    n=len(e)
    addresses=[]
    for addr,count in sorted(frequency.items()):
        addresses.append({
            "address":addr,
            "address_hex":f"{addr:04X}",
            "changed_frames":count,
            "changed_fraction":count/n,
            "delta_histogram":{
                f"{d:02X}":c for d,c in sorted(deltas[addr].items())
            },
            "examples":examples[addr][:8],
        })

    edge_fields={0x0505:"edge_x",0x0509:"edge_x_secondary",0x050D:"edge_y",0x0511:"edge_y_secondary",
                 0x052B:"count_x_primary",0x052F:"count_x_secondary",
                 0x0533:"count_y_primary",0x0537:"count_y_secondary"}
    known=[]
    for item in addresses:
        addr=item["address"]
        # Include either byte of each known 16-bit field.
        base=next((b for b in edge_fields if addr in (b,b+1)),None)
        if base is not None:
            known.append({**item,"field":edge_fields[base],"word_base_hex":f"{base:04X}"})

    report={
        "schema_version":1,
        "fixture":"preparation-emission-race",
        "helper_call_site":"81:A597",
        "helper_return_site":"81:A59A",
        "observed_frames":n,
        "wrapper_instructions":instructions,
        "changed_addresses":addresses,
        "known_edge_count_changes":known,
        "stable_changed_addresses":[
            x["address_hex"] for x in addresses if x["changed_frames"]==n
        ],
    }
    return report

def render(report: dict) -> str:
    lines=[
        "# A597 edge-preparation helper contract","",
        f"- observed helper invocations: **{report['observed_frames']}**",
        f"- distinct low-WRAM bytes changed: **{len(report['changed_addresses'])}**",
        f"- bytes changed on every sampled invocation: **{', '.join(report['stable_changed_addresses']) or 'none'}**",
        "",
        "## Wrapper instruction window","",
        "| PC | op | operand | JSR target | A | X | Y | camera X | edge X |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in report["wrapper_instructions"]:
        operand=" ".join(f"{b:02X}" for b in r["operand_bytes"])
        lines.append(
            f"| {r['pc_hex']} | {r['opcode_hex']} | {operand} | "
            f"{r.get('jsr_target_hex','')} | {r['a']} | {r['x']} | {r['y']} | "
            f"{r['camx']} | {r['edgex']} |"
        )
    lines += ["","## Low-WRAM changes across A597","",
              "| address | changed frames | deltas |",
              "|---|---:|---|"]
    for r in report["changed_addresses"]:
        hist=", ".join(f"{k}×{v}" for k,v in r["delta_histogram"].items())
        lines.append(f"| {r['address_hex']} | {r['changed_frames']} | {hist} |")
    if report["known_edge_count_changes"]:
        lines += ["","Known edge/count fields touched:"]
        for r in report["known_edge_count_changes"]:
            lines.append(
                f"- {r['field']} ({r['word_base_hex']}), byte {r['address_hex']}: "
                f"{r['changed_frames']}/{report['observed_frames']} sampled calls"
            )
    return "\n".join(lines)+"\n"

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    report=analyze(args.log)
    payload=json.dumps(report,indent=2)+"\n"
    md=render(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
