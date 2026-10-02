#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from build_course_presentation_contract import (
    COARSE_ENTRY_BYTES, COARSE_TABLE_BASE, COARSE_TABLE_BYTES,
    FINE_RECORD_BYTES, FINE_TABLE_BASE, ROM, descriptor, dim_value, le16,
)
from rnc_method1 import unpack_method1

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/generated/course-presentation-contract-sample.json"
MD_OUT=ROOT/"analysis/generated/course-presentation-contract-sample.md"
SAMPLE=[(1,"Dragster baseline"),(9,"128x8 race"),(5,"32x32 circuit"),(6,"16x64 race")]

def surface_slot(word):
    if not (word & 0x03FF):
        return None
    return ((word & 0x000F)>>1)+((word & 0x03F0)>>2)

def inspect_course(rom,streams,index,label):
    _off,packed,_hdr=streams[index-1]
    decoded=unpack_method1(packed)
    parsed=parse_course_resource_list(decoded)
    dim_x,dim_y=dim_value(decoded[13]),dim_value(decoded[14])
    coarse_cols,coarse_rows=dim_x*4,dim_y*4
    coarse_count=coarse_cols*coarse_rows
    cursor=parsed["resource_cursor_initial"]
    resources=[descriptor(rom,rid) for rid in parsed["resource_ids"]]
    c000_total=sum(x["c000_span"] for x in resources)
    a000_total=sum(x["a000_span"] for x in resources)
    fine_bytes=cursor-FINE_TABLE_BASE
    fine_aligned=fine_bytes>=0 and fine_bytes%FINE_RECORD_BYTES==0
    record_count=fine_bytes//FINE_RECORD_BYTES if fine_aligned else -1
    coarse=[le16(decoded,COARSE_TABLE_BASE+i*2) for i in range(coarse_count)]
    used=sorted(set(coarse))
    bad=[]
    normal=0
    if fine_aligned:
        for rid in range(record_count):
            base=FINE_TABLE_BASE+rid*FINE_RECORD_BYTES
            for cell in range(16):
                word=le16(decoded,base+cell*2)
                slot=surface_slot(word)
                if slot is None:
                    continue
                normal+=1
                if not 0<=slot<c000_total:
                    bad.append({"record_id":rid,"cell":cell,"word":word,"slot":slot})
    checks={
        "header_product_1024":dim_x*dim_y==1024,
        "runtime_coarse_entries_16384":coarse_count==16384,
        "coarse_table_exactly_0x8000":coarse_count*COARSE_ENTRY_BYTES==COARSE_TABLE_BYTES,
        "fine_region_32_byte_aligned":fine_aligned,
        "coarse_record_refs_in_range":bool(used) and used[-1]<record_count,
        "normal_surface_slots_in_materialized_range":not bad,
        "a000_is_32_bytes_per_c000_slot":a000_total==c000_total*32,
    }
    return {
        "index":index,"label":label,"header_dims":[dim_x,dim_y],
        "coarse_grid":[coarse_cols,coarse_rows],"coarse_entry_count":coarse_count,
        "resource_list_offset":cursor,"fine_record_bytes":fine_bytes,
        "fine_record_count":record_count,"used_record_id_min":used[0] if used else None,
        "used_record_id_max":used[-1] if used else None,"used_record_id_count":len(used),
        "resource_count":len(parsed["resource_ids"]),"c000_total":c000_total,
        "a000_total":a000_total,"normal_surface_word_count":normal,
        "invalid_surface_slots":bad,"checks":checks,
    }

def render_md(result):
    lines=["# Course presentation-contract sample validation","",
           "Deliberately small cross-course invariant check, not a 45-course census.","",
           "| course | dims | coarse grid | fine records | C000 slots | A000 bytes | all checks |",
           "|---|---:|---:|---:|---:|---:|---|"]
    for x in result["courses"]:
        ok=all(x["checks"].values())
        lines.append(f"| {x['index']} ({x['label']}) | {x['header_dims'][0]}x{x['header_dims'][1]} | {x['coarse_grid'][0]}x{x['coarse_grid'][1]} | {x['fine_record_count']} | {x['c000_total']} | {x['a000_total']} | {'yes' if ok else 'NO'} |")
    lines += ["","Validated invariants:","",
              "- header dimensions multiply to 1024;",
              "- runtime expansion yields 16,384 coarse sectors and an exact 0x8000-byte u16 coarse table;",
              "- 0x800F to the resource cursor is an integral number of 32-byte fine records;",
              "- every coarse reference stays inside the fine-record table;",
              "- every normal packed surface word selects a C000 slot inside the materialized resource span;",
              "- A000 materialization is exactly 32 bytes per C000 slot.","",
              "This is enough to treat the Dragster two-level spatial/resource shape as a reusable family invariant for Widescreen-facing queries while still deferring a full-corpus/editor-format census.",""]
    return "\n".join(lines)

def main():
    rom=ROM.read_bytes()
    streams=list(find_streams(rom))
    courses=[inspect_course(rom,streams,i,label) for i,label in SAMPLE]
    result={"schema_version":1,
            "sample_policy":"one representative from four distinct header shapes; stop before corpus-wide expansion",
            "sample_indices":[i for i,_ in SAMPLE],
            "courses":courses,
            "all_checks_pass":all(all(x["checks"].values()) for x in courses)}
    if not result["all_checks_pass"]:
        raise SystemExit(json.dumps(result,indent=2))
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    MD_OUT.write_text(render_md(result),encoding="utf-8")
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
