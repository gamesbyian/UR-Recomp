#!/usr/bin/env python3
"""Locate the first observed Uniracers medal-matrix mutation in SRAM dumps."""

from __future__ import annotations
import argparse,json,re
from pathlib import Path

MEDAL_START=0x069C
MEDAL_END=0x072C
TAG_RE=re.compile(r"medal-(baseline|\d+k)")

def medal_changes(base:bytes,cur:bytes):
    return [
        {"offset":i,"before":base[i],"after":cur[i]}
        for i in range(MEDAL_START,MEDAL_END)
        if base[i]!=cur[i]
    ]

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("dump_dir",type=Path)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    dumps={}
    for p in args.dump_dir.glob("medal-*.sram.bin"):
        m=TAG_RE.match(p.name)
        if m:
            dumps[m.group(1)]=p.read_bytes()
    if "baseline" not in dumps:
        raise SystemExit("missing medal-baseline SRAM dump")
    base=dumps["baseline"]
    if len(base)!=8192:
        raise SystemExit("baseline SRAM is not 8192 bytes")
    rows=[]
    order=[("010k",10000),("020k",20000),("040k",40000),("080k",80000)]
    for tag,frame in order:
        data=dumps.get(tag)
        if data is None:
            continue
        if len(data)!=8192:
            raise SystemExit(f"{tag}: SRAM is not 8192 bytes")
        changes=medal_changes(base,data)
        rows.append({"tag":tag,"frame":frame,"medal_changes":changes})
    first=next((r for r in rows if r["medal_changes"]),None)
    report={
      "schema_version":1,
      "fixture":"Dessyreqt 2014 reset-anchored 100% bot",
      "baseline_frame":750,
      "samples":rows,
      "first_observed_medal_mutation":first,
      "search_complete_through_frame":max((r["frame"] for r in rows),default=750),
    }
    if first:
        report["interpretation"]="First bounded sample with a game-authored medal-matrix mutation; refine between the preceding sample and this frame before building final reload acceptance."
    else:
        report["interpretation"]="No medal mutation observed in the bounded search window; extend exponentially without weakening the medal criterion."
    payload=json.dumps(report,indent=2)+"\n"
    print(payload,end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    return 0 if first else 1

if __name__=="__main__":
    raise SystemExit(main())
