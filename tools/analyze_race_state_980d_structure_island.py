#!/usr/bin/env python3
"""Recover the 82:980D mirrored race-state bridge across the four preserved ROMs."""
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
OUTJ=ROOT/"analysis/generated/race-state-980d-structure-island.json"
OUTM=ROOT/"analysis/generated/race-state-980d-structure-island.md"
REGIONS=[
 ("long_entry_wrapper","code","82:980D","82:9810"),
 ("mirrored_state_bridge","code","82:9811","82:98BD"),
]

def best_shift(src,dst,start,end,center=0,radius=96):
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
 target=cpu_to_offset("82:980D")
 d=trace(usa)
 code=[r for r in census["regions"] if r["kind"]=="code"]
 seed_entries(d,sorted({cpu_to_offset(r["usa_start"]) for r in code}))
 out=[]
 for r in code:
  s,e=cpu_to_offset(r["usa_start"]),cpu_to_offset(r["usa_end"])
  for p in range(s,e+1):
   if not (d.code_map[p]&d.OP_CODE): continue
   op=usa[p]; got=None
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
 aligns={}
 for b,blob in blobs.items():
  aligns[b]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if b=="usa-retail" else best_shift(usa,blob,us,ue)
   aligns[b][name]={"shift":sh,"similarity":round(sim,6)}
 ds={}
 for b,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset("82:980D")+aligns[b]["long_entry_wrapper"]["shift"],
                  cpu_to_offset("82:9811")+aligns[b]["mirrored_state_bridge"]["shift"]])
  ds[b]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
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
  "island":"RaceStateBridge980D",
  "usa_start":"82:980D","usa_end":"82:98BD","next_entry":"82:98BE",
  "bounded_bytes":cpu_to_offset("82:98BD")-cpu_to_offset("82:980D")+1,
  "boundary_basis":{
   "entry":"82:980D is the uncovered long-entry target called from the accepted race-frame orchestrator.",
   "exit":"82:98BD is RTS; 82:98BE begins a distinct routine."
  },
  "accepted_caller_edges":caller_edges(usa,census),
  "observed_dataflow":[
   "compares paired values $0FC3/$0FC5 after halving",
   "derives mirrored outputs $0FCB/$0FCD from paired bitfields $0FBB/$0FBD",
   "forces either output to $FFFF when paired availability/state flags $0EF5/$0EF7 are active",
   "forces both outputs to $FFFF outside the accepted $77074B mode range"
  ],
  "regions":rows,
 }

def render(r):
 lines=["# 82:980D mirrored race-state bridge structural island","",
  "USA 82:980D..98BD is a compact long-entry helper called directly from race-frame orchestration. It derives mirrored $0FCB/$0FCD outputs from paired course/control state and terminates at 82:98BD; 82:98BE begins a separate routine and is excluded.","",
  "| Region | Bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines+=["","## Accepted-census caller",""]
 for e in r["accepted_caller_edges"]:
  lines.append(f"- {e['callsite']} {e['kind']} -> 82:980D from {e['source']} / {e['region']}")
 lines+=["","The label remains structural: the mirrored-output behavior is clear, while exact higher-level gameplay naming for $0FCB/$0FCD is deferred.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("RACE_STATE_980D_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
