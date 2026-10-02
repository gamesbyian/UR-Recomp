#!/usr/bin/env python3
"""Match stock VRAM update-list state to recorded $2116/$2118 PPU writes."""

from __future__ import annotations
import argparse,json,re
from pathlib import Path

TAG_RE=re.compile(r"race-start-active-(\d{3})$")

def u16(blob:bytes,addr:int)->int:
    return blob[addr] | (blob[addr+1]<<8)

def expected_events(wram:bytes)->list[dict]:
    events=[]
    for family,count_addr,dest_base,selector_base in (
        ("A",0x0DCD,0x0D8D,0x0D6D),
        ("B",0x0DCF,0x0DAD,0x0D7D),
    ):
        count=u16(wram,count_addr)
        for i in range(count-1,-1,-1):
            dest=u16(wram,dest_base+i*2)
            selector=wram[selector_base+i]
            source_word=u16(wram,0x2132+selector*2)
            swapped=((source_word & 0xFF)<<8)|(source_word>>8)
            events.append({
                "family":family,"index":i,"destination":dest,"selector":selector,
                "source_word":source_word,
                "write_2118":swapped & 0xFF,
                "write_2119":(swapped>>8)&0xFF,
            })
    return events

def recorded_events(path:Path)->list[dict]:
    rows=[]
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        f=line.split("\t")
        if len(f)<4: continue
        try: value=int(f[3],16)
        except ValueError: continue
        rows.append((f[2].upper(),value))
    out=[]
    for i in range(len(rows)-3):
        regs=[rows[i+j][0] for j in range(4)]
        if regs==["2116","2117","2118","2119"]:
            out.append({
                "destination":rows[i][1] | (rows[i+1][1]<<8),
                "write_2118":rows[i+2][1],
                "write_2119":rows[i+3][1],
            })
    return out

def as_key(row:dict)->tuple[int,int,int]:
    return row["destination"],row["write_2118"],row["write_2119"]

def find_contiguous(haystack:list[dict],needle:list[dict])->int|None:
    if not needle: return None
    keys=[as_key(x) for x in haystack]
    target=[as_key(x) for x in needle]
    for i in range(len(keys)-len(target)+1):
        if keys[i:i+len(target)]==target:
            return i
    return None

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("dump_dir",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()

    samples=[]
    for wram_path in sorted(args.dump_dir.glob("prep-emission-*.wram.bin")):
        tag=wram_path.name.removesuffix(".wram.bin")
        m=TAG_RE.match(tag)
        if not m: continue
        wram=wram_path.read_bytes()
        if len(wram)!=0x20000: continue
        expected=expected_events(wram)
        recorded=recorded_events(args.dump_dir/f"{tag}.ppuw.tsv")
        match=find_contiguous(recorded,expected)
        samples.append({
            "sample":tag,
            "relative_frame":int(m.group(1)),
            "count_a":u16(wram,0x0DCD),
            "count_b":u16(wram,0x0DCF),
            "expected_events":expected,
            "recorded_d383_shape_events":recorded,
            "exact_contiguous_match_start":match,
            "exact_match":bool(expected) and match is not None,
        })
    if not samples:
        raise SystemExit("no race-start-active WRAM dumps found")
    first_nonzero=next((x for x in samples if x["expected_events"]),None)
    first_match=next((x for x in samples if x["exact_match"]),None)
    report={
        "schema_version":1,
        "fixture":"preparation-emission-race",
        "first_nonzero_update_list_sample":first_nonzero,
        "first_exact_emission_match_sample":first_match,
        "samples":samples,
    }
    lines=[
      "# Stock preparation-list → PPU emission probe","",
      f"- first non-zero update-list sample: **{first_nonzero['sample'] if first_nonzero else 'none'}**",
      f"- first exact predicted emission match: **{first_match['sample'] if first_match else 'none'}**","",
      "| sample | list A | list B | predicted events | recorded D383-shaped events | exact match |",
      "|---|---:|---:|---:|---:|---|",
    ]
    for x in samples:
        lines.append(f"| {x['sample']} | {x['count_a']} | {x['count_b']} | {len(x['expected_events'])} | {len(x['recorded_d383_shape_events'])} | {x['exact_match']} |")
    payload=json.dumps(report,indent=2)+"\n"
    md="\n".join(lines)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if first_match else 1

if __name__=="__main__":
    raise SystemExit(main())
