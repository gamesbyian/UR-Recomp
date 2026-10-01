#!/usr/bin/env python3
"""Probe the per-racer collision/contact response core across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/collision-response-structure-island.json"
OUTM=ROOT/"analysis/generated/collision-response-structure-island.md"
REGIONS=[
 ("candidate_reduction_and_surface_classification","81:8FB8","81:91F0",-32,-32),
 ("landing_air_and_velocity_gates","81:91F1","81:9303",-32,-32),
 ("contact_response_after_europe_nops","81:9304","81:97FF",-32,-26),
 ("final_position_correction_and_return","81:9800","81:983A",-32,-15),
 ("contact_direction_quantizer","81:983B","81:99D5",-32,-15),
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

def ranges_for(predicate,start,end):
 out=[]; run=None
 for x in range(start,end+1):
  if predicate(x):
   if run is None: run=x
  elif run is not None:
   out.append({"start":offset_to_cpu(run),"end":offset_to_cpu(x-1),"size":x-run}); run=None
 if run is not None: out.append({"start":offset_to_cpu(run),"end":offset_to_cpu(end),"size":end-run+1})
 return out

def fine_profile(src,dst,start,end,center,window=16):
 return local_profile(src,dst,start,end,center,window)

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-32}
 shifts={}
 for build,blob in blobs.items():
  shifts[build]={}
  for name,s,e,proto_shift,europe_shift in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   if build=="pal-prototype-1994-11-29":
    shifts[build][name]=proto_shift
   elif build=="europe-retail":
    shifts[build][name]=europe_shift
   else:
    shifts[build][name]=0
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[cpu_to_offset(s)+shifts[build][name] for name,s,e,proto_shift,europe_shift in REGIONS]
  for cpu in ["81:9355","81:93CA","81:9401","81:9467","81:9484","81:9646","81:96AD","81:9969","81:996B","81:9972"]:
   off=cpu_to_offset(cpu)
   if build=="europe-retail":
    local_shift=-26 if off<cpu_to_offset("81:9800") else -15
   elif build=="pal-prototype-1994-11-29":
    local_shift=-32
   else:
    local_shift=0
   seeds.append(off+local_shift)
  seed_entries(d,seeds); ds[build]=d
 rows=[]
 for name,s,e,proto_shift,europe_shift in REGIONS:
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
   row["builds"][build]=info
  rows.append(row)
 eu=blobs["europe-retail"]
 insertions=[
  {
   "name":"europe_landing_nop_insert",
   "usa_boundary_before":"81:9304","europe_start":"81:92E4","size":6,
   "hex":eu[cpu_to_offset("81:92E4"):cpu_to_offset("81:92E9")+1].hex(" "),
   "instructions":"NOP; NOP; NOP; NOP; NOP; NOP",
   "effect":"Europe retail alone inserts six NOPs after the landing-state CMP/BNE gate; subsequent homolog shift changes -32 to -26.",
  },
  {
   "name":"europe_position_guard_insert",
   "usa_boundary_before":"81:9800","europe_start":"81:97E6","size":11,
   "hex":eu[cpu_to_offset("81:97E6"):cpu_to_offset("81:97F0")+1].hex(" "),
   "instructions":"LDA $0DE7; AND #$00FE; CMP #$0008; BEQ +8",
   "effect":"Europe retail alone adds an 11-byte guard before the final position-correction tail; subsequent homolog shift changes -26 to -15.",
  },
 ]
 return {"schema_version":1,"island":"PerRacerCollisionContactResponse","usa_start":"81:8FB8","usa_end":"81:99D5","next_code_entry":"81:99D6","dormant_usa_code":[{"start":"81:9484","end":"81:948A","size":7,"instructions":"LDA #$0764; STA $A3; BRA $94AF","note":"valid instruction-aligned alternative bypassed by the recovered live predecessor path"}],"europe_only_insertions":insertions,"usa_unreached_runs":ranges_for(lambda x:not (ds["usa-retail"].code_map[x]&(ds["usa-retail"].OP_CODE|ds["usa-retail"].OP_PARAM)),cpu_to_offset("81:8FB8"),cpu_to_offset("81:99D5")),"regions":rows}

def render(r):
 lines=["# Per-racer collision / contact-response structural island","",
 "USA 81:8FB8..99D5 consumes sampled course/contact state, reduces collision candidates, classifies landing/air state, corrects velocity and position, and includes the contact-direction quantizer at 81:983B. The next independent long-entry wrapper begins at 81:99D6.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COLLISION_RESPONSE_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
