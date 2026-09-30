#!/usr/bin/env python3
"""Decode the low-ROM course-corpus selector candidate around 00:9D34."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECOMPILER=ROOT/"snesrecomp"/"recompiler"
V2=RECOMPILER/"v2"
sys.path.insert(0,str(RECOMPILER))
sys.path.insert(0,str(V2))
from decoder import decode_function  # type: ignore  # noqa: E402

LANDMARK=0x009D34
CANDIDATE_STARTS=(0x9CF0,0x9CF4,0x9D00,0x9D10,0x9D1D,0x9D20,0x9D2A)

def fmt(di):
    pc=di.key.pc
    return f"$\{(pc>>16)&0xff:02X}:\{pc&0xffff:04X} [M=\{di.key.m} X=\{di.key.x}] \{di.insn.mnem:<5} \{di.insn._fmt()}"

def find_calls(rom:bytes, bank:int, pc:int):
    pats=[
        ("JSR",bytes((0x20,pc&0xff,(pc>>8)&0xff))),
        ("JSL",bytes((0x22,pc&0xff,(pc>>8)&0xff,bank))),
        ("JSL-mirror",bytes((0x22,pc&0xff,(pc>>8)&0xff,bank|0x80))),
    ]
    out=[]
    for kind,pat in pats:
        pos=0
        while True:
            off=rom.find(pat,pos)
            if off<0: break
            sb=off//0x8000
            sa=0x8000+(off%0x8000)
            if kind=="JSR" and sb!=bank:
                pos=off+1
                continue
            out.append({"kind":kind,"rom_offset":off,"source_cpu":f"\{sb:02X}:\{sa:04X}"})
            pos=off+1
    return sorted(out,key=lambda x:x["rom_offset"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path,nargs="?",default=Path("reference/roms/retail/Uniracers_USA.sfc"))
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    results=[]
    for start in CANDIDATE_STARTS:
        for m in (0,1):
            for x in (0,1):
                try:
                    graph=decode_function(rom,bank=0,start=start,entry_m=m,entry_x=x)
                except Exception as exc:
                    results.append({"start":f"00:\{start:04X}","m":m,"x":x,"error":str(exc),"covers_landmark":False})
                    continue
                rows=sorted(graph.insns.values(),key=lambda d:(d.key.pc,d.key.m,d.key.x))
                covers=[d for d in rows if (d.key.pc&0xffffff)==LANDMARK]
                near=[d for d in rows if 0x009CF0 <= (d.key.pc&0xffffff) <= 0x009D90]
                results.append({
                    "start":f"00:\{start:04X}","m":m,"x":x,"error":None,
                    "decoded_states":len(rows),"covers_landmark":bool(covers),
                    "calls_to_root":find_calls(rom,0,start),
                    "near_landmark":[fmt(d) for d in near],
                })
    good=[r for r in results if r.get("covers_landmark")]
    report={"schema_version":1,"landmark":"00:9D34","candidate_starts":[f"00:\{x:04X}" for x in CANDIDATE_STARTS],"covering_graphs":good,"all_attempts":results}
    print(json.dumps(report,indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
