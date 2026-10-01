#!/usr/bin/env python3
"""Probe the race/stunt timer lifecycle across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/race-timer-structure-island.json"
OUTM=ROOT/"analysis/generated/race-timer-structure-island.md"

REGIONS=[
 ("long_entry_and_dispatch_live","81:C697","81:C6A3"),
 ("dormant_cb37_call","81:C6A4","81:C6A6"),
 ("mode_dispatch_tail","81:C6A7","81:C6D2"),
 ("count_up_timer","81:C6D3","81:C7E0"),
 ("stunt_countdown_timer","81:C7E1","81:C906"),
]

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def best_shift(src,dst,start,end,center=0,radius=128):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  sc=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if sc>best[1]: best=(shift,sc)
 return best

def local_profile(src,dst,start,end,center,window=48):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1); sh,sc=best_shift(src,dst,p,hi,center,64)
  out.append({"usa_start":offset_to_cpu(p),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  p=hi+1
 return out

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-20}
 shifts={}
 for build,blob in blobs.items():
  shifts[build]={}
  for name,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   shifts[build][name]=best_shift(usa,blob,us,ue,centers[build])[0]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[cpu_to_offset(s)+shifts[build][name] for name,s,e in REGIONS]
  seed_entries(d,seeds); ds[build]=d
 rows=[]
 for name,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=shifts[build][name]; bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),**roles(ds[build],bs,be),
         "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=role_disagreements=0
    for pos in range(us,ue+1):
     a=ds["usa-retail"].code_map[pos]; b=ds[build].code_map[pos+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM):
      role_disagreements+=1
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
    info["aligned_opcode_pairs"]=pairs
    info["aligned_equal_opcode_pairs"]=equal
    info["aligned_opcode_consensus_fraction"]=round(equal/pairs,6) if pairs else None
    info["aligned_role_disagreements"]=role_disagreements
   if build in {"pal-prototype-1994-11-29","europe-retail"}:
    info["local_shift_profile_48byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {
  "schema_version":1,
  "island":"RaceAndStuntTimerLifecycle",
  "usa_start":"81:C697","usa_end":"81:C906",
  "long_entry":"81:C697","dispatcher":"81:C69B",
  "count_up_entry":"81:C6D3","countdown_entry":"81:C7E1",
  "next_code_entry":"81:C907",
  "regions":rows,
 }

def render(r):
 lines=["# Race / stunt timer lifecycle structural island","",
 "USA 81:C697..C906 contains the timer long-entry wrapper, mode dispatcher, count-up race timer, stunt countdown timer, digit refresh, timeout handling, and warning-sound threshold. The next code begins at 81:C907.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("TIMER_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
