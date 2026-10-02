#!/usr/bin/env python3
"""Probe the 83:ED2F..F0B6 angle/physics cluster across the preserved ROMs."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
CENSUS=ROOT/"analysis/generated/comparative-structural-census.json"
OUTJ=ROOT/"analysis/generated/angle-physics-ed2f-structure-island.json"
OUTM=ROOT/"analysis/generated/angle-physics-ed2f-structure-island.md"
REGIONS=[
 ("long_entry_wrapper","code","83:ED2F","83:ED32"),
 ("angle_motion_update","code","83:ED33","83:EF0F"),
 ("ground_angle_update","code","83:EF10","83:F0B6"),
]

def best_shift(src,dst,start,end,center=0,radius=160):
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
 target=cpu_to_offset("83:ED2F")
 d=trace(usa)
 code=[r for r in census["regions"] if r["kind"]=="code"]
 seed_entries(d,sorted({cpu_to_offset(r["usa_start"]) for r in code}))
 out=[]
 for r in code:
  s,e=cpu_to_offset(r["usa_start"]),cpu_to_offset(r["usa_end"])
  for p in range(s,e+1):
   if not (d.code_map[p]&d.OP_CODE): continue
   op=usa[p]; got=None
   if op==0x22 and p+3<len(usa):
    addr=usa[p+1]|(usa[p+2]<<8); bank=usa[p+3]
    if addr>=0x8000: got=cpu_to_offset(f"{bank:02X}:{addr:04X}")
   if got==target:
    out.append({"callsite":offset_to_cpu(p),"kind":"JSL","source":r["source"],"region":r["name"]})
 return out

def build(root:Path=ROOT):
 blobs={k:(root/p.relative_to(ROOT)).read_bytes() for k,p in ROMS.items()}
 census=json.loads((root/CENSUS.relative_to(ROOT)).read_text())
 usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":36,"europe-retail":72}
 aligns={}
 for b,blob in blobs.items():
  aligns[b]={}; center=centers[b]
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if b=="usa-retail" else best_shift(usa,blob,us,ue,center)
   aligns[b][name]={"shift":sh,"similarity":round(sim,6)}
   center=sh
 ds={}
 for b,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset(s)+aligns[b][name]["shift"] for name,_,s,_ in REGIONS])
  ds[b]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for b,blob in blobs.items():
   sh=aligns[b][name]["shift"]; bs,be=us+sh,ue+sh
   item={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,
         "similarity":aligns[b][name]["similarity"],"size":be-bs+1,"size_delta":0,
         "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest(),**roles(ds[b],bs,be)}
   if b!="usa-retail":
    pairs=equal=bad=0
    for p in range(us,ue+1):
     a=ds["usa-retail"].code_map[p]; bb=ds[b].code_map[p+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(bb&ds[b].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(bb&ds[b].OP_PARAM): bad+=1
     if a&ds["usa-retail"].OP_CODE and bb&ds[b].OP_CODE:
      pairs+=1
      if usa[p]==blob[p+sh]: equal+=1
    item.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad})
   row["builds"][b]=item
  rows.append(row)
 return {
  "schema_version":1,
  "island":"AnglePhysicsED2F",
  "usa_start":"83:ED2F","usa_end":"83:F0B6","next_entry":"83:F0B7",
  "bounded_bytes":cpu_to_offset("83:F0B6")-cpu_to_offset("83:ED2F")+1,
  "boundary_basis":{
   "entry":"83:ED2F is a long-entry wrapper called twice from the accepted racer-update island.",
   "internal":"83:ED33 calls 83:EF10 before updating angle/motion state; both are explicit instruction-aligned entries.",
   "exit":"83:F0B6 is RTS; 83:F0B7 begins a separate JSR/RTL wrapper for the following F0BB routine."
  },
  "accepted_caller_edges":caller_edges(usa,census),
  "observed_dataflow":[
   "updates active-racer angle and angular state including $0F49/$0F69/$0F77/$0F83/$0F8F/$0F95/$0F97/$0F99",
   "uses track/direction/air-state inputs to derive a bounded target angle",
   "feeds geometry/math helpers at $81:B773 and $80:96FD",
   "preserves a separate F0B7/F0BB rendering-preparation path outside this island"
  ],
  "regions":rows,
 }

def render(r):
 lines=["# ED2F angle/physics structural island","",
  "USA 83:ED2F..F0B6 is a per-racer angle/motion cluster called twice from the accepted racer-update path. The following F0B7/F0BB path is excluded because it belongs to rendering/tile preparation.","",
  "| Region | Bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']}; roleΔ {q.get('aligned_role_disagreements',0)})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines+=["","## Accepted-census callers",""]
 for e in r["accepted_caller_edges"]:
  lines.append(f"- {e['callsite']} {e['kind']} -> 83:ED2F from {e['source']} / {e['region']}")
 lines+=["","This first pass is structural. Regional alignment disagreements, if any, are evidence to subdivide rather than grounds to force a constant-shift match.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("ED2F_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
