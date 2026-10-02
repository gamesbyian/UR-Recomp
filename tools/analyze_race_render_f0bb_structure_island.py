#!/usr/bin/env python3
"""Recover the race-loop render/geometry service at USA 83:F0BB..F4D1."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/race-render-f0bb-structure-island.json"
OUTM=ROOT/"analysis/generated/race-render-f0bb-structure-island.md"
REGIONS=[
 ("race_render_body","code","83:F0BB","83:F295"),
 ("address_decode_helper","code","83:F296","83:F2BA"),
 ("tile_pair_decode_helper","code","83:F2BB","83:F4D1"),
]

def best_shift(src,dst,start,end,center=0,radius=128):
 block=src[start:end+1]; best=(center,-1.0)
 for sh in range(center-radius,center+radius+1):
  lo=start+sh; hi=lo+len(block)
  if lo<0 or hi>len(dst): continue
  score=sum(a==b for a,b in zip(block,dst[lo:hi]))/len(block)
  if score>best[1]: best=(sh,score)
 return best

def roles(d,s,e):
 op=pa=other=0
 for p in range(s,e+1):
  r=d.code_map[p]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":other}

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":36,"europe-retail":72}
 aligns={}; ds={}
 for build,blob in blobs.items():
  aligns[build]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue,centers[build])
   aligns[build][name]={"shift":sh,"similarity":round(sim,6),"start":offset_to_cpu(us+sh),"end":offset_to_cpu(ue+sh)}
  d=trace(blob)
  seed_entries(d,[cpu_to_offset("83:F0BB")+aligns[build]["race_render_body"]["shift"]])
  ds[build]=d
 rows=[]
 for name,kind,s,e in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e); builds={}
  for build,blob in blobs.items():
   q=aligns[build][name]; sh=q["shift"]; bs,be=us+sh,ue+sh
   info={**q,"size":be-bs+1,"size_delta":0,**roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if build!="usa-retail":
    pairs=equal=bad=0
    for pos in range(us,ue+1):
     aa=ds["usa-retail"].code_map[pos]; bb=ds[build].code_map[pos+sh]
     if bool(aa&ds["usa-retail"].OP_CODE)!=bool(bb&ds[build].OP_CODE) or bool(aa&ds["usa-retail"].OP_PARAM)!=bool(bb&ds[build].OP_PARAM): bad+=1
     if aa&ds["usa-retail"].OP_CODE and bb&ds[build].OP_CODE:
      pairs+=1
      if usa[pos]==blob[pos+sh]: equal+=1
    info.update({"aligned_opcode_pairs":pairs,"aligned_equal_opcode_pairs":equal,"aligned_role_disagreements":bad})
   builds[build]=info
  rows.append({"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":builds})
 return {
  "schema_version":1,"island":"RaceRenderF0BB",
  "usa_start":"83:F0BB","usa_end":"83:F4D1","next_entry":"83:F4D2","bounded_bytes":1047,
  "boundary_basis":{
   "entry":"83:F0BB is called directly from the accepted race-frame orchestrator at 83:CD7F.",
   "internal":"83:F296 and 83:F2BB are JSR targets reached from the main routine.",
   "exit":"83:F4D1 is RTS; 83:F4D2 begins a distinct helper and F4DA begins text data."
  },
  "accepted_caller_edges":[{"callsite":"83:CD7F","kind":"JSR","source":"race-frame-orchestrator","target":"83:F0BB"}],
  "regions":rows
 }

def render(r):
 lines=["# Race-render F0BB structural island","",
 "USA 83:F0BB..F4D1 is a race-loop rendering/geometry service called from 83:CD7F. It contains a 475-byte main body and two internal decode helpers, ending before the unrelated F4D2 helper and F4DA text data.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines.append("")
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("RACE_RENDER_F0BB_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
