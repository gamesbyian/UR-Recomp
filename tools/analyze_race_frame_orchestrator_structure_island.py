#!/usr/bin/env python3
"""Recover the race-frame orchestration corridor around the main frame loop."""
from __future__ import annotations
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/race-frame-orchestrator-structure-island.json"
OUTM=ROOT/"analysis/generated/race-frame-orchestrator-structure-island.md"
PAL_LINE_BUILDS={"pal-prototype-1994-11-29","europe-retail"}

REGIONS=[
 ("setup_loop_prefix","83:CBCC","83:CC86","code"),
 ("loop_body_after_rep_cleanup","83:CC87","83:CD9F","code"),
]
SHIFTS={
 "usa-retail":(0,0),
 "legacy-beta":(0,0),
 "pal-prototype-1994-11-29":(0,-2),
 "europe-retail":(38,36),
}

def roles(d,start,end):
 op=param=other=0; opcode_starts=[]
 for off in range(start,end+1):
  role=d.code_map[off]
  if role & d.OP_CODE:
   op+=1; opcode_starts.append(offset_to_cpu(off))
  elif role & d.OP_PARAM: param+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":param,"unreached_or_data_bytes":other,"opcode_starts":opcode_starts}

def similarity(src,dst,src_start,src_end,dst_start,dst_end):
 a=src[src_start:src_end+1]; b=dst[dst_start:dst_end+1]
 n=min(len(a),len(b))
 return sum(a[i]==b[i] for i in range(n))/max(len(a),len(b))

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}
 usa=blobs["usa-retail"]
 rows=[]
 for index,(name,s,e,kind) in enumerate(REGIONS):
  us=cpu_to_offset(s); ue=cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   shift=SHIFTS[build][index]
   size_delta=-2 if index==0 and build in PAL_LINE_BUILDS else 0
   bs=us+shift; be=ue+shift+size_delta
   d=trace(blob); seed_entries(d,[bs])
   classified=roles(d,bs,be)
   row["builds"][build]={
    "start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":shift,
    "similarity":round(similarity(usa,blob,us,ue,bs,be),6),
    "size":be-bs+1,"size_delta":size_delta,
    **{k:v for k,v in classified.items() if k!="opcode_starts"},
    "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest(),
   }
  rows.append(row)
 # Seed the entire corridor as one control-flow graph as well, so loop reachability
 # is asserted independently from the piecewise homolog bookkeeping.
 us=cpu_to_offset("83:CBCC"); ue=cpu_to_offset("83:CD9F")
 usa_trace=trace(usa); seed_entries(usa_trace,[us]); usa_roles=roles(usa_trace,us,ue)
 return {
  "schema_version":1,
  "island":"race-frame orchestration corridor",
  "usa_start":"83:CBCC","usa_end":"83:CD9F","usa_size":ue-us+1,
  "seed_basis":"USA 83:CBCC is SEP #$30, independently establishing 8-bit A/X before the setup and loop corridor.",
  "loop":{"header":"83:CC62","back_edge":"83:CD9D JMP $CC62",
          "header_reached":"83:CC62" in usa_roles["opcode_starts"],
          "back_edge_reached":"83:CD9D" in usa_roles["opcode_starts"]},
  "known_calls":{"input":"82:AA6A","racer_update":"82:89B5 wrapper","oam":"82:ACA1","player_state_marshal":"81:8D14"},
  "lineage_edits":[{
    "usa_span":"83:CC85..CC86","bytes":"e2 20","instruction":"SEP #$20",
    "effect":"PAL prototype and Europe omit the second of two consecutive SEP #$20 instructions at USA 83:CC83..CC86; net -2 bytes with the following loop body otherwise continuing at the new homolog shift."
  }],
  "regions":rows,
 }

def render(r):
 lines=["# Race-frame orchestration structural island: USA 83:CBCC..CD9F","",
 "The corridor begins at an explicit SEP #$30, includes the main race-loop header at 83:CC62, and reaches the JMP $CC62 back-edge at 83:CD9D.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |",
 "|---|---:|---|---|---|"]
 for x in r["regions"]:
  def cell(build):
   b=x["builds"][build]
   return f"{b['start']}..{b['end']} ({b['shift']:+d}; size {b['size']}; sim {b['similarity']:.3f}; op {b['opcode_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines += ["","## Lineage edit","",
 "USA retail and the legacy beta contain consecutive SEP #$20 instructions at 83:CC83..CC86. The PAL prototype and Europe retail omit the second instruction (USA 83:CC85..CC86), contracting the remaining loop body by two bytes. The edit is already present in the 1994-11-29 PAL prototype.",
 "","The corridor directly orchestrates input decode, racer simulation, player-state marshaling, racer OAM construction, and additional HUD/race services. This artifact records control-flow structure without assigning semantics to every callee.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)+"\n"); print(render(r)); print("RACE_FRAME_ORCHESTRATOR_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
