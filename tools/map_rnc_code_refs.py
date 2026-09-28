#!/usr/bin/env python3
"""Map calls to the identified RNC1 unpacker and references to packed stream starts."""
from pathlib import Path

ROMS={
    "usa-retail": (Path("reference/roms/retail/Uniracers_USA.sfc"), 0x00B8F1),
    "europe-retail": (Path("reference/roms/retail/Unirally_Europe.sfc"), 0x00B8E2),
    "legacy-beta": (Path("reference/roms/prototypes/Uniracers_Beta_legacy.sfc"), 0x00B8F1),
    "pal-prototype": (Path("reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"), 0x00B8D1),
}
OUT=Path("analysis/generated/rnc-code-reference-map.md")

def lorom_addr(off):
    bank=off//0x8000
    addr=0x8000+(off%0x8000)
    return bank,addr

def find_all(data,needle):
    out=[]; p=0
    while True:
        p=data.find(needle,p)
        if p<0:return out
        out.append(p); p+=1

def rnc_offsets(data):
    out=[]; p=0
    while True:
        p=data.find(b"RNC\x01",p)
        if p<0:return out
        if p+18<=len(data):
            packed=int.from_bytes(data[p+8:p+12],"big")
            unpacked=int.from_bytes(data[p+4:p+8],"big")
            if packed and unpacked and p+18+packed<=len(data):
                out.append(p)
        p+=1

def addr_variants(off):
    bank,addr=lorom_addr(off)
    vals=[]
    for b in {bank,bank|0x80}:
        vals.append((b,addr,bytes((addr&0xff,(addr>>8)&0xff,b))))
    return vals

def fmt_off(off):
    b,a=lorom_addr(off)
    return f"`0x{off:06X}` (LoROM {b:02X}:{a:04X})"

def main():
    lines=["# RNC Decoder Calls and Packed-Stream References","",
           "Generated mechanically from the identified RNC1 entry and the 45 validated stream starts. CPU-bank mirrors are searched explicitly. A raw pointer hit is evidence of byte-level reference only until surrounding structure is classified.",""]
    for name,(path,entry) in ROMS.items():
        data=path.read_bytes()
        eb,ea=lorom_addr(entry)
        lines += [f"## {name}","",f"Identified unpacker entry: {fmt_off(entry)}.","","### Direct JSL callers",""]
        calls=[]
        for bank in {eb,eb|0x80}:
            needle=bytes((0x22,ea&0xff,(ea>>8)&0xff,bank))
            calls += [(x,bank) for x in find_all(data,needle)]
        calls=sorted(set(calls))
        if calls:
            for off,bank in calls:
                context=data[max(0,off-24):min(len(data),off+28)]
                lines.append(f"- {fmt_off(off)}, encoded target bank `{bank:02X}`: `{context.hex(' ')}`")
        else:
            lines.append("- none")
        lines += ["","### Packed-stream pointer references","",
                  "| Stream | Stream offset | 24-bit pointer hits | 16-bit address-word hits in likely pointer region |",
                  "|---:|---:|---|---|"]
        for idx,soff in enumerate(rnc_offsets(data),1):
            sb,sa=lorom_addr(soff)
            hits=[]
            for bank,addr,ptr in addr_variants(soff):
                for h in find_all(data,ptr):
                    if h != soff:
                        hits.append((h,bank))
            # 16-bit low word alone is noisy. Restrict listing to pre-RNC area and only count.
            word=bytes((sa&0xff,(sa>>8)&0xff))
            wh=[h for h in find_all(data[:0x0C0000],word)]
            hs=", ".join(f"{fmt_off(h)}→{bank:02X}:{sa:04X}" for h,bank in sorted(set(hits))) or "none"
            lines.append(f"| {idx} | `0x{soff:06X}` | {hs} | {len(wh)} |")
        lines.append("")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(OUT)

if __name__=="__main__":main()
