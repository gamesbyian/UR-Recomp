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

REGIONS=[
 ("resolver_prefix_before_europe_nops","81:8FB8","81:9303",-32,-32),
 ("resolver_after_europe_nops","81:9304","81:97FF",-32,-26),
 ("resolver_after_europe_gate","81:9800","81:983A",-32,-15),
 ("collision_geometry_helper","81:983B","81:99D5",-32,-15),
]
DORMANT_USA=["81:9484","81:9646","81:96AD","81:9969","81:996B","81:9972"]

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def shift_for(cpu,build):
 off=cpu_to_offset(cpu)
 for _,s,e,proto,eu in REGIONS:
  if cpu_to_offset(s)<=off<=cpu_to_offset(e):
   return 0 if build in {"usa-retail","legacy-beta"} else (proto if build=="pal-prototype-1994-11-29" else eu)
 raise ValueError(cpu)

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[cpu_to_offset(s)+(0 if build in {"usa-retail","legacy-beta"} else (proto if build=="pal-prototype-1994-11-29" else eu)) for _,s,e,proto,eu in REGIONS]
  seeds += [cpu_to_offset(cpu)+shift_for(cpu,build) for cpu in DORMANT_USA]
  seed_entries(d,seeds); ds[build]=d
 rows=[]
 for name,s,e,proto_shift,europe_shift in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   sh=0 if build in {"usa-retail","legacy-beta"} else (proto_shift if build=="pal-prototype-1994-11-29" else europe_shift)
   bs,be=us+sh,ue+sh
   sc=sum(a==b for a,b in zip(usa[us:ue+1],blob[bs:be+1]))/(ue-us+1)
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":sh,"size":be-bs+1,"size_delta":0,
         "similarity":round(sc,6),**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=bad=0; role_mismatches=[]; opcode_mismatches=[]
    for pos in range(us,ue+1):
     a=ds["usa-retail"].code_map[pos]; b=ds[build].code_map[pos+sh]
     role_bad=bool(a&ds["usa-retail"].OP_CODE)!=bool(b&ds[build].OP_CODE) or bool(a&ds["usa-retail"].OP_PARAM)!=bool(b&ds[build].OP_PARAM)
     if role_bad:
      bad+=1; role_mismatches.append({"usa":offset_to_cpu(pos),"other":offset_to_cpu(pos+sh),"usa_byte":f"{usa[pos]:02x}","other_byte":f"{blob[pos+sh]:02x}"})
     if a&ds["usa-retail"].OP_CODE and b&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
      else: opcode_mismatches.append({"usa":offset_to_cpu(pos),"other":offset_to_cpu(pos+sh),"usa_byte":f"{usa[pos]:02x}","other_byte":f"{blob[pos+sh]:02x}"})
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad,"role_mismatches":role_mismatches,"opcode_mismatches":opcode_mismatches})
   row["builds"][build]=info
  rows.append(row)
 us=cpu_to_offset("81:9302"); eu=us-32
 gate_us=cpu_to_offset("81:9800"); gate_eu=gate_us-15-11
 return {
  "schema_version":1,"island":"CollisionContactResolutionCluster",
  "usa_start":"81:8FB8","usa_end":"81:99D5","main_entry":"81:8FB8","helper_entry":"81:983B","next_wrapper":"81:99D6",
  "dormant_seed_entries":DORMANT_USA,
  "lineage_edits":[
   {"build":"europe-retail","usa_seam":"after 81:9303","europe_span":offset_to_cpu(eu+2)+".."+offset_to_cpu(eu+7),"size_delta":6,"effect":"Branch at USA 81:9302 D0 09 becomes D0 0F in Europe and is followed by six NOP bytes; subsequent homolog shift changes -32 to -26."},
   {"build":"europe-retail","usa_seam":"before 81:9800","europe_span":offset_to_cpu(gate_eu)+".."+offset_to_cpu(gate_eu+10),"size_delta":11,"hex":blobs["europe-retail"][gate_eu:gate_eu+11].hex(" "),"effect":"Europe inserts an 11-byte conditional gate before the shared 81:9800 tail; subsequent homolog shift changes -26 to -15."},
  ],
  "regions":rows,
 }

def render(r):
 lines=["# Collision/contact resolution structural island","",
 "USA `81:8FB8..99D5` contains the per-racer collision/contact resolver plus its directly called geometry helper. Four dormant branch entries are seeded explicitly so the full USA code surface is classified. The next wrapper begins at `81:99D6`.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines += ["","## Europe-only structural edits",""]
 for e in r["lineage_edits"]: lines.append(f"- {e['usa_seam']}: {e['effect']}")
 lines.append("")
 return "\n".join(lines)
def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COLLISION_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
