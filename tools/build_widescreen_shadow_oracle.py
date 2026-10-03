#!/usr/bin/env python3
"""Build a compact future-stock strip oracle for the +16 host-capacity prototype."""
from __future__ import annotations
import argparse, re
from pathlib import Path

RX=re.compile(
    r"URWS_PRIMARY margin=0 camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)

def build(text:str)->list[tuple[int,int,str]]:
    rows=[]
    for camx,edge,count,payload in RX.findall(text):
        if int(count)!=16 or int(edge,16)==0xffff:
            continue
        rows.append((int(camx),int(edge,16),payload.upper()))
    if not rows:
        raise ValueError("no stock horizontal strip rows found")
    return rows

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("out",type=Path)
    args=ap.parse_args()
    rows=build(args.log.read_text(encoding="utf-8",errors="replace"))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(
        "".join(f"{camx} {edge:04X} {payload}\n" for camx,edge,payload in rows),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} stock strip rows to {args.out}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
