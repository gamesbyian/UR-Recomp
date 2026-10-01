#!/usr/bin/env python3
"""Probe the per-racer collision/contact resolution cluster across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu
ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/collision-resolution-structure-island.json"
OUTM=ROOT/"analysis/generated/collision-resolution-structure-island.md"
REGIONS=[
 ("collision_contact_resolver","81:8FB8","81:983A"),
 ("collision_geometry_helper","81:983B","81:99D5"),
]

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def spans_for_mask(d,start,end):
 spans=[]; a=None
 for p in range(start,end+1):
  reached=bool(d.code_map[p]&(d.OP_CODE|d.OP_PARAM))
  if not reached and a is None: a=p
  if reached and a is not None:
   spans.append({"start":offset_to_cpu(a),"end":offset_to_cpu(p-1),"size":p-a}); a=None
 if a is not None: spans.append({"start":offset_to_cpu(a),"end":offset_to_cpu(end),"size":end-a+1})
 return spans

def best_shift(src,dst,start,end,center=0,radius=192):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  sc=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if sc>best[1]: best=(shift,sc)
 return best

def local_profile(src,dst,start,end,center,window=96):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1); sh,sc=best_shift(src,dst,p,hi,center,96)
  out.append({"usa_start":offset_to_cpu(p),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  p=hi+1
 return out

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-32}
 shifts={}
 for build,blob in blobs.items():
  shifts[build]={}
  for name,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   shifts[build][name]=best_shift(usa,blob,us,ue,centers[build])[0]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset(s)+shifts[build][name] for name,s,e in REGIONS]); ds[build]=d
 rows=[]
 for name,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"usa_unreached_spans":spans_for_mask(ds["usa-retail"],us,ue),"builds":{}}
  for build,blob in blobs.items():
   sh=shifts[build][name]; bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=roles_bad=0
    for pos in range(us,ue+1):
     a=ds["usa-retail"].code_map[pos]; b=ds[build].code_map[pos+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM): roles_bad+=1
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":roles_bad})
   if build in {"pal-prototype-1994-11-29","europe-retail"}: info["local_shift_profile_96byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {"schema_version":1,"island":"CollisionContactResolutionCluster","usa_start":"81:8FB8","usa_end":"81:99D5","main_entry":"81:8FB8","helper_entry":"81:983B","next_wrapper":"81:99D6","regions":rows}

def render(r):
 lines=["# Collision/contact resolution structural island","",
 "USA `81:8FB8..99D5` contains the per-racer collision/contact resolver plus its directly called geometry helper. The next wrapper begins at `81:99D6`.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"
def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COLLISION_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
