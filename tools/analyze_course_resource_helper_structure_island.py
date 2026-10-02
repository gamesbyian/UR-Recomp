#!/usr/bin/env python3
"""Recover the course/resource helper cluster at USA 82:B293..B32E."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/course-resource-helper-structure-island.json"
OUTM=ROOT/"analysis/generated/course-resource-helper-structure-island.md"
REGIONS=[
 ("stream_byte_reader","82:B293","82:B2A8"),
 ("descriptor_wrapper_and_decoder","82:B2A9","82:B2D9"),
 ("resource_transfer_materializer","82:B2DA","82:B32E"),
]
CALLS=[
 {"callsite":"82:E18C","kind":"JSL","target":"82:B2DA","source":"course-materialization"},
 {"callsite":"82:E1F5","kind":"JSL","target":"82:B2A9","source":"course-materialization"},
]

def best_shift(src,dst,start,end,center=0,radius=128):
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
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-15,"europe-retail":7}
 aligns={}
 for build,blob in blobs.items():
  aligns[build]={}
  for name,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue,centers[build])
   aligns[build][name]={"shift":sh,"similarity":round(sim,6),"start":offset_to_cpu(us+sh),"end":offset_to_cpu(ue+sh)}
 ds={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[]
  for entry in ("82:B293","82:B2A9","82:B2DA"):
   # use the shift of the containing region
   region=next(n for n,s,e in REGIONS if cpu_to_offset(s)<=cpu_to_offset(entry)<=cpu_to_offset(e))
   seeds.append(cpu_to_offset(entry)+aligns[build][region]["shift"])
  seed_entries(d,seeds); ds[build]=d
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
 return {"schema_version":1,"island":"CourseResourceHelperCluster","usa_start":"82:B293","usa_end":"82:B32E","entries":["82:B293","82:B2A9","82:B2DA"],"next_data":"82:B32F","known_callers":CALLS,"regions":rows}

def render(r):
 lines=["# Course/resource helper structural island","",
 "USA `82:B293..B32E` is the compact helper cluster reached from the recovered course materialization loader: a stream-byte reader, a descriptor decoder/wrapper, and a resource transfer/materialization routine. The next span at `82:B32F` is table/data in the preserved listing.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines+=["","## Accepted caller edges",""]
 for x in r["known_callers"]: lines.append(f"- {x['callsite']} {x['kind']} → {x['target']} from {x['source']}")
 lines.append("")
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COURSE_RESOURCE_HELPER_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
