#!/usr/bin/env python3
"""Run bounded da65 second-witness probes on PAL retail/prototype regions.

Processor-width assumptions are deliberately independent of snes2asm:
- reset/init uses architectural reset state plus explicit XCE/SEP/REP transitions;
- A0DA uses the local REP #$30 transition;
- D1D7 contains no M/X-sensitive immediate widths in the selected helper.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
USA=ROOT/"reference/roms/retail/Uniracers_USA.sfc"
ROMS={
 "europe-retail": ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "pal-prototype-1994-11-29": ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
}

# Inclusive SNES bank-00 ranges with independently justified da65 modes.
PROBES=[
 {"id":"reset-init","start":0x91D1,"end":0x933B,"ranges":[
   (0x91D1,0x91D4,"MX","architectural reset state; XCE/SEP begins here"),
   (0x91D5,0x9317,"Mx","SEP #$20 => M8; REP #$10 => X16"),
   (0x9318,0x932E,"mx","local REP #$20 with X already 16"),
   (0x932F,0x933B,"Mx","local SEP #$20 with X still 16"),
 ]},
 {"id":"ppu-init-16bit","start":0xA0DA,"end":0xA11E,"ranges":[
   (0xA0DA,0xA11E,"mx","local REP #$30 establishes M16/X16"),
 ]},
 {"id":"joypad-helper","start":0xD1D7,"end":0xD1E8,"ranges":[
   (0xD1D7,0xD1E8,"Mx","selected instructions have no M/X-sensitive immediate width"),
 ]},
]

LINE_RE=re.compile(r'^\s*([A-Za-z]{2,5})\s*(.*?)(?:\s*;.*)?$')

def file_off(addr:int)->int:
    return addr-0x8000

def info_text(probe:dict, shift:int=0)->str:
    lines=['GLOBAL { CPU "65816"; STARTADDR $8000; };','SEGMENT { START $8000; END $FFFF; NAME "bank_00"; };']
    for a,b,mode,why in probe['ranges']:
        a += shift
        b += shift
        lines.append(f'RANGE {{ START ${a:04X}; END ${b:04X}; TYPE CODE; ADDRMODE "{mode}"; COMMENT "{why}"; }};')
    return '\n'.join(lines)+'\n'

def best_shift(source:bytes, target:bytes, probe:dict, radius:int=128)->tuple[int,float]:
    """Align homologous code by raw-byte similarity, independently of snes2asm."""
    a=probe['start']-0x8000
    b=probe['end']-0x8000+1
    src=source[a:b]
    best=(0,-1.0)
    for shift in range(-radius,radius+1):
        pa=a+shift
        pb=pa+len(src)
        if pa < 0 or pb > len(target):
            continue
        dst=target[pa:pb]
        score=sum(x==y for x,y in zip(src,dst))/len(src)
        if score > best[1]:
            best=(shift,score)
    return best

def run_da65(exe:Path, rom:Path, probe:dict, tmp:Path, shift:int=0)->str:
    bank=rom.read_bytes()[:0x8000]
    binp=tmp/f"{rom.stem}-{probe['id']}.bin"
    inf=tmp/f"{rom.stem}-{probe['id']}.info"
    out=tmp/f"{rom.stem}-{probe['id']}.s"
    binp.write_bytes(bank)
    inf.write_text(info_text(probe,shift),encoding='utf-8')
    subprocess.run([str(exe),'--info',str(inf),'--comments','4','-o',str(out),str(binp)],check=True)
    return out.read_text(encoding='utf-8',errors='replace')

def normalized_lines(text:str,probe:dict)->list[str]:
    # Keep only emitted assembly statements in the selected address span.
    # da65 does not expose addresses on every line, so this is a representation
    # comparison, not an address oracle; exact boundaries are checked by whether
    # each bounded stream remains syntactically aligned between builds.
    out=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith(';') or s.startswith('.') or s.endswith(':'):
            continue
        m=LINE_RE.match(s)
        if m:
            out.append(' '.join(s.split()))
    return out

def instruction_shape(line:str)->str:
    body=line.split(';',1)[0].strip()
    body=re.sub(r'^[A-Za-z_][A-Za-z0-9_]*:\s*','',body)
    return body.split(None,1)[0].lower() if body else ""

def instruction_size(line:str)->int | None:
    m=re.search(r';\s*[0-9A-Fa-f]{4}\s+((?:[0-9A-Fa-f]{2}(?:\s+|$))+)',line)
    if not m:
        return None
    return len(re.findall(r'[0-9A-Fa-f]{2}',m.group(1)))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--da65',type=Path,required=True)
    ap.add_argument('--json-out',type=Path,default=ROOT/'analysis/generated/pal-da65-adjudication.json')
    ap.add_argument('--md-out',type=Path,default=ROOT/'analysis/generated/pal-da65-adjudication.md')
    args=ap.parse_args()
    report={'schema_version':1,'method':{'analyzer':'cc65 da65 65816','width_provenance':'architectural/local REP/SEP evidence independent of snes2asm'},'probes':[]}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for probe in PROBES:
            usa_bytes=USA.read_bytes()[:0x8000]
            shifts={}
            similarities={}
            for name,rom in ROMS.items():
                target=rom.read_bytes()[:0x8000]
                shifts[name],similarities[name]=best_shift(usa_bytes,target,probe)
            row={
                'id':probe['id'],
                'usa_anchor_start':f"00:{probe['start']:04X}",
                'usa_anchor_end':f"00:{probe['end']:04X}",
                'ranges':[{'start':f"00:{a:04X}",'end':f"00:{b:04X}",'addrmode':mode,'basis':why} for a,b,mode,why in probe['ranges']],
                'builds':{}
            }
            norms={}
            for name,rom in ROMS.items():
                shift=shifts[name]
                asm=run_da65(args.da65,rom,probe,tmp,shift)
                norm=normalized_lines(asm,probe)
                norms[name]=norm
                row['builds'][name]={
                    'start':f"00:{probe['start']+shift:04X}",
                    'end':f"00:{probe['end']+shift:04X}",
                    'shift_from_usa':shift,
                    'raw_similarity_to_usa':round(similarities[name],6),
                    'instruction_lines':len(norm),
                    'normalized':norm
                }
            a=norms['europe-retail']; b=norms['pal-prototype-1994-11-29']
            ashapes=[instruction_shape(x) for x in a]
            bshapes=[instruction_shape(x) for x in b]
            asizes=[instruction_size(x) for x in a]
            bsizes=[instruction_size(x) for x in b]
            row['same_instruction_count']=len(a)==len(b)
            row['exact_normalized_match']=a==b
            row['instruction_shape_match']=ashapes==bshapes
            row['instruction_size_sequence_match']=asizes==bsizes
            row['shape_mismatch_indices']=[i for i,(x,y) in enumerate(zip(ashapes,bshapes)) if x!=y]
            row['size_mismatch_indices']=[i for i,(x,y) in enumerate(zip(asizes,bsizes)) if x!=y]
            report['probes'].append(row)
    args.json_out.parent.mkdir(parents=True,exist_ok=True)
    args.json_out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    lines=['# PAL retail vs prototype: bounded da65 adjudication','', 'Width-state provenance is independent of snes2asm.','', '| Probe | USA anchor | Europe range / shift / sim | Prototype range / shift / sim | Lines E/P | Shape | Sizes | Exact |','|---|---|---|---|---:|---|---|---|']
    for p in report['probes']:
        lines.append(f"| {p['id']} | `{p['usa_anchor_start']}..{p['usa_anchor_end']}` | `{p['builds']['europe-retail']['start']}..{p['builds']['europe-retail']['end']}` / {p['builds']['europe-retail']['shift_from_usa']:+d} / {p['builds']['europe-retail']['raw_similarity_to_usa']:.3f} | `{p['builds']['pal-prototype-1994-11-29']['start']}..{p['builds']['pal-prototype-1994-11-29']['end']}` / {p['builds']['pal-prototype-1994-11-29']['shift_from_usa']:+d} / {p['builds']['pal-prototype-1994-11-29']['raw_similarity_to_usa']:.3f} | {p['builds']['europe-retail']['instruction_lines']}/{p['builds']['pal-prototype-1994-11-29']['instruction_lines']} | {p['instruction_shape_match']} | {p['instruction_size_sequence_match']} | {p['exact_normalized_match']} |")
    all_shapes=all(p['instruction_shape_match'] for p in report['probes'])
    all_sizes=all(p['instruction_size_sequence_match'] for p in report['probes'])
    lines += ['', f'Across these probes, instruction-shape agreement: **{all_shapes}**; instruction-size-sequence agreement: **{all_sizes}**.', '', 'Interpretation rule: USA recovered-code ranges provide independent M/X provenance, while raw-byte similarity independently locates each homolog in Europe and the PAL prototype. Equal da65 instruction counts plus shape/size agreement support stable boundaries despite relocation; only a remaining mismatch after homolog alignment should be escalated to Ghidra/xref inspection.', '']
    args.md_out.write_text('\n'.join(lines),encoding='utf-8')
    print(args.md_out.read_text())
    return 0

if __name__=="__main__": raise SystemExit(main())
