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
SEEDS=("83:F0BB","83:F2BB","82:ACA5","82:D197")

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

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    refs=references(rom)
    ctx=decoded_contexts(rom,refs)
    report={"schema_version":1,"targets":{k:f"0x{v:04X}" for k,v in TARGETS.items()},"references":refs,"contexts":ctx}
    md=["# Racer staging-array executable references",""]
    for name,target in TARGETS.items():
        md += [f"## {name} (\`0x{target:04X}\`)","",f"Executable references: **{len(refs[name])}**.",""]
        for block in ctx[name]:
            r=block["reference"]
            md.append(f"### {r['cpu']} bytes \`{r['bytes']}\`")
            md.append("")
            for x in block["context"]:
                md.append(f"    {x['cpu']}  {x['text']}")
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
