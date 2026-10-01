#!/usr/bin/env python3
"""Recover the stunt-message/reward/display pipeline across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/stunt-message-pipeline-structure-island.json"
OUTM=ROOT/"analysis/generated/stunt-message-pipeline-structure-island.md"

REGIONS=[
 ("message_consume_pre_cleanup","code","81:C0DD","81:C24A",-32,-15),
 ("pal_line_removed_nops","code","81:C24B","81:C24D",None,None),
 ("message_consume_post_cleanup","code","81:C24E","81:C368",-35,-18),
 ("score_display_prefix","code","81:C369","81:C371",-35,-18),
 ("score_display_usa_gate","code","81:C372","81:C37E",-35,None),
 ("score_display_suffix","code","81:C37F","81:C457",-35,-23),
 ("message_reward_lookup_block","data","81:C458","81:C571",-35,-23),
 ("queue_long_entry_and_helpers","code","81:C572","81:C604",-35,-23),
]
ENTRY_POINTS={
 "usa-retail":["81:C0DD","81:C572","81:C576","81:C5AF","81:C5B3"],
 "legacy-beta":["81:C0DD","81:C572","81:C576","81:C5AF","81:C5B3"],
 "pal-prototype-1994-11-29":["81:C0BD","81:C54F","81:C553","81:C58C","81:C590"],
 "europe-retail":["81:C0CE","81:C55B","81:C55F","81:C598","81:C59C"],
}

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}

def similarity(a,b):
 return sum(x==y for x,y in zip(a,b))/max(len(a),len(b))

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 ds={}
 for build,blob in blobs.items():
  d=trace(blob); seed_entries(d,[cpu_to_offset(x) for x in ENTRY_POINTS[build]]); ds[build]=d

 rows=[]
 for name,kind,s,e,proto_shift,europe_shift in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  shifts={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":proto_shift,"europe-retail":europe_shift}
  for build,shift in shifts.items():
   if shift is None: continue
   blob=blobs[build]; bs,be=us+shift,ue+shift
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":shift,"size":be-bs+1,"size_delta":0,
         "similarity":round(similarity(usa[us:ue+1],blob[bs:be+1]),6),
         "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code": info.update(roles(ds[build],bs,be))
   else: info.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   row["builds"][build]=info
  rows.append(row)

 n0,n1=cpu_to_offset("81:C24B"),cpu_to_offset("81:C24D")
 eu_s,eu_e=cpu_to_offset("81:C35D"),cpu_to_offset("81:C364")
 europe=blobs["europe-retail"]
 return {
  "schema_version":1,
  "island":"StuntMessageRewardDisplayPipeline",
  "usa_start":"81:C0DD","usa_end":"81:C604",
  "lineage_edits":{
   "pal_line_nop_cleanup":{
    "usa_span":"81:C24B..C24D","size":3,"hex":usa[n0:n1+1].hex(" "),
    "instructions":"NOP; NOP; NOP",
    "effect":"PAL prototype and Europe omit the three USA/beta NOPs in the P2 message-consumer path.",
   },
   "europe_two_player_gate":{
    "usa_span":"81:C372..C37E","usa_size":13,"usa_hex":usa[cpu_to_offset("81:C372"):cpu_to_offset("81:C37E")+1].hex(" "),
    "prototype_span":"81:C34F..C35B",
    "europe_span":"81:C35D..C364","europe_size":8,"europe_hex":europe[eu_s:eu_e+1].hex(" "),
    "effect":"Europe replaces the longer USA/prototype two-player score-display gate with an equivalent 8-byte compare/branch/jump sequence, net -5 bytes.",
   },
  },
  "data_accesses":[
   {"site":"81:C1A8","base":"81:C458","role":"message presentation/action lookup indexed by message id"},
   {"site":"81:C167","base":"81:C4AA","role":"signed stunt-message boost reward lookup indexed by 2*(message id-1)"},
   {"site":"81:C10E","base":"81:C521","role":"message-to-stat/record mapping lookup indexed by message id-1"},
  ],
  "next_code_entry":"81:C605",
  "regions":rows,
 }

def render(r):
 lines=["# Stunt message / reward / display structural island","",
 "USA 81:C0DD..C604 connects queued stunt messages to score/boost rewards, message presentation, score-display digitization, embedded lookup data, and queue append helpers. The next code begins at 81:C605.","",
 "| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"].get(b)
   if not q: return "none"
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 lines += ["","## Structural edits","",
 "- USA/beta C24B..C24D are three NOPs; both PAL-line builds omit them.",
 "- Europe additionally contracts USA C372..C37E (13 bytes) to an 8-byte equivalent two-player display gate, net -5.",
 "- The embedded data block ends at C571. C572..C575 is executable JSR $C576; RTL, not table data; its relocated JSR operand exposed the true seam.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("STUNT_MESSAGE_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
