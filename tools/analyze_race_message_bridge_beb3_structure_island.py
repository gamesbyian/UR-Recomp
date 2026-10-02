#!/usr/bin/env python3
"""Recover the race-frame message/state bridge at USA 81:BEB3..C0DC."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/race-message-bridge-beb3-structure-island.json"
OUTM=ROOT/"analysis/generated/race-message-bridge-beb3-structure-island.md"
REGIONS=[
 ("long_entry_wrapper","code","81:BEB3","81:BEB6"),
 ("race_message_dispatch","code","81:BEB7","81:BF40"),
 ("mirrored_commit_helper","code","81:BF41","81:BFE2"),
 ("mirrored_materialize_helper","code","81:BFE3","81:C0DC"),
]

def best_shift(src,dst,start,end,center=0,radius=96):
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
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-32,"europe-retail":-15}
 aligns={}; ds={}
 for build,blob in blobs.items():
  aligns[build]={}
  for name,kind,s,e in REGIONS:
   us,ue=cpu_to_offset(s),cpu_to_offset(e)
   sh,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue,centers[build])
   aligns[build][name]={"shift":sh,"similarity":round(sim,6),"start":offset_to_cpu(us+sh),"end":offset_to_cpu(ue+sh)}
  d=trace(blob)
  seed_entries(d,[cpu_to_offset("81:BEB7")+aligns[build]["race_message_dispatch"]["shift"],
                  cpu_to_offset("81:BF41")+aligns[build]["mirrored_commit_helper"]["shift"],
                  cpu_to_offset("81:BFE3")+aligns[build]["mirrored_materialize_helper"]["shift"]])
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
  "schema_version":1,
  "island":"RaceMessageBridgeBEB3",
  "usa_start":"81:BEB3","usa_end":"81:C0DC","next_entry":"81:C0DD",
  "bounded_bytes":554,
  "boundary_basis":{
   "entry":"81:BEB3 is the long-entry target called from the accepted race-frame orchestrator at 83:CD61.",
   "internal":"81:BEB7, 81:BF41 and 81:BFE3 are direct helper entries separated by RTS boundaries.",
   "exit":"81:C0DC is RTS; 81:C0DD begins the already-accepted stunt-message pipeline."
  },
  "accepted_caller_edges":[{"callsite":"83:CD61","kind":"JSL","source":"race-frame-orchestrator","target":"81:BEB3"}],
  "observed_dataflow":[
   "handles mirrored P1/P2 message/state paths using $11B7/$11B9 and $0E9D/$0EBD",
   "materializes 16-byte character/message payloads through table reads in banks $17 and $80",
   "sets mirrored ready flags $0EDD/$0EDF and cooldown/state values $0C9F/$0CA1"
  ],
  "regions":rows
 }

def render(r):
 lines=["# Race-message bridge BEB3 structural island","",
 "USA 81:BEB3..C0DC is a race-frame message/state bridge called from 83:CD61, ending immediately before the accepted stunt-message pipeline at 81:C0DD. It contains the long-entry wrapper and three bounded executable helpers.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines += ["","The bridge exposes a paired P1/P2 handoff into the already-recovered stunt-message queue: mirrored state/ready flags and mirrored 16-byte payload buffers are updated before 81:C0DD consumes them.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("RACE_MESSAGE_BEB3_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
