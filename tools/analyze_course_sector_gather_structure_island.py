#!/usr/bin/env python3
"""Probe the course-sector neighborhood gather immediately before the surface sampler."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
START="81:8A4A"; END="81:8B94"
OUTJ=ROOT/"analysis/generated/course-sector-gather-structure-island.json"
OUTM=ROOT/"analysis/generated/course-sector-gather-structure-island.md"

def best_shift(src,dst,start,end,radius=96):
 block=src[start:end+1]; best=(0,-1.0)
 for sh in range(-radius,radius+1):
  a=start+sh; b=a+len(block)
  if a<0 or b>len(dst): continue
  sim=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if sim>best[1]: best=(sh,sim)
 return best

def role_counts(d,s,e):
 op=pa=other=0
 for p in range(s,e+1):
  r=d.code_map[p]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":other}

def build(root:Path=ROOT):
 blobs={k:(root/p.relative_to(ROOT)).read_bytes() for k,p in ROMS.items()}
 usa=blobs["usa-retail"]; us,ue=cpu_to_offset(START),cpu_to_offset(END)
 aligns={}
 for name,blob in blobs.items():
  sh,sim=(0,1.0) if name=="usa-retail" else best_shift(usa,blob,us,ue)
  aligns[name]={"shift":sh,"similarity":round(sim,6)}
 ds={}
 for name,blob in blobs.items():
  d=trace(blob); seed_entries(d,[us+aligns[name]["shift"]]); ds[name]=d
 builds={}
 for name,blob in blobs.items():
  sh=aligns[name]["shift"]; s,e=us+sh,ue+sh
  info={"start":offset_to_cpu(s),"end":offset_to_cpu(e),"shift":sh,
        "similarity":aligns[name]["similarity"],"size":e-s+1,
        "sha256":hashlib.sha256(blob[s:e+1]).hexdigest(),**role_counts(ds[name],s,e)}
  if name!="usa-retail":
   pairs=equal=bad=0
   for p in range(us,ue+1):
    a=ds["usa-retail"].code_map[p]; b=ds[name].code_map[p+sh]
    if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[name].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[name].OP_PARAM): bad+=1
    if a&ds["usa-retail"].OP_CODE and b&ds[name].OP_CODE:
     pairs+=1
     if usa[p]==blob[p+sh]: equal+=1
   info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad})
  builds[name]=info
 return {
  "schema_version":1,
  "island":"CourseSectorNeighborhoodGather",
  "usa_start":START,"usa_end":END,"size":ue-us+1,
  "next_region":"81:8B95",
  "boundary_basis":{
   "entry":"81:8A4A begins with explicit 16-bit coordinate/sector setup.",
   "exit":"81:8B94 is RTS; 81:8B95 begins the already-censused course-surface sampler.",
  },
  "observed_dataflow":[
   "reduces X/Y coordinates to 64-unit sector coordinates",
   "loads four neighboring sector entries from $7F000F",
   "selects/interpolates a local entry using within-sector coordinates",
   "reads the selected payload through $7F800F and writes the 20-byte workspace at $0260..$0272"
  ],
  "builds":builds,
 }

def render(r):
 lines=["# Course-sector neighborhood gather structural island","",
  "USA 81:8A4A..8B94 is the function immediately upstream of the existing course-surface sampler. It converts the current X/Y coordinates into coarse 64-unit sector coordinates, gathers the neighboring sector entries, selects a local payload, and fills the $0260..$0272 workspace consumed by the next stage.","",
  "| Build | Range | Shift | Similarity | Opcodes | Operands | Unreached/data |",
  "|---|---|---:|---:|---:|---:|---:|"]
 for name in ("usa-retail","pal-prototype-1994-11-29","europe-retail","legacy-beta"):
  b=r["builds"][name]
  lines.append(f"| {name} | {b['start']}..{b['end']} | {b['shift']:+d} | {b['similarity']:.3f} | {b['opcode_bytes']} | {b['operand_bytes']} | {b['unreached_or_data_bytes']} |")
 lines+=["","Boundary: 81:8B94 is the RTS; 81:8B95 begins the already-censused surface sampler.","",
 "The label is intentionally structural. It describes the observed sector-neighborhood/dataflow role without claiming that every $7F000F/$7F800F field is semantically decoded.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r))
if __name__=="__main__": main()
