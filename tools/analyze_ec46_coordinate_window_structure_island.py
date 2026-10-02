#!/usr/bin/env python3
"""Recover the 83:EC46 coordinate/window helper and its immediately preceding table."""
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
CENSUS=ROOT/"analysis/generated/comparative-structural-census.json"
OUTJ=ROOT/"analysis/generated/ec46-coordinate-window-structure-island.json"
OUTM=ROOT/"analysis/generated/ec46-coordinate-window-structure-island.md"

REGIONS=[
 ("coordinate_step_table","data","83:EBE6","83:EC45"),
 ("coordinate_window_update","code","83:EC46","83:ED2E"),
]

def best_shift(src,dst,start,end,center=0,radius=128):
 block=src[start:end+1]; best=(center,-1.0)
 for sh in range(center-radius,center+radius+1):
  lo=start+sh; hi=lo+len(block)
  if lo<0 or hi>len(dst): continue
  sim=sum(a==b for a,b in zip(block,dst[lo:hi]))/len(block)
  if sim>best[1]: best=(sh,sim)
 return best

def roles(d,s,e):
 op=pa=other=0
 for p in range(s,e+1):
  r=d.code_map[p]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":other}

def caller_edges(usa,census):
 target=cpu_to_offset("83:EC46")
 d=trace(usa)
 code=[r for r in census["regions"] if r["kind"]=="code"]
 seed_entries(d,sorted({cpu_to_offset(r["usa_start"]) for r in code}))
 out=[]
 for r in code:
  s,e=cpu_to_offset(r["usa_start"]),cpu_to_offset(r["usa_end"])
  for p in range(s,e+1):
   if not (d.code_map[p]&d.OP_CODE): continue
   op=usa[p]
   got=None
   if op==0x20 and p+2<len(usa):
    bank=(p//0x8000)|0x80; addr=usa[p+1]|(usa[p+2]<<8)
    if addr>=0x8000: got=cpu_to_offset(f"{bank:02X}:{addr:04X}")
   elif op==0x22 and p+3<len(usa):
    addr=usa[p+1]|(usa[p+2]<<8); bank=usa[p+3]
    if addr>=0x8000: got=cpu_to_offset(f"{bank:02X}:{addr:04X}")
   if got==target:
    out.append({"callsite":offset_to_cpu(p),"kind":"JSR" if op==0x20 else "JSL","source":r["source"],"region":r["name"]})
 return out

def build(root:Path=ROOT):
 blobs={k:(root/p.relative_to(ROOT)).read_bytes() for k,p in ROMS.items()}
 census=json.loads((root/CENSUS.relative_to(ROOT)).read_text())
 usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":0,"europe-retail":0}
 aligns={}
 for b,blob in blobs.items():
  aligns[b]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if b=="usa-retail" else best_shift(usa,blob,us,ue,centers[b])
   aligns[b][name]={"shift":sh,"similarity":round(sim,6)}
 ds={}
 for b,blob in blobs.items():
  d=trace(blob)
  entry=cpu_to_offset("83:EC46")+aligns[b]["coordinate_window_update"]["shift"]
  seed_entries(d,[entry])
  ds[b]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for b,blob in blobs.items():
   sh=aligns[b][name]["shift"]; bs,be=us+sh,ue+sh
   item={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,
         "similarity":aligns[b][name]["similarity"],"size":be-bs+1,"size_delta":0,
         "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code":
    item.update(roles(ds[b],bs,be))
    if b!="usa-retail":
     pairs=equal=bad=0
     for p in range(us,ue+1):
      a=ds["usa-retail"].code_map[p]; bb=ds[b].code_map[p+sh]
      if bool(a&ds["usa-retail"].OP_CODE)!=bool(bb&ds[b].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(bb&ds[b].OP_PARAM): bad+=1
      if a&ds["usa-retail"].OP_CODE and bb&ds[b].OP_CODE:
       pairs+=1
       if usa[p]==blob[p+sh]: equal+=1
     item.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad})
   else:
    item.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   row["builds"][b]=item
  rows.append(row)
 return {
  "schema_version":1,
  "island":"CoordinateWindowUpdate",
  "usa_start":"83:EBE6","usa_end":"83:ED2E","next_entry":"83:ED2F",
  "bounded_bytes":cpu_to_offset("83:ED2E")-cpu_to_offset("83:EBE6")+1,
  "boundary_basis":{
   "table":"83:EBE6..EC45 is a 48-word monotonic step table referenced by the executable body.",
   "entry":"83:EC46 is the direct race-frame caller target.",
   "exit":"83:ED2E is RTS; 83:ED2F begins a separate JSR/RTL long-entry wrapper."
  },
  "accepted_caller_edges":caller_edges(usa,census),
  "observed_dataflow":[
   "updates two mirrored coordinate/window outputs at $0D3F and $0D41",
   "uses state bytes at $0DE9/$0DEB, selectors at $0D43/$0D45, and values at $0DE3/$0DE5",
   "indexes the preceding 48-word table and adds base $100C for the mid-range path",
   "sets validity flags $0D1B/$0D1D when an output coordinate is active"
  ],
  "regions":rows,
 }

def render(r):
 lines=["# 83:EC46 coordinate/window structural island","",
  "USA 83:EBE6..ED2E contains a 48-word step table followed by the direct race-frame target at 83:EC46. The code updates mirrored outputs at $0D3F/$0D41 from paired state/selector inputs and returns at 83:ED2E; 83:ED2F begins a separate long-entry wrapper and is excluded.","",
  "| Region | Kind | Bytes | PAL prototype | Europe | Legacy beta |",
  "|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines+=["","## Accepted-census caller",""]
 for e in r["accepted_caller_edges"]:
  lines.append(f"- {e['callsite']} {e['kind']} -> 83:EC46 from {e['source']} / {e['region']}")
 lines+=["","The semantic label is intentionally conservative. The paired outputs behave like coordinate/window positions, but higher-level gameplay meaning is not asserted here.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("EC46_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
