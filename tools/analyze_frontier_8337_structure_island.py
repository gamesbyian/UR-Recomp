#!/usr/bin/env python3
"""Probe the uncovered 82:8337 structural frontier and its directly owned helper cluster."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS = {
 "usa-retail": ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29": ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail": ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta": ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
CENSUS = ROOT/"analysis/generated/comparative-structural-census.json"
OUTJ = ROOT/"analysis/generated/frontier-8337-structure-island.json"
OUTM = ROOT/"analysis/generated/frontier-8337-structure-island.md"

REGIONS = [
 ("long_entry_wrapper","code","82:8337","82:833A"),
 ("embedded_step_table","data","82:833B","82:836C"),
 ("primary_body_prefix","code","82:836D","82:853C"),
 ("primary_body_suffix","code","82:8540","82:87CB"),
 ("state_transition_helper","code","82:87CC","82:8929"),
 ("sequence_advance_helper","code","82:892A","82:8951"),
]
ENTRIES = ("82:8337","82:836D","82:87CC","82:892A")

def best_shift(src,dst,start,end,center=0,radius=128):
 block=src[start:end+1]; best=(center,-1.0)
 for sh in range(center-radius,center+radius+1):
  lo=start+sh; hi=lo+len(block)
  if lo<0 or hi>len(dst): continue
  score=sum(a==b for a,b in zip(block,dst[lo:hi]))/len(block)
  if score>best[1]: best=(sh,score)
 return best

def local_profile(src,dst,start,end,center=0,window=32):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1)
  sh,sim=best_shift(src,dst,p,hi,center,16)
  out.append({"usa_start":offset_to_cpu(p),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sim,6)})
  p=hi+1
 return out

def roles(d,s,e):
 op=pa=other=0
 for p in range(s,e+1):
  r=d.code_map[p]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":other}

def caller_edges(usa,census):
 target=cpu_to_offset("82:8337")
 d=trace(usa)
 code=[r for r in census["regions"] if r["kind"]=="code"]
 seed_entries(d,sorted({cpu_to_offset(r["usa_start"]) for r in code}))
 edges=[]
 for r in code:
  start,end=cpu_to_offset(r["usa_start"]),cpu_to_offset(r["usa_end"])
  for p in range(start,end+1):
   if not (d.code_map[p]&d.OP_CODE): continue
   op=usa[p]; got=None
   if op==0x20 and p+2<len(usa):
    bank=(p//0x8000)|0x80; addr=usa[p+1]|(usa[p+2]<<8)
    if addr>=0x8000: got=cpu_to_offset(f"{bank:02X}:{addr:04X}")
   elif op==0x22 and p+3<len(usa):
    addr=usa[p+1]|(usa[p+2]<<8); bank=usa[p+3]
    if addr>=0x8000: got=cpu_to_offset(f"{bank:02X}:{addr:04X}")
   if got==target:
    edges.append({"callsite":offset_to_cpu(p),"source":r["source"],"region":r["name"],"kind":"JSR" if op==0x20 else "JSL"})
 return edges

def build(root:Path=ROOT):
 paths={k:root/p.relative_to(ROOT) for k,p in ROMS.items()}
 blobs={k:p.read_bytes() for k,p in paths.items()}; usa=blobs["usa-retail"]
 census=json.loads((root/CENSUS.relative_to(ROOT)).read_text())
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-15,"europe-retail":7}
 aligns={}
 for build,blob in blobs.items():
  aligns[build]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue,centers[build])
   aligns[build][name]={"shift":sh,"similarity":round(sim,6)}
 ds={}
 for build,blob in blobs.items():
  d=trace(blob); seeds=[]
  for entry in ENTRIES:
   off=cpu_to_offset(entry)
   region=next(name for name,kind,s,e in REGIONS if kind=="code" and cpu_to_offset(s)<=off<=cpu_to_offset(e))
   seeds.append(off+aligns[build][region]["shift"])
  seed_entries(d,seeds); ds[build]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=aligns[build][name]["shift"]; bs,be=us+sh,ue+sh
   item={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"similarity":aligns[build][name]["similarity"],"size":be-bs+1,"size_delta":0,"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code": item.update(roles(ds[build],bs,be))
   else: item.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   if build!="usa-retail" and kind=="code":
    item["local_shift_profile_32byte"]=local_profile(usa,blob,us,ue,sh)
    pairs=equal=bad=0
    for p in range(us,ue+1):
     a=ds["usa-retail"].code_map[p]; b=ds[build].code_map[p+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM): bad+=1
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[p]==blob[p+sh]: equal+=1
    item.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad})
   row["builds"][build]=item
  rows.append(row)
 return {
  "schema_version":1,
  "island":"Frontier8337ConnectedCluster",
  "usa_start":"82:8337","usa_end":"82:8951","next_entry":"82:8952",
  "bounded_bytes":cpu_to_offset("82:8951")-cpu_to_offset("82:8337")+1,
  "homolog_region_bytes":sum(x["size"] for x in rows),
  "boundary_basis":{
   "entry":"82:8337 is the uncovered long-entry target reached from the accepted race-frame orchestrator.",
   "embedded_data":"82:833B..836C is a 25-word table referenced by the executable body.",
   "exit":"82:8951 is RTS; 82:8952 begins a separate JSR/RTL long-entry wrapper."
  },
  "accepted_caller_edges":caller_edges(usa,census),
  "lineage_edits":[{
   "builds":["pal-prototype-1994-11-29","europe-retail"],
   "usa_span":"82:853D..853F",
   "usa_hex":"20 2a 89",
   "instruction":"JSR $892A",
   "size_delta":-3,
   "effect":"Both PAL-line builds omit the USA/beta call to the six-state sequence-advance helper; following homologs shift from 0 to -3."
  }],
  "regions":rows,
 }

def render(r):
 lines=["# 82:8337 connected structural island","",
 "USA 82:8337..8951 contains the uncovered 82:8337 long-entry target, a 25-word embedded table, the primary body beginning at 82:836D, and two directly owned helpers through the RTS at 82:8951. Both PAL-line builds omit the USA/beta JSR $892A at 82:853D, producing a three-byte contraction; comparable code is therefore split on that seam. 82:8952 begins a separate long-entry wrapper and is excluded.","",
 "| Region | Kind | Bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines+=["","## Accepted-census callers",""]
 for e in r["accepted_caller_edges"]: lines.append(f"- {e['callsite']} {e['kind']} -> 82:8337 from {e['source']} / {e['region']}")
 lines+=["","## PAL-line contraction",""]
 for e in r["lineage_edits"]: lines.append(f"- {e['usa_span']} {e['instruction']}: {e['effect']}")
 lines+=["","No authoritative recovered RAM labels support a stronger subsystem name yet, so the semantic label remains intentionally structural.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("FRONTIER_8337_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
