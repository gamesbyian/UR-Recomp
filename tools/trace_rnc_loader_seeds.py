#!/usr/bin/env python3
"""Trace the RNC wrapper and base-stream reference in the canonical USA ROM."""
from pathlib import Path

ROM=Path("reference/roms/retail/Uniracers_USA.sfc")
OUT=Path("analysis/generated/rnc-loader-trace-seeds.md")

def find_all(data,needle):
    out=[];p=0
    while True:
        p=data.find(needle,p)
        if p<0:return out
        out.append(p);p+=1

def lorom(off):
    return off//0x8000,0x8000+(off%0x8000)

def label(off):
    b,a=lorom(off); return f"`0x{off:06X}` (LoROM {b:02X}:{a:04X})"

def context(data,off,before=48,after=96):
    s=max(0,off-before); e=min(len(data),off+after)
    return s,data[s:e].hex(" ")

def main():
    data=ROM.read_bytes()
    unpack=0x00B8F1
    jsl_call=0x013322
    wrapper=0x013320
    wb,wa=lorom(wrapper)

    lines=["# RNC Loader Trace Seeds","",
           "Canonical USA ROM only. This report identifies raw code/data references useful for the next disassembly/trace pass; semantic labels beyond the already identified RNC unpacker remain provisional.","",
           f"## Tiny wrapper around RNC1_Unpack","",
           f"- wrapper candidate starts at {label(wrapper)}.",
           f"- direct JSL to the identified unpacker occurs at {label(jsl_call)}.",
           ""]
    s,h=context(data,wrapper,64,128)
    lines += [f"Bytes from {label(s)}:", "", f"`{h}`", ""]

    lines += ["### References to wrapper address", ""]
    refs=[]
    for bank in {wb,wb|0x80}:
        jsl=bytes((0x22,wa&0xff,(wa>>8)&0xff,bank))
        jsr=bytes((0x20,wa&0xff,(wa>>8)&0xff))
        refs += [("JSL",x,bank) for x in find_all(data,jsl)]
        # JSR is only meaningful when caller executes in same bank; list as raw candidates.
        refs += [("JSR-word",x,None) for x in find_all(data,jsr)]
    for kind,off,bank in sorted(set(refs), key=lambda x:x[1]):
        s,h=context(data,off,48,80)
        suffix=f" target-bank {bank:02X}" if bank is not None else ""
        lines.append(f"- {kind} at {label(off)}{suffix}; context from {label(s)}: `{h}`")
    if not refs: lines.append("- none")

    base_ptrs=[bytes((0x00,0x80,0x18)),bytes((0x00,0x80,0x98))]
    lines += ["","## References to RNC corpus base 18:8000 / 98:8000",""]
    hits=[]
    for ptr in base_ptrs:
        for off in find_all(data,ptr):
            if off==0x0C0000: continue
            hits.append((off,ptr[2]))
    for off,bank in sorted(set(hits)):
        s,h=context(data,off,64,128)
        lines.append(f"- pointer bytes for bank {bank:02X} at {label(off)}; context from {label(s)}: `{h}`")

    lines += ["","## Nearby 24-bit ROM-address tables in low ROM","",
              "Searches low ROM for runs of >=3 consecutive little-endian LoROM pointers into file region 0x0C0000-0x0FC000. This can expose an index even when pointers do not land exactly on RNC headers.",""]
    ptrs=[]
    for off in range(0,min(0x0C0000,len(data))-2):
        a=data[off]|(data[off+1]<<8); b=data[off+2]&0x7f
        if a<0x8000: continue
        fileoff=b*0x8000+(a-0x8000)
        if 0x0C0000<=fileoff<0x0FC000:
            ptrs.append((off,fileoff,data[off+2]))
    # detect entries spaced every 3 bytes
    pmap={o:(fo,b) for o,fo,b in ptrs}
    seen=set()
    for off in sorted(pmap):
        if off in seen or off-3 in pmap: continue
        run=[];cur=off
        while cur in pmap:
            run.append((cur,*pmap[cur]));seen.add(cur);cur+=3
        if len(run)>=3:
            lines.append(f"- run length {len(run)} starting {label(off)}")
            for ro,fo,b in run[:64]:
                lines.append(f"  - +0x{ro-off:04X}: bank byte {b:02X} -> file `0x{fo:06X}`")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(OUT)

if __name__=="__main__": main()
