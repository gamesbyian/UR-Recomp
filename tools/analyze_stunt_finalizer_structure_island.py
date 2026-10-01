#!/usr/bin/env python3
"""Probe the stunt-finalization/scoring subsystem across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/stunt-finalizer-structure-island.json"
OUTM=ROOT/"analysis/generated/stunt-finalizer-structure-island.md"

REGIONS=[
 ("air_state_and_rotation_progress","code","82:9A42","82:9B57"),
 ("landing_trick_classification","code","82:9B58","82:9C97"),
 ("score_index_and_message_emit","code","82:9C98","82:9D67"),
 ("state_clear_and_exit","code","82:9D68","82:9D8B"),
 ("flip_score_weights","data","82:9D8C","82:9D95"),
 ("roll_score_weights","data","82:9D96","82:9D9F"),
 ("twist_score_weights","data","82:9DA0","82:9DA9"),
 ("trick_praise_table","data","82:9DAA","82:A01A"),
]

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def best_shift(src,dst,start,end,center,radius=48):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def local_profile(src,dst,start,end,center,window=32):
 out=[]; pos=start
 while pos<=end:
  hi=min(end,pos+window-1)
  sh,sc=best_shift(src,dst,pos,hi,center)
  out.append({"usa_start":offset_to_cpu(pos),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  pos=hi+1
 return out

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 ds={}
 for name,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset("82:9A42")])
  ds[name]=d
 rows=[]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-5,"europe-retail":17}
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh,sc=best_shift(usa,blob,us,ue,centers[build])
   bs,be=us+sh,ue+sh
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,
         "size_delta":0,"similarity":round(sc,6),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code": info.update(roles(ds[build],bs,be))
   else: info.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   if build in {"pal-prototype-1994-11-29","europe-retail"} and kind=="code":
    info["local_shift_profile_32byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {
  "schema_version":1,
  "island":"Stunt_FinalizeAndScoreAirTricks",
  "usa_start":"82:9A42","usa_end":"82:A01A",
  "routine_end":"82:9D8B",
  "next_code_entry":"82:A01B",
  "regions":rows,
 }

def render(r):
 lines=["# Stunt finalization/scoring structural island","",
 "USA code begins at 82:9A42, returns at 82:9D8B, and is immediately followed by three compact score-weight tables plus the trick/praise lookup through 82:A01A. Next code begins at 82:A01B.","",
 "| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("STUNT_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
