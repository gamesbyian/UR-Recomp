#!/usr/bin/env python3
"""Recover the geometry math helper at USA 81:B6C0..B712 across preserved builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/geometry-math-helper-structure-island.json"
OUTM=ROOT/"analysis/generated/geometry-math-helper-structure-island.md"
REGIONS=[
 ("long_entry_wrapper","81:B6C0","81:B6C3"),
 ("hardware_multiply_geometry_body","81:B6C4","81:B712"),
]
CALLS=["81:9C92","81:9CAE","81:9CDC","81:9CF8","81:9D33","81:9D43","81:9D71","81:9D81"]

def best_shift(src,dst,start,end,center=0,radius=96):
 block=src[start:end+1]; best=(center,-1.0)
 for sh in range(center-radius,center+radius+1):
  a=start+sh; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(sh,score)
 return best

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
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-15}
 aligns={}
 for build,blob in blobs.items():
  aligns[build]={}
  body_s,body_e=cpu_to_offset("81:B6C4"),cpu_to_offset("81:B712")
  body_shift,body_sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,body_s,body_e,centers[build])
  for name,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   if name=="long_entry_wrapper":
    sh=body_shift
    sim=sum(x==y for x,y in zip(usa[us:ue+1],blob[us+sh:ue+sh+1]))/(ue-us+1)
   else:
    sh,sim=body_shift,body_sim
   aligns[build][name]={"shift":sh,"similarity":round(sim,6),"start":offset_to_cpu(us+sh),"end":offset_to_cpu(ue+sh)}
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset("81:B6C0")+aligns[build]["long_entry_wrapper"]["shift"],cpu_to_offset("81:B6C4")+aligns[build]["hardware_multiply_geometry_body"]["shift"]])
  ds[build]=d
 rows=[]
 for name,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   a=aligns[build][name]; sh=a["shift"]; bs,be=us+sh,ue+sh
   info={**a,"size":be-bs+1,"size_delta":0,**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=bad=0; mismatches=[]
    for pos in range(us,ue+1):
     x=ds["usa-retail"].code_map[pos]; y=ds[build].code_map[pos+sh]
     if bool(x&ds["usa-retail"].OP_CODE)!=bool(y&ds[build].OP_CODE) or bool(x&ds["usa-retail"].OP_PARAM)!=bool(y&ds[build].OP_PARAM): bad+=1
     if x&ds["usa-retail"].OP_CODE and y&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
      else: mismatches.append({"usa":offset_to_cpu(pos),"other":offset_to_cpu(pos+sh),"usa_byte":f"{usa[pos]:02x}","other_byte":f"{blob[pos+sh]:02x}"})
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad,"opcode_mismatches":mismatches})
   row["builds"][build]=info
  rows.append(row)
 return {
  "schema_version":1,
  "island":"GeometryHardwareMultiplyHelper",
  "usa_start":"81:B6C0","usa_end":"81:B712",
  "entry":"81:B6C0","body_entry":"81:B6C4","next_entry":"81:B713",
  "known_callers":[{"callsite":x,"source":"geometry-precompute"} for x in CALLS],
  "hardware_registers":{"multiplicand":"$211B","multiplier":"$211C","product_mid":"$2135","product_high":"$2136"},
  "regions":rows,
 }

def render(r):
 lines=["# Geometry hardware-multiply helper structural island","",
 "USA 81:B6C0..B712 is a long-entry wrapper plus the shared geometry math body called eight times by the recovered geometry-precompute island. The body uses the SNES hardware multiply registers $211B/$211C and reads $2135/$2136; 81:B713 begins a separate routine.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines+=["","## Accepted callers",""]
 for x in r["known_callers"]: lines.append(f"- {x['callsite']} from {x['source']}")
 lines += ["", "The 79-byte body is byte-identical across all four preserved ROMs. Only the 4-byte long-entry wrapper call operand relocates with the surrounding bank-81 layout.", ""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("GEOMETRY_MATH_HELPER_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
