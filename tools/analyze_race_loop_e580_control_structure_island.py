#!/usr/bin/env python3
"""Recover the race-loop E580 control island and preceding lookup table."""
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
OUTJ=ROOT/"analysis/generated/race-loop-e580-control-structure-island.json"
OUTM=ROOT/"analysis/generated/race-loop-e580-control-structure-island.md"
REGIONS=[
 ("race_control_lookup","data","83:E540","83:E57F"),
 ("race_loop_control","code","83:E580","83:E7A4"),
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
 target=cpu_to_offset("83:E580")
 d=trace(usa)
 code=[r for r in census["regions"] if r["kind"]=="code"]
 seed_entries(d,sorted({cpu_to_offset(r["usa_start"]) for r in code}))
 out=[]
 for r in code:
  s,e=cpu_to_offset(r["usa_start"]),cpu_to_offset(r["usa_end"])
  for p in range(s,e+1):
   if not (d.code_map[p]&d.OP_CODE): continue
   if usa[p]!=0x20 or p+2>=len(usa): continue
   bank=(p//0x8000)|0x80
   addr=usa[p+1]|(usa[p+2]<<8)
   if addr>=0x8000 and cpu_to_offset(f"{bank:02X}:{addr:04X}")==target:
    out.append({"callsite":offset_to_cpu(p),"kind":"JSR","source":r["source"],"region":r["name"]})
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
  seed_entries(d,[cpu_to_offset("83:E580")+aligns[b]["race_loop_control"]["shift"]])
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
  "island":"RaceLoopE580Control",
  "usa_start":"83:E540","usa_end":"83:E7A4","next_entry":"83:E7A5",
  "bounded_bytes":cpu_to_offset("83:E7A4")-cpu_to_offset("83:E540")+1,
  "boundary_basis":{
   "table":"83:E540..E57F is a 64-byte/32-word table read as 16-bit values through LDA $83E540,X.",
   "entry":"83:E580 is called directly from accepted race-frame orchestration at 83:CD47.",
   "exit":"83:E7A4 is RTS; 83:E7A5 begins the separate routine owned by parallel PR #176."
  },
  "accepted_caller_edges":caller_edges(usa,census),
  "observed_dataflow":[
   "selects and writes a paired control/resource value through $11F3/$11F5",
   "branches on race state $11BB, mode $77074B, and phase $0FE7",
   "queues APU/control commands through $82:8000 and services them through $82:8035",
   "updates paired race lifecycle state in $0315..$032F and accumulators $11CF/$11D1"
  ],
  "regions":rows,
 }

def render(r):
 lines=["# Race-loop E580 control structural island","",
  "USA 83:E540..E7A4 is a seam-bounded race-loop support island between the merged E066/E53F control pair and the separate E7A5 routine. It contains a 64-byte table plus the direct race-frame target at E580.","",
  "| Region | Kind | Bytes | PAL prototype | Europe | Legacy beta |",
  "|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines+=["","## Accepted-census caller",""]
 for e in r["accepted_caller_edges"]:
  lines.append(f"- {e['callsite']} {e['kind']} -> 83:E580 from {e['source']} / {e['region']}")
 lines+=["","The label is intentionally structural. The routine clearly participates in race-phase/control state and APU command selection, but exact higher-level semantics of $11F3/$11F5 are not asserted.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("E580_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
