#!/usr/bin/env python3
"""Extract selected WRAM-address transitions from SNESRecomp/snesref JSONL traces."""

from __future__ import annotations
import argparse, json
from pathlib import Path

DEFAULT_ADDRS = [0x042B,0x042F,0x0DFD,0x0F57,0x0F61,0x11CD,0x11CE,0x11F9,0x11FD]

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    ap.add_argument("--addr", action="append", type=lambda x:int(x,0))
    ap.add_argument("--from-frame", dest="from_frame", type=int, default=0)
    ap.add_argument("--to-frame", dest="to_frame", type=int, default=2**31-1)
    ap.add_argument("--json-out", type=Path)
    args=ap.parse_args()
    wanted=set(args.addr or DEFAULT_ADDRS)
    events=[]
    with args.trace.open(encoding="utf-8") as fh:
        for raw in fh:
            row=json.loads(raw)
            frame=int(row["f"])
            addr=int(row["adr"],16)
            if args.from_frame <= frame <= args.to_frame and addr in wanted:
                events.append({
                    "frame":frame,"addr":f"0x{addr:04X}",
                    "old":int(row["old"],16),"val":int(row["val"],16)
                })
    result={"trace":str(args.trace),"from_frame":args.from_frame,"to_frame":args.to_frame,
            "addresses":[f"0x{x:04X}" for x in sorted(wanted)],"events":events}
    print(json.dumps(result,indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
