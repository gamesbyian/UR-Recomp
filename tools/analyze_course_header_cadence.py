#!/usr/bin/env python3
"""Probe the first 16 decoded bytes of each USA RNC payload against 5-track tour cadence."""
from pathlib import Path
from collections import defaultdict
from rnc_method1 import parse_header, unpack_method1

ROM=Path("reference/roms/retail/Uniracers_USA.sfc")
OUT=Path("analysis/generated/course-header-cadence.md")

def streams(data):
    out=[];p=0
    while True:
        p=data.find(b"RNC\x01",p)
        if p<0:return out
        h=parse_header(data[p:p+18]); end=p+18+h.packed_size
        if h.packed_size and h.unpacked_size and end<=len(data):
            out.append(unpack_method1(data[p:end]))
        p+=1

def u16le(d,o): return d[o] | (d[o+1]<<8)

def main():
    ss=streams(ROM.read_bytes())
    lines=["# Decoded Course-Header Cadence Probe","",
           "Mechanical probe of the first 16 unpacked bytes in the 45 USA RNC streams. The five-position grouping is tested because the shipped game organizes each tour as Race, Circuit, Stunt, Race, Circuit; semantic field names are intentionally not assigned yet.","",
           "| # | Tour slot | First 16 bytes | b2 | LE16@3 | LE16@5 | LE16@7 | LE16@9 | b11 | b12 | b13 | b14 | b15 |",
           "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    vals=defaultdict(list)
    for i,d in enumerate(ss,1):
        slot=((i-1)%5)+1
        for off in range(16): vals[(slot,off)].append(d[off])
        h=d[:16]
        lines.append(f"| {i} | {slot} | `{h.hex(' ')}` | {d[2]:02X} | {u16le(d,3)} | {u16le(d,5)} | {u16le(d,7)} | {u16le(d,9)} | {d[11]:02X} | {d[12]:02X} | {d[13]:02X} | {d[14]:02X} | {d[15]:02X} |")
    lines += ["","## Slot-discriminating bytes","",
              "For each header byte, this lists the distinct values observed in each of the five recurring tour positions.",""]
    for off in range(16):
        groups=[]
        for slot in range(1,6):
            groups.append(f"{slot}:"+"/".join(f"{v:02X}" for v in sorted(set(vals[(slot,off)]))))
        lines.append(f"- byte {off}: " + "; ".join(groups))
    stunt=[ss[i-1][2] for i in range(3,46,5)]
    non=[d[2] for i,d in enumerate(ss,1) if ((i-1)%5)+1 != 3]
    lines += ["","## Exact cadence test","",
              f"- tour-slot-3 streams: {len(stunt)}; byte 2 values: {sorted(set(stunt))}.",
              f"- all other streams: {len(non)}; byte 2 values: {sorted(set(non))}.",
              f"- condition `byte[2] == 0x2D` selects {sum(d[2]==0x2d for d in ss)}/45 streams, at ordinals: " + ", ".join(str(i) for i,d in enumerate(ss,1) if d[2]==0x2d) + ".",
              "",
              "This cadence is a structural observation. Interpreting byte 2 as a track-type field, timer, score-mode flag, or another stunt-specific quantity requires a runtime or cross-reference test.",
              ""]
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text("\n".join(lines),encoding="utf-8"); print(OUT)
if __name__=="__main__":main()
