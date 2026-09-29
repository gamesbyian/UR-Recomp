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
 # Longer MAKEHUFF prologue from RNC_1.S:
 # STY TEMP4; LDA #5; JSR GTBITS; BEQ...; STA TEMP1; STA TEMP2;
 # LDY #0; PHY; LDA #4; JSR GTBITS; PLY; STA [WRKBUF],Y;
 # INY; INY; DEC TEMP2; BNE...
 "makehuff-prologue":[
   0x84,None,0xA9,0x05,0x00,0x20,None,None,0xF0,None,
   0x85,None,0x85,None,0xA0,0x00,0x00,0x5A,
   0xA9,0x04,0x00,0x20,None,None,0x7A,0x97,None,
   0xC8,0xC8,0xC6,None,0xD0,None
 ],
 # MAKEHUFF tail:
 # INY; INY; DEX; BNE MAKEHUFF4; LSR HUFBSE; INC BITLEN;
 # CMP #16; BNE MAKEHUFF3; RTS
 "makehuff-tail":[
   0xC8,0xC8,0xCA,0xD0,None,0x46,None,0xE6,None,
   0xC9,0x10,0x00,0xD0,None,0x60
 ],
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
    lines += ["## Preserved RNC routine bounds",""]
    tail_len=len(PATTERNS["makehuff-tail"])
    for name,path in ROMS.items():
        pro=allhits[name]["makehuff-prologue"]
        tail=allhits[name]["makehuff-tail"]
        if len(pro)==1 and len(tail)==1 and tail[0] >= pro[0]:
            end=tail[0]+tail_len
            entry=allhits[name]["entry-loose"][0] if allhits[name]["entry-loose"] else None
            rel=(end-entry) if entry is not None else None
            lines.append(
                f"- {name}: MAKEHUFF \`0x{pro[0]:06X}\`..\`0x{end-1:06X}\` "
                f"(tail RTS at \`0x{end-1:06X}\`"
                + (f", RNC entry-relative end +\`0x{rel:X}\`" if rel is not None else "")
                + ")."
            )
        else:
            lines.append(f"- {name}: routine bounds unresolved (prologue hits={pro}, tail hits={tail}).")
    lines.append("")
    lines += ["## Traced writer-site context","",
              "Dynamic trace run 36517696016 identified USA interpreter attribution-scope entries 01:BA96 and 01:BB73. "
              "For the other builds, contexts below use the unpacker-entry displacement so structurally corresponding code can be compared without assuming absolute addresses.",""]
    usa_entry=allhits["usa-retail"]["entry-loose"][0]
    traced={"byte11-mutation-scope":0x00BA96,"payload-install-scope":0x00BB73}
    for label,usa_off in traced.items():
        delta=usa_off-usa_entry
        lines += [f"### {label}: USA offset `0x{usa_off:06X}`, entry-relative +`0x{delta:X}`",""]
        for name,path in ROMS.items():
            data=path.read_bytes()
            entries=allhits[name]["entry-loose"]
            if not entries:
                lines.append(f"- {name}: no unpacker entry")
                continue
            off=entries[0]+delta
            chunk=data[max(0,off-24):min(len(data),off+48)]
            lines.append(f"- {name}: `0x{off:06X}` (LoROM {snes_lorom(off)}): `{chunk.hex(' ')}`")
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
