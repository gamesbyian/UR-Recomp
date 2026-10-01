#!/usr/bin/env python3
"""Probe the race camera-control cluster across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/camera-control-structure-island.json"
OUTM=ROOT/"analysis/generated/camera-control-structure-island.md"

REGIONS=[
 ("camera_velocity_follow_solver","81:9FBF","81:A2E4"),
 ("camera_smoothing_helper","81:A2E5","81:A30E"),
 ("camera_scale_config","81:A30F","81:A52A"),
 ("camera_update_wrapper","81:A52B","81:A59D"),
]

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def best_shift(src,dst,start,end,center=0,radius=160):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  sc=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if sc>best[1]: best=(shift,sc)
 return best

def local_profile(src,dst,start,end,center,window=64):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1); sh,sc=best_shift(src,dst,p,hi,center,96)
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
   if build in {"pal-prototype-1994-11-29","europe-retail"}:
    info["local_shift_profile_64byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {
  "schema_version":1,
  "island":"RaceCameraControlCluster",
  "usa_start":"81:9FBF","usa_end":"81:A59D",
  "per_frame_entry":"81:A52F",
  "long_entry_wrapper":"81:A52B",
  "regions":rows,
 }

def render(r):
 lines=["# Race camera-control structural island","",
 "This probe covers the camera target-velocity solver, its smoothing helper, zoom/scale configuration, and the per-frame camera update wrapper.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("CAMERA_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
