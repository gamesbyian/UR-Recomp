#!/usr/bin/env python3
"""Recover the Course_LoadAndMaterialize structural island across preserved builds."""
from __future__ import annotations
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/course-materialization-structure-island.json"
OUTM=ROOT/"analysis/generated/course-materialization-structure-island.md"
REGIONS=[
 ("setup","82:E165","82:E1CF","code"),
 ("resource_record_header","82:E1D1","82:E213","code"),
 ("dma_row_loop","82:E216","82:E2FF","code"),
 ("resource_materialize_A000_C000","82:E302","82:E385","code"),
 ("exit","82:E388","82:E395","code"),
]

def best_shift(src,dst,start,end,radius=128):
 block=src[start:end+1]; best=(0,-1.0)
 for shift in range(-radius,radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def roles(d,start,end):
 op=param=other=0
 for off in range(start,end+1):
  role=d.code_map[off]
  if role & d.OP_CODE: op+=1
  elif role & d.OP_PARAM: param+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":param,"unreached_or_data_bytes":other}

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 aligns={}
 for build,blob in blobs.items():
  per={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s); en=cpu_to_offset(e)
   shift,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,st,en)
   per[name]={"shift":shift,"similarity":round(sim,6),"start":offset_to_cpu(st+shift),"end":offset_to_cpu(en+shift)}
  aligns[build]=per
 analyzers={}
 for build,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset(s)+aligns[build][name]["shift"] for name,s,e,kind in REGIONS if kind=="code"])
  analyzers[build]={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s)+aligns[build][name]["shift"]; en=cpu_to_offset(e)+aligns[build][name]["shift"]
   analyzers[build][name]=roles(d,st,en)
 rows=[]
 for name,s,e,kind in REGIONS:
  us=cpu_to_offset(s); ue=cpu_to_offset(e)
  row={"name":name,"kind":kind,"size":ue-us+1,"usa_start":s,"usa_end":e,"builds":{}}
  for build,blob in blobs.items():
   a=aligns[build][name]; bs=us+a["shift"]; be=ue+a["shift"]
   row["builds"][build]={**a,**analyzers[build][name],"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
  rows.append(row)
 return {
  "schema_version":1,
  "island":"Course_LoadAndMaterialize 82:E165..E395",
  "boundary_basis":{
   "entry":"direct JSR at USA 82:DE0F plus existing named-function correspondence",
   "resource_loop":"header cursor read at E1D1; DMA loop begins E216",
   "materialization":"post-DMA branch at E302 enters resource-to-WRAM materialization; loop returns to E1D9",
   "exit":"all terminal paths converge at E388..E395 and RTS",
  },
  "regions":rows,
 }

def render(r):
 lines=["# Course materialization structural island: 82:E165..E395","",
 "This island follows the full named course loader from its direct entry through resource-list iteration, VRAM/DMA staging, A000/C000 WRAM materialization and the common exit.","",
 "| Region | Size | USA | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|---|"]
 for x in r["regions"]:
  def cell(build):
   b=x["builds"][build]
   return f"{b['start']}..{b['end']} ({b['shift']:+d}, sim {b['similarity']:.3f}; op {b['opcode_bytes']}, unreached/data {b['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('usa-retail')} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines += ["","## Structural boundaries","",
 "- setup: entry through DMA/pointer initialization.",
 "- resource_record_header: mutable decoded-course resource cursor, FF terminator, descriptor resolution and per-resource row metadata.",
 "- dma_row_loop: repeated 0x40-byte transfer rows with LoROM bank-wrap and VRAM progression.",
 "- resource_materialize_A000_C000: copies the resolved resource payload into paired runtime planes at 7E:A000 and 7E:C000.",
 "- exit: restores the bank-82 vector at DP $4F/$51 and returns.",
 "","This is structure recovery, not a claim that every field inside the island is semantically named."]
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COURSE_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
