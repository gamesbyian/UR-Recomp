#!/usr/bin/env python3
"""Find executable references to racer presentation staging arrays."""

from __future__ import annotations
import argparse, json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))

from compare_europe_usa_snes2asm_homologs import cpu_to_offset, offset_to_cpu, seed_entries, trace

TARGETS={
    "piece_source_stage":0x1645,
    "piece_selector_stage":0x15A1,
    "piece_position_stage":0x16E9,
}
SEEDS=("83:F0BB","83:F2BB","82:ACA5","82:D197","82:B8E3","82:C53E")
RAW_OPS={
    0xAD:"LDA abs",0xBD:"LDA abs,X",0xB9:"LDA abs,Y",
    0x8D:"STA abs",0x9D:"STA abs,X",0x99:"STA abs,Y",
    0xAE:"LDX abs",0xBE:"LDX abs,Y",0x8E:"STX abs",
    0xAC:"LDY abs",0xBC:"LDY abs,X",0x8C:"STY abs",
    0x6D:"ADC abs",0x7D:"ADC abs,X",0x79:"ADC abs,Y",
    0xED:"SBC abs",0xFD:"SBC abs,X",0xF9:"SBC abs,Y",
    0xCD:"CMP abs",0xDD:"CMP abs,X",0xD9:"CMP abs,Y",
    0x2D:"AND abs",0x3D:"AND abs,X",0x39:"AND abs,Y",
    0x0D:"ORA abs",0x1D:"ORA abs,X",0x19:"ORA abs,Y",
    0x4D:"EOR abs",0x5D:"EOR abs,X",0x59:"EOR abs,Y",
    0x2C:"BIT abs",
    0xAF:"LDA long",0xBF:"LDA long,X",0x8F:"STA long",0x9F:"STA long,X",
}

def references(rom:bytes)->dict:
    d=trace(rom)
    seed_entries(d,[cpu_to_offset(x) for x in SEEDS])
    out={k:[] for k in TARGETS}
    for off,status in enumerate(d.code_map):
        if not (status & d.OP_CODE):
            continue
        d.flags=status & 0x30
        op=rom[off]
        try:
            size=d.opSize(op)
        except Exception:
            continue
        if size < 3 or off+size>len(rom):
            continue
        # Absolute/absolute-indexed instructions use a 16-bit operand at +1.
        operand=rom[off+1] | (rom[off+2]<<8)
        for name,target in TARGETS.items():
            if operand==target:
                out[name].append({
                    "cpu":offset_to_cpu(off),
                    "opcode":f"0x{op:02X}",
                    "size":size,
                    "bytes":rom[off:off+size].hex(" "),
                    "mx_flags":status & 0x30,
                })
    return out


def raw_references(rom:bytes, d)->dict:
    out={k:[] for k in TARGETS}
    for name,target in TARGETS.items():
        lo=target&0xff; hi=(target>>8)&0xff
        for operand in range(1,len(rom)-2):
            if rom[operand]!=lo or rom[operand+1]!=hi:
                continue
            opoff=operand-1; op=rom[opoff]
            if op not in RAW_OPS:
                continue
            long_mode=op in (0xAF,0xBF,0x8F,0x9F)
            if long_mode and (operand+2>=len(rom) or rom[operand+2]!=0x7E):
                continue
            status=d.code_map[opoff] if opoff<len(d.code_map) else 0
            out[name].append({
                "cpu":offset_to_cpu(opoff),
                "opcode":f"0x{op:02X}",
                "mnemonic":RAW_OPS[op],
                "bytes":rom[opoff:opoff+(4 if long_mode else 3)].hex(" "),
                "snes2asm_executable":bool(status & d.OP_CODE),
                "snes2asm_role":status,
            })
    return out

def decoded_contexts(rom:bytes,refs:dict)->dict:
    d=trace(rom)
    seed_entries(d,[cpu_to_offset(x) for x in SEEDS])
    contexts={}
    for name,rows in refs.items():
        contexts[name]=[]
        for row in rows:
            off=cpu_to_offset(row["cpu"])
            start=max((off//0x8000)*0x8000,off-24)
            end=min(((off//0x8000)+1)*0x8000,off+40)
            d.decode(start,end)
            ins=[]
            for q,obj in d.code.item_range(start,end):
                ins.append({"cpu":offset_to_cpu(q),"text":obj.text()})
            contexts[name].append({"reference":row,"context":ins})
    return contexts


def consumer_clusters(rom:bytes)->list[dict]:
    d=trace(rom)
    seed_entries(d,[cpu_to_offset(x) for x in SEEDS])
    clusters=[]
    for start_cpu,end_cpu in (("82:B8C0","82:B940"),("82:C51B","82:C59B")):
        start=cpu_to_offset(start_cpu); end=cpu_to_offset(end_cpu)+1
        d.decode(start,end)
        rows=[]
        for off,ins in d.code.item_range(start,end):
            rows.append({"cpu":offset_to_cpu(off),"text":ins.text(),"bytes":rom[off:off+d.opSize(rom[off])].hex(" ")})
        clusters.append({"start":start_cpu,"end":end_cpu,"rows":rows})
    return clusters

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    refs=references(rom)
    d=trace(rom); seed_entries(d,[cpu_to_offset(x) for x in SEEDS])
    raw=raw_references(rom,d)
    ctx=decoded_contexts(rom,refs)
    clusters=consumer_clusters(rom)
    report={"schema_version":3,"targets":{k:f"0x{v:04X}" for k,v in TARGETS.items()},"references":refs,"raw_operand_candidates":raw,"contexts":ctx,"consumer_clusters":clusters}
    md=["# Racer staging-array executable references",""]
    for name,target in TARGETS.items():
        md += [f"## {name} (\`0x{target:04X}\`)","",f"Executable references: **{len(refs[name])}**.",f"Raw plausible operand references: **{len(raw[name])}**.",""]
        for rr in raw[name]:
            md.append(f"- raw {rr['cpu']} {rr['mnemonic']} bytes \`{rr['bytes']}\` executable={rr['snes2asm_executable']}")
        md.append("")
        for block in ctx[name]:
            r=block["reference"]
            md.append(f"### {r['cpu']} bytes \`{r['bytes']}\`")
            md.append("")
            for x in block["context"]:
                md.append(f"    {x['cpu']}  {x['text']}")
            md.append("")
    md += ["## Candidate consumer clusters",""]
    for cl in clusters:
        md.append(f"### {cl['start']}..{cl['end']}")
        md.append("")
        for row in cl["rows"]:
            md.append(f"    {row['cpu']}  {row['text']}    ; {row['bytes']}")
        md.append("")
    text="\n".join(md)+"\n"
    js=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(js)
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True);args.md_out.write_text(text)
    print(text)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
