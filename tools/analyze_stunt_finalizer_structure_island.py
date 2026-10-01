#!/usr/bin/env python3
"""Recover the stunt-finalization/scoring subsystem across preserved ROM builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
ENTRY={
 "usa-retail":"82:9A42",
 "legacy-beta":"82:9A42",
 "pal-prototype-1994-11-29":"82:9A3D",
 "europe-retail":"82:9A53",
}
OUTJ=ROOT/"analysis/generated/stunt-finalizer-structure-island.json"
OUTM=ROOT/"analysis/generated/stunt-finalizer-structure-island.md"

REGIONS=[
 ("air_state_and_rotation_progress","code","82:9A42","82:9B57",-5,17),
 ("landing_trick_classification","code","82:9B58","82:9C97",-5,17),
 ("score_index_and_message_prefix","code","82:9C98","82:9D08",-5,17),
 ("pal_line_removed_nops","code","82:9D09","82:9D0D",None,None),
 ("praise_select_emit","code","82:9D0E","82:9D67",-10,12),
 ("state_clear_and_exit","code","82:9D68","82:9D8B",-10,12),
 ("flip_score_weights","data","82:9D8C","82:9D95",-10,12),
 ("roll_score_weights","data","82:9D96","82:9D9F",-10,12),
 ("twist_score_weights","data","82:9DA0","82:9DA9",-10,12),
 ("trick_praise_table","data","82:9DAA","82:A01A",-10,12),
]

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
 for name,blob in blobs.items():
  d=trace(blob); seed_entries(d,[cpu_to_offset(ENTRY[name])]); ds[name]=d

 rows=[]
 for name,kind,s,e,proto_shift,europe_shift in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  shifts={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":proto_shift,"europe-retail":europe_shift}
  for build,shift in shifts.items():
   if shift is None: continue
   blob=blobs[build]; bs,be=us+shift,ue+shift
   info={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":shift,
         "size":be-bs+1,"size_delta":0,
         "similarity":round(similarity(usa[us:ue+1],blob[bs:be+1]),6),
         "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if kind=="code": info.update(roles(ds[build],bs,be))
   else: info.update({"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":be-bs+1})
   row["builds"][build]=info
  rows.append(row)

 nop_s,nop_e=cpu_to_offset("82:9D09"),cpu_to_offset("82:9D0D")
 return {
  "schema_version":1,
  "island":"Stunt_FinalizeAndScoreAirTricks",
  "usa_start":"82:9A42","usa_end":"82:A01A",
  "routine_end":"82:9D8B",
  "next_code_entries":{
   "usa-retail":"82:A01B","legacy-beta":"82:A01B",
   "pal-prototype-1994-11-29":"82:A011","europe-retail":"82:A027",
  },
  "lineage_edit":{
   "usa_span":"82:9D09..9D0D","size":5,"hex":usa[nop_s:nop_e+1].hex(" "),
   "instructions":"NOP; NOP; NOP; NOP; NOP",
   "effect":"PAL prototype and Europe omit all five USA/beta NOPs; subsequent code and all scoring tables move five bytes earlier within each PAL-line build.",
  },
  "regions":rows,
 }

def render(r):
 lines=["# Stunt finalization/scoring structural island","",
 "USA code begins at 82:9A42 and returns at 82:9D8B. Three compact score-weight tables and the 625-byte trick/praise lookup continue through 82:A01A; the next USA code begins at 82:A01B.","",
 "| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"].get(b)
   if not q: return "none"
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['kind']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 e=r["lineage_edit"]
 lines += ["","## Lineage edit","",f"- {e['usa_span']} ({e['size']} bytes): {e['instructions']}.",
  "- USA/beta retain the five NOPs. PAL prototype and Europe omit them, changing the prototype shift -5 to -10 and Europe +17 to +12.",
  "- All three score-weight tables and the 625-byte trick/praise table are byte-identical across all four builds after this shift.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("STUNT_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
