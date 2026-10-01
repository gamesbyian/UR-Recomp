#!/usr/bin/env python3
"""Re-score PAL retail/prototype snes2asm disagreement after homolog alignment.

The first pass compared identical file offsets. This pass locally aligns each
code-related window by raw-byte similarity before comparing snes2asm roles,
instruction starts, and M/X flags.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
SNES2ASM_ROOT=ROOT/"third_party/src/snes2asm"
if str(SNES2ASM_ROOT) not in sys.path:
    sys.path.insert(0,str(SNES2ASM_ROOT))

from snes2asm.cartridge import Cartridge
from snes2asm.disassembler import Disassembler

FIRST=ROOT/'analysis/generated/pal-retail-vs-prototype-snes2asm.json'
EUROPE=ROOT/"reference/roms/retail/Unirally_Europe.sfc"
PROTO=ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
OUT_JSON=ROOT/"analysis/generated/pal-snes2asm-homolog-alignment.json"
OUT_MD=ROOT/"analysis/generated/pal-snes2asm-homolog-alignment.md"


def trace(data:bytes)->Disassembler:
    opts=SimpleNamespace(hex=False,nolabel=True)
    cart=Cartridge({"lorom":True,"hirom":False,"fastrom":False,"slowrom":False,"empty_fill":255})
    cart.set(bytearray(data))
    d=Disassembler(cart,opts)
    d.mark_vectors(); d.find_valid_code_paths()
    return d


def role(d:Disassembler,off:int)->str:
    m=d.code_map[off]
    if m & d.OP_CODE: return 'opcode'
    if m & d.OP_PARAM: return 'operand'
    return 'unreached'


def mode(d:Disassembler,off:int)->tuple[bool,bool] | None:
    if role(d,off)!='opcode': return None
    m=d.code_map[off]
    return (not bool(m & 0x20),not bool(m & 0x10))


def best_shift(source:bytes,target:bytes,start:int,end:int,radius:int=256)->tuple[int,float]:
    src=source[start:end+1]
    best=(0,-1.0)
    for shift in range(-radius,radius+1):
        a=start+shift; b=a+len(src)
        if a<0 or b>len(target): continue
        dst=target[a:b]
        score=sum(x==y for x,y in zip(src,dst))/len(src)
        if score>best[1]: best=(shift,score)
    return best


def compare_roles(rd:Disassembler,pd:Disassembler,start:int,end:int,shift:int)->dict:
    same=Counter(); aligned=Counter()
    same_mode=0; aligned_mode=0; opcode_pairs_same=0; opcode_pairs_aligned=0
    for off in range(start,end+1):
        rr=role(rd,off)
        sr=role(pd,off)
        ar=role(pd,off+shift)
        same[f'{rr}->{sr}'] += 1
        aligned[f'{rr}->{ar}'] += 1
        if rr=='opcode' and sr=='opcode':
            opcode_pairs_same += 1
            if mode(rd,off)!=mode(pd,off): same_mode += 1
        if rr=='opcode' and ar=='opcode':
            opcode_pairs_aligned += 1
            if mode(rd,off)!=mode(pd,off+shift): aligned_mode += 1
    def disagreements(c:Counter)->int:
        return sum(v for k,v in c.items() if k.split('->')[0]!=k.split('->')[1])
    return {
        'same_offset_role_pairs':dict(same),
        'aligned_role_pairs':dict(aligned),
        'same_offset_role_disagreements':disagreements(same),
        'aligned_role_disagreements':disagreements(aligned),
        'same_offset_opcode_pairs':opcode_pairs_same,
        'aligned_opcode_pairs':opcode_pairs_aligned,
        'same_offset_mx_disagreements':same_mode,
        'aligned_mx_disagreements':aligned_mode,
    }


def build()->dict:
    first=json.loads(FIRST.read_text(encoding='utf-8'))
    retail=EUROPE.read_bytes(); proto=PROTO.read_bytes()
    rd=trace(retail); pd=trace(proto)
    rows=[]
    for w in first['windows']:
        if not w['da65_candidate']: continue
        a=w['start']; b=w['end']
        shift,sim=best_shift(retail,proto,a,b)
        metrics=compare_roles(rd,pd,a,b,shift)
        rows.append({
            'retail_start':a,'retail_end':b,
            'retail_start_cpu':w['start_cpu'],'retail_end_cpu':w['end_cpu'],
            'prototype_shift':shift,
            'prototype_start':a+shift,'prototype_end':b+shift,
            'raw_similarity_after_alignment':round(sim,6),
            'original_changed_bytes':w['changed_bytes'],
            'original_classifications':w['classifications'],
            **metrics,
        })
    rows.sort(key=lambda x:(-x['same_offset_role_disagreements'],x['retail_start']))
    totals={
        'windows':len(rows),
        'same_offset_role_disagreements':sum(x['same_offset_role_disagreements'] for x in rows),
        'aligned_role_disagreements':sum(x['aligned_role_disagreements'] for x in rows),
        'same_offset_mx_disagreements':sum(x['same_offset_mx_disagreements'] for x in rows),
        'aligned_mx_disagreements':sum(x['aligned_mx_disagreements'] for x in rows),
        'zero_role_disagreement_after_alignment':sum(x['aligned_role_disagreements']==0 for x in rows),
    }
    before=totals['same_offset_role_disagreements']
    after=totals['aligned_role_disagreements']
    totals['role_disagreement_reduction_fraction']=0 if before==0 else round((before-after)/before,6)
    return {'schema_version':1,'method':{'alignment':'local raw-byte similarity within +/-256 bytes','analyzer':'vendored snes2asm','note':'alignment is independent of snes2asm role classification'},'totals':totals,'windows':rows}


def render(r:dict)->str:
    t=r['totals']
    lines=[
        "# PAL/prototype snes2asm after homolog alignment","",
        f"Windows rescored: **{t['windows']}**.",
        f"Whole-window role disagreements at identical offsets: **{t['same_offset_role_disagreements']}**.",
        f"Role disagreements after local homolog alignment: **{t['aligned_role_disagreements']}**.",
        f"Reduction: **{t['role_disagreement_reduction_fraction']:.1%}**.",
        f"Windows with zero role disagreement after alignment: **{t['zero_role_disagreement_after_alignment']} / {t['windows']}**.",
        "",
        "| Europe window | Proto shift | Raw sim | Role disagree same→aligned | M/X disagree same→aligned |",
        "|---|---:|---:|---:|---:|",
    ]
    for w in r['windows']:
        lines.append(f"| `{w['retail_start_cpu']}..{w['retail_end_cpu']}` | {w['prototype_shift']:+d} | {w['raw_similarity_after_alignment']:.3f} | {w['same_offset_role_disagreements']}→{w['aligned_role_disagreements']} | {w['same_offset_mx_disagreements']}→{w['aligned_mx_disagreements']} |")
    lines += ['', 'Only disagreements that survive homolog alignment should be considered candidates for da65/Ghidra adjudication. Same-offset disagreement is retained as raw evidence but is not itself semantic evidence.', '']
    return '\n'.join(lines)


def main()->int:
    r=build()
    OUT_JSON.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    OUT_MD.write_text(render(r),encoding='utf-8')
    print(OUT_MD.read_text())
    return 0

if __name__=="__main__": raise SystemExit(main())
