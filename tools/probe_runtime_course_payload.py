#!/usr/bin/env python3
"""Match decoded RNC payloads against the live course buffer in a WRAM dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1

WRAM_COURSE_BASE = 0x10000  # 7F:0000 in the 128 KiB WRAM dump

def u16le(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off+2], "little")

def compare(decoded: bytes, live: bytes, limit: int) -> dict:
    n=min(len(decoded),len(live))
    diffs=[i for i,(a,b) in enumerate(zip(decoded[:n],live[:n])) if a!=b]
    prefix=0
    while prefix<n and decoded[prefix]==live[prefix]:
        prefix+=1
    return {
        "decoded_size":len(decoded),
        "live_compared":n,
        "equal_bytes":n-len(diffs),
        "equal_fraction": (n-len(diffs))/n if n else 0.0,
        "common_prefix":prefix,
        "diff_count":len(diffs),
        "first_differences":[
            {
                "offset":f"0x{i:04X}",
                "decoded":f"0x{decoded[i]:02X}",
                "live":f"0x{live[i]:02X}",
            }
            for i in diffs[:limit]
        ],
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("wram",type=Path)
    ap.add_argument("--limit",type=int,default=64)
    ap.add_argument("--focus-stream",type=int)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()

    rom=args.rom.read_bytes()
    wram=args.wram.read_bytes()
    if len(wram)<0x20000:
        raise SystemExit(f"expected 128 KiB WRAM dump, got {len(wram)} bytes")
    live=wram[WRAM_COURSE_BASE:]

    results=[]
    for index,(off,packed,h) in enumerate(find_streams(rom),1):
        decoded=unpack_method1(packed)
        result=compare(decoded,live,args.limit)
        result.update({
            "stream":index,
            "rom_offset":f"0x{off:06X}",
            "header_first_16":decoded[:16].hex(" "),
            "pair1":[u16le(decoded,3),u16le(decoded,5)],
            "pair2":[u16le(decoded,7),u16le(decoded,9)],
        })
        results.append(result)

    results.sort(key=lambda x:(x["equal_fraction"],x["common_prefix"]),reverse=True)
    best=results[0]
    racer_state={
        "slot1_x":u16le(wram,0x0411),
        "slot1_y":u16le(wram,0x0415),
        "slot2_x":u16le(wram,0x0413),
        "slot2_y":u16le(wram,0x0417),
    }
    by_stream={x["stream"]:x for x in results}
    focus=by_stream.get(args.focus_stream)
    report={
        "wram_course_base":"7F:0000",
        "best_match":best,
        "focus_stream":focus,
        "top_matches":results[:5],
        "runtime_racer_state":racer_state,
    }

    print(
        f"best stream #{best['stream']} @ {best['rom_offset']}: "
        f"equal={best['equal_bytes']}/{best['live_compared']} "
        f"({best['equal_fraction']:.6f}) prefix={best['common_prefix']} "
        f"diffs={best['diff_count']}"
    )
    print(f"header: {best['header_first_16']}")
    if focus is not None:
        print(
            f"focus stream #{args.focus_stream}: "
            f"equal={focus['equal_bytes']}/{focus['live_compared']} "
            f"({focus['equal_fraction']:.6f}) prefix={focus['common_prefix']} "
            f"diffs={focus['diff_count']} live_b11=0x{live[11]:02X}"
        )
    print(f"pair1={best['pair1']} pair2={best['pair2']}")
    print(
        "runtime racers: "
        f"slot1=({racer_state['slot1_x']},{racer_state['slot1_y']}) "
        f"slot2=({racer_state['slot2_x']},{racer_state['slot2_y']})"
    )
    if best["pair1"][0]:
        print(
            "x-scale checks: "
            f"pair1.x*16={best['pair1'][0]*16} "
            f"pair2.x*16={best['pair2'][0]*16}"
        )
    print("first differences:")
    for d in best["first_differences"]:
        print(f"  {d['offset']}: decoded={d['decoded']} live={d['live']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
