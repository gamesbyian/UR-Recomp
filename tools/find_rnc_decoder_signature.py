#!/usr/bin/env python3
"""Search ROMs for opcode signatures derived from the preserved 1992 SNES RNC_1.S."""
from pathlib import Path

ROMS={
 "usa-retail":Path("reference/roms/retail/Uniracers_USA.sfc"),
 "europe-retail":Path("reference/roms/retail/Unirally_Europe.sfc"),
 "legacy-beta":Path("reference/roms/prototypes/Uniracers_Beta_legacy.sfc"),
 "pal-prototype":Path("reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"),
}
OUT=Path("analysis/generated/rnc-decoder-signature-search.md")

# None is a wildcard. These signatures intentionally use instruction structure,
# not buffer addresses, which were integration-time equates in RNC_1.S.
PATTERNS={
 "entry-loose":[0xC2,0x39,0xA3,0x06,None,None,0xA3,0x08,None,None,0xA3,0x0A,None,None,0xA3,0x04,0x8B,0xEB,0x48,0xAB,0xAB],
 "entry-dp-sta":[0xC2,0x39,0xA3,0x06,0x85,None,0xA3,0x08,0x85,None,0xA3,0x0A,0x85,None,0xA3,0x04,0x8B,0xEB,0x48,0xAB,0xAB],
 # MAKEHUFF begins STY TEMP4; LDA #5; JSR GTBITS; BEQ...
 "makehuff-shape":[0x84,None,0xA9,0x05,0x00,0x20,None,None,0xF0,None],
}

def find(data,pat):
    n=len(pat); out=[]
    for i in range(len(data)-n+1):
        if all(p is None or data[i+j]==p for j,p in enumerate(pat)):
            out.append(i)
    return out

def snes_lorom(off):
    bank=off//0x8000
    addr=0x8000+(off%0x8000)
    return f"{bank:02X}:{addr:04X}"

def main():
    lines=["# RNC1 Decoder Signature Search","",
           "Mechanical search for opcode shapes derived from the preserved period `SOURCE/SUPERNES/RNC_1.S`. A hit is a candidate until surrounding code/control flow is checked.",""]
    allhits={}
    for name,path in ROMS.items():
        data=path.read_bytes(); allhits[name]={}
        lines += [f"## {name}",""]
        for pname,pat in PATTERNS.items():
            hits=find(data,pat); allhits[name][pname]=hits
            rendered=", ".join(f"`0x{x:06X}` (LoROM {snes_lorom(x)})" for x in hits) or "none"
            lines.append(f"- {pname}: {rendered}")
        lines.append("")
    lines += ["## Cross-build exact bytes around candidate entry hits",""]
    offsets=sorted(set(x for d in allhits.values() for x in d["entry-loose"]))
    for off in offsets:
        lines.append(f"### ROM offset `0x{off:06X}`")
        lines.append("")
        for name,path in ROMS.items():
            data=path.read_bytes()
            if off < len(data):
                chunk=data[max(0,off-16):min(len(data),off+96)]
                lines.append(f"- {name}: `{chunk.hex(' ')}`")
        lines.append("")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(OUT)

if __name__=="__main__": main()
