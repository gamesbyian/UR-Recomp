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
    dim_pairs=[]
    for i,d in enumerate(ss,1):
        w=d[13] or 256
        h=d[14] or 256
        dim_pairs.append((i,w,h,w*h))
    products=sorted(set(p for _,_,_,p in dim_pairs))
    end_fields=[(i,u16le(d,11),len(d),len(d)-u16le(d,11)) for i,d in enumerate(ss,1)]
    end_deltas=sorted(set(delta for _,_,_,delta in end_fields))
    trailing_after=[(i,v,n,n-(v+1)) for i,v,n,_ in end_fields]
    trailing_lengths=sorted(set(t for _,_,_,t in trailing_after))
    whole_1024=[
        i for i,v,_,_ in end_fields
        if ((v + 1) - 16) >= 0 and ((v + 1) - 16) % 1024 == 0
    ]
    lines += ["","## Near-end aligned cursor relationship","",
              "Treating bytes 11–12 as little-endian places the field near decoded EOF and reveals a stronger corpus-wide alignment property.","",
              f"- `(LE16@11 + 1) % 16 == 0`: {sum((v+1)%16==0 for _,v,_,_ in end_fields)}/45 streams.",
              f"- bytes remaining after the cursor (`decoded_size - (LE16@11 + 1)`): {trailing_lengths}.",
              f"- minimum/maximum bytes after cursor: {min(trailing_lengths)}..{max(trailing_lengths)}.",
              f"- stronger candidate `LE16@11 + 1 = 16 + N×1024`: {len(whole_1024)}/45 streams (ordinals {whole_1024}).",
              "",
              "The 16-byte alignment is therefore the corpus-wide fact. The tempting interpretation as a 16-byte header followed by only whole 1024-byte planes is rejected; the separate 1024-unit dimension invariant should not be conflated with this cursor boundary.",
              "",
              "Dragster has `LE16@11 = 0x840F`, so the next byte is the 16-byte-aligned offset `0x8410`; exactly seven bytes remain through decoded EOF at `0x8416`. The observed runtime seven-step increment walks the field from `0x840F` to `0x8416`, consuming that entire trailing region and stopping on the final valid byte. This motivates a **pre-trailer cursor** hypothesis: the field may be initialized to the inclusive end of an aligned main-data region and advanced through a variable trailing structure during setup. A second-course runtime capture is required before promoting that interpretation.",
              "",
              "## Dimension-pair invariant","",
              "Bytes 13 and 14 form an unusually strict power-of-two-style pair. Treating encoded byte value `0x00` as 256, every one of the 45 streams satisfies `dim13 × dim14 = 1024`.","",
              f"- distinct decoded pairs: " + ", ".join(f"`{w}×{h}`" for w,h in sorted(set((w,h) for _,w,h,_ in dim_pairs))) + ".",
              f"- distinct products: {products}.",
              f"- invariant holds: {all(p==1024 for _,_,_,p in dim_pairs)} (45/45).",
              "",
              "This strongly supports bytes 13/14 as complementary course-layout dimensions or strides over a fixed 1024-unit plane/table. It does **not** yet establish the unit (tile, block, column, lookup entry, etc.). The zero-as-256 interpretation is structural and should be runtime-validated, especially on the 256×4 and 4×256 cases.",
              "",
              "## Exact cadence test","",
              f"- tour-slot-3 streams: {len(stunt)}; byte 2 values: {sorted(set(stunt))}.",
              f"- all other streams: {len(non)}; byte 2 values: {sorted(set(non))}.",
              f"- condition `byte[2] == 0x2D` selects {sum(d[2]==0x2d for d in ss)}/45 streams, at ordinals: " + ", ".join(str(i) for i,d in enumerate(ss,1) if d[2]==0x2d) + ".",
              "",
              "This cadence is a structural observation. Interpreting byte 2 as a track-type field, timer, score-mode flag, or another stunt-specific quantity requires a runtime or cross-reference test.",
              ""]
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text("\n".join(lines),encoding="utf-8"); print(OUT)
if __name__=="__main__":main()
