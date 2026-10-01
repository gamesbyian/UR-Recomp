#!/usr/bin/env python3
"""Recover the per-racer collision/contact resolution cluster across preserved ROM builds."""
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

# name, start, end, Europe shift, execution class
REGIONS=[
 ("resolver_prefix_before_europe_nops","81:8FB8","81:9303",-32,"live"),
 ("resolver_live_a","81:9304","81:9483",-26,"live"),
 ("resolver_usa_dormant_a","81:9484","81:948A",-26,"usa-dormant"),
 ("resolver_live_b","81:948B","81:9645",-26,"live"),
 ("resolver_usa_dormant_b","81:9646","81:9669",-26,"usa-dormant"),
 ("resolver_live_c","81:966A","81:96AC",-26,"live"),
 ("resolver_usa_dormant_c","81:96AD","81:96AF",-26,"usa-dormant"),
 ("resolver_live_d","81:96B0","81:97FF",-26,"live"),
 ("resolver_tail_after_europe_gate","81:9800","81:983A",-15,"live"),
 ("geometry_helper_live_prefix","81:983B","81:9968",-15,"live"),
 ("geometry_helper_usa_dormant","81:9969","81:9978",-15,"usa-dormant"),
 ("geometry_helper_live_tail","81:9979","81:99D5",-15,"live"),
]

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
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  # Seed only trusted live entries. Dormant USA alternatives retain the inherited
  # classification produced by normal control flow rather than fabricated M/X context.
  base_shift=0 if build in {"usa-retail","legacy-beta"} else -32
  helper_shift=0 if build in {"usa-retail","legacy-beta"} else (-32 if build=="pal-prototype-1994-11-29" else -15)
  seed_entries(d,[cpu_to_offset("81:8FB8")+base_shift,cpu_to_offset("81:983B")+helper_shift]); ds[build]=d
 rows=[]
 for name,s,e,europe_shift,execution_class in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","execution_class":execution_class,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=0 if build in {"usa-retail","legacy-beta"} else (-32 if build=="pal-prototype-1994-11-29" else europe_shift)
   bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail" and execution_class=="live":
    pairs=equal=bad=0; mismatches=[]
    for pos in range(us,ue+1):
     a=ds["usa-retail"].code_map[pos]; b=ds[build].code_map[pos+sh]
     if bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM): bad+=1
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
      else: mismatches.append({"usa":offset_to_cpu(pos),"other":offset_to_cpu(pos+sh),"usa_byte":f"{usa[pos]:02x}","other_byte":f"{blob[pos+sh]:02x}"})
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad,"opcode_mismatches":mismatches})
   row["builds"][build]=info
  rows.append(row)
 eu_branch=cpu_to_offset("81:9302")-32
 gate=cpu_to_offset("81:9800")-26
 return {
  "schema_version":1,"island":"CollisionContactResolutionCluster","usa_start":"81:8FB8","usa_end":"81:99D5",
  "main_entry":"81:8FB8","helper_entry":"81:983B","next_wrapper":"81:99D6",
  "lineage_edits":[
   {"build":"europe-retail","usa_seam":"after 81:9303","europe_span":offset_to_cpu(eu_branch+2)+".."+offset_to_cpu(eu_branch+7),"size_delta":6,"effect":"Branch homolog of USA 81:9302 changes D0 09 to D0 0F and is followed by six NOPs; following shift changes -32 to -26."},
   {"build":"europe-retail","usa_seam":"before 81:9800","europe_span":offset_to_cpu(gate)+".."+offset_to_cpu(gate+10),"size_delta":11,"hex":blobs["europe-retail"][gate:gate+11].hex(" "),"effect":"Europe inserts LDA $0DE7; AND #$00FE; CMP #$0008; BEQ +8 before the shared tail; following shift changes -26 to -15."},
  ],
  "regions":rows,
 }

def render(r):
 lines=["# Collision/contact resolution structural island","",
 "USA `81:8FB8..99D5` contains the per-racer collision/contact resolver plus its directly called geometry helper. Live trusted-entry code and instruction-bounded USA-dormant alternatives are represented separately so dormant paths are not given fabricated analyzer M/X context. The next wrapper begins at `81:99D6`.","",
 "| Region | Class | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['execution_class']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines += ["","## Europe-only structural edits",""]
 for e in r["lineage_edits"]: lines.append(f"- {e['usa_seam']}: {e['effect']}")
 lines += ["","USA-dormant regions are still instruction-bounded code from the recovered listing/control graph; their analyzer opcode counts are intentionally not promoted as trusted-entry measurements.",""]
 return "\n".join(lines)
def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COLLISION_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
