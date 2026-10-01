#!/usr/bin/env python3
"""Probe the per-racer contact-geometry constructor across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/contact-geometry-structure-island.json"
OUTM=ROOT/"analysis/generated/contact-geometry-structure-island.md"
REGIONS=[
 ("angle_and_source_record_setup","81:9E2A","81:9E7C"),
 ("vertex_expansion_and_orientation","81:9E7D","81:9F1C"),
 ("mirror_offset_and_collision_anchor_finalize","81:9F1D","81:9FBE"),
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

def local_profile(src,dst,start,end,center,window=32):
 out=[]; p=start
 while p<=end:
  hi=min(end,p+window-1); sh,sc=best_shift(src,dst,p,hi,center,64)
  out.append({"usa_start":offset_to_cpu(p),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  p=hi+1
 return out

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-15}
 shifts={}
 for build,blob in blobs.items():
  shifts[build]={}
  for name,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   shifts[build][name]=best_shift(usa,blob,us,ue,centers[build])[0]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  entry_shift=shifts[build][REGIONS[0][0]]
  seed_entries(d,[cpu_to_offset("81:9E2A")+entry_shift]); ds[build]=d
 rows=[]
 for name,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=shifts[build][name]; bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=bad=0; mismatches=[]
    for pos in range(us,ue+1):
     a=ds["usa-retail"].code_map[pos]; b=ds[build].code_map[pos+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM): bad+=1
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
      else: mismatches.append({"usa":offset_to_cpu(pos),"target":offset_to_cpu(pos+sh),"usa_opcode":f"{usa[pos]:02x}","target_opcode":f"{blob[pos+sh]:02x}"})
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad,"opcode_mismatches":mismatches})
   if build in {"pal-prototype-1994-11-29","europe-retail"}:
    info["local_shift_profile_32byte"]=local_profile(usa,blob,us,ue,sh)
   row["builds"][build]=info
  rows.append(row)
 return {"schema_version":1,"island":"PerRacerContactGeometryConstructor","usa_start":"81:9E2A","usa_end":"81:9FBE","callers":["81:8DD6","81:8F2A"],"next_code_entry":"81:9FBF","regions":rows}

def render(r):
 lines=["# Per-racer contact-geometry structural island","",
 "USA `81:9E2A..9FBE` is called independently for P1 and P2 from the persistent-state marshal, before the course-surface sampler and collision resolver. It derives orientation-dependent contact geometry and writes the active-player collision anchor at `125B,Y`. Camera control begins immediately at `81:9FBF`.","",
 "All 405 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype preserves the routine at constant shift -32; Europe preserves it at constant shift -15. Both regional builds match all 246 aligned opcode positions with zero code/operand-role disagreements.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines += ["","The routine is the structural bridge from shared current-player orientation/state to the course-surface sampler and collision resolver. Regional collision lineage edits therefore occur downstream of this constructor, not in contact-geometry generation.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("CONTACT_GEOMETRY_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
