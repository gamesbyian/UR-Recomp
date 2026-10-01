#!/usr/bin/env python3
"""Probe the stunt-message/reward/display pipeline across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/stunt-message-pipeline-structure-island.json"
OUTM=ROOT/"analysis/generated/stunt-message-pipeline-structure-island.md"
REGIONS=[
 ("queue_consume_reward","code","81:C0DD","81:C368"),
 ("score_display","code","81:C369","81:C457"),
 ("embedded_message_reward_data","data","81:C458","81:C575"),
 ("queue_helpers_and_append","code","81:C576","81:C604"),
]
SEED_USA=["81:C0DD","81:C576","81:C5B3"]

def best_shift(src,dst,start,end,center=0,radius=96):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def local_profile(src,dst,start,end,center,window=32):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1); sh,sc=best_shift(src,dst,p,hi,center,64)
  out.append({"usa_start":offset_to_cpu(p),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  p=hi+1
 return out

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 # First get coarse shifts, then seed each build at homologous executable entries.
 region_shifts={}
 for build,blob in blobs.items():
  region_shifts[build]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   center=0 if build in {"usa-retail","legacy-beta"} else (-35 if build=="pal-prototype-1994-11-29" else -23)
   region_shifts[build][name]=best_shift(usa,blob,us,ue,center)[0]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[]
  for cpu in SEED_USA:
   off=cpu_to_offset(cpu)
   # choose the containing coarse code region's shift
   for name,kind,s,e in REGIONS:
    if kind=="code" and cpu_to_offset(s)<=off<=cpu_to_offset(e):
     seeds.append(off+region_shifts[build][name]); break
  seed_entries(d,seeds); ds[build]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=region_shifts[build][name]; bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code": info.update(roles(ds[build],bs,be))
   else: info.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   if build in {"pal-prototype-1994-11-29","europe-retail"}:
    info["local_shift_profile_32byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {"schema_version":1,"island":"StuntMessageRewardDisplayPipeline","usa_start":"81:C0DD","usa_end":"81:C604","regions":rows}

def render(r):
 lines=["# Stunt message / reward / display structural island","",
 "This probe spans the mirrored stunt-message consumers, boost/score reward logic, score-display conversion, embedded lookup data, and the queue append helpers.","",
 "| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("STUNT_MESSAGE_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
