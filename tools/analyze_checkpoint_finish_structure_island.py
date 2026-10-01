#!/usr/bin/env python3
"""Recover the checkpoint/finish course-object handler across preserved builds."""
from __future__ import annotations
import hashlib,json
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/checkpoint-finish-structure-island.json"
OUTM=ROOT/"analysis/generated/checkpoint-finish-structure-island.md"

REGIONS=[
 ("entry_time_prefix","81:8050","81:8101",0,0),
 ("frame_normalization_usa_shape","81:8102","81:8117",0,None),
 ("post_normalization","81:8118","81:8194",0,-14),
 ("lap_hud","81:8195","81:81D3",0,-14),
 ("late_pre_contractions","81:81D4","81:820F",0,-14),
 ("late_after_delete_1","81:8216","81:8226",-6,-20),
 ("late_after_delete_2","81:822D","81:823D",-12,-26),
 ("late_after_delete_3","81:8244","81:8252",-18,-32),
 ("late_after_delete_4","81:825A","81:8277",-25,-39),
 ("late_after_delete_5","81:827C","81:82E0",-29,-43),
]
USA_ONLY_DELETIONS=[
 ("pal_delete_1","81:8210","81:8215","8a 99 39 0e a5 00","TXA; STA $0E39,Y; LDA $00"),
 ("pal_delete_2","81:8227","81:822C","8a 99 3d 0e a5 00","TXA; STA $0E3D,Y; LDA $00"),
 ("pal_delete_3","81:823E","81:8243","8a 99 41 0e a5 00","TXA; STA $0E41,Y; LDA $00"),
 ("pal_delete_4","81:8253","81:8259","99 35 0e 8a 99 45 0e","STA $0E35,Y; TXA; STA $0E45,Y"),
 ("pal_delete_5","81:8278","81:827B","ea ea ea ea","NOP; NOP; NOP; NOP"),
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
  d=trace(blob); seed_entries(d,[cpu_to_offset("81:8050")]); ds[name]=d

 rows=[]
 for name,s,e,proto_shift,europe_shift in REGIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  shifts={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":proto_shift,"europe-retail":europe_shift}
  for build,shift in shifts.items():
   if shift is None:
    continue
   blob=blobs[build]; bs=us+shift; be=ue+shift
   row["builds"][build]={
    "start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":shift,
    "size":be-bs+1,"size_delta":0,
    "similarity":round(similarity(usa[us:ue+1],blob[bs:be+1]),6),
    **roles(ds[build],bs,be),
    "sha256":hashlib.sha256(blob[bs:be+1]).hexdigest(),
   }
  rows.append(row)

 eu_s=cpu_to_offset("81:8102"); eu_e=cpu_to_offset("81:8109"); europe=blobs["europe-retail"]
 europe_norm={
  "name":"frame_normalization_europe_shape","kind":"code",
  "usa_reference_start":"81:8102","usa_reference_end":"81:8117",
  "start":"81:8102","end":"81:8109","size":8,"size_delta_vs_usa":-14,
  **roles(ds["europe-retail"],eu_s,eu_e),
  "hex":europe[eu_s:eu_e+1].hex(" "),
 }

 deletions=[]
 for name,s,e,expected_hex,instructions in USA_ONLY_DELETIONS:
  us,ue=cpu_to_offset(s),cpu_to_offset(e); hx=usa[us:ue+1].hex(" ")
  deletions.append({
   "name":name,"usa_start":s,"usa_end":e,"size":ue-us+1,
   "hex":hx,"expected_hex":expected_hex,"instructions":instructions,
   "usa_roles":roles(ds["usa-retail"],us,ue),
   "legacy_beta_identical":blobs["legacy-beta"][us:ue+1]==usa[us:ue+1],
   "pal_prototype_omits":True,"europe_retail_omits":True,
  })

 return {
  "schema_version":1,"island":"Race_HandleCheckpointFinish",
  "usa_start":"81:8050","usa_end":"81:82E0",
  "usa_size":cpu_to_offset("81:82E0")-cpu_to_offset("81:8050")+1,
  "dispatch":{"object_code":"0x14","entry":"81:8050","shared_exit":"81:82E1"},
  "lineage_edits":{
   "europe_only_frame_normalization":europe_norm,
   "pal_line_usa_only_deletions":deletions,
   "pal_line_total_contraction":-29,
   "europe_total_contraction_after_both_lineages":-43,
  },
  "regions":rows,
 }

def render(r):
 lines=[
  "# Checkpoint / finish structural island: USA 81:8050..82E0","",
  "Object code 0x14 dispatches to 81:8050. The handler rejoins the shared object-handler continuation at 81:82E1.","",
  "| Region | USA bytes | PAL prototype | Europe | Legacy beta |",
  "|---|---:|---|---|---|",
 ]
 for x in r["regions"]:
  def cell(build):
   q=x["builds"].get(build)
   if not q: return "none"
   return f"{q['start']}..{q['end']} ({q['shift']:+d}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines += ["","## Lineage edits","",
  "Europe retail alone contracts the USA 22-byte frame-normalization block at 81:8102..8117 to 8 bytes at 81:8102..8109, contributing -14 bytes before the later shared PAL-line edits.","",
  "The PAL prototype and Europe both omit five instruction-aligned USA blocks later in the handler:"]
 for d in r["lineage_edits"]["pal_line_usa_only_deletions"]:
  lines.append(f"- {d['usa_start']}..{d['usa_end']} ({d['size']} bytes): {d['hex']} = {d['instructions']}")
 lines += ["",
  "Those five deletions total 29 bytes. Therefore the PAL prototype finishes the handler at shift -29 relative to USA; Europe finishes at -43 after layering the earlier -14 timer contraction.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("CHECKPOINT_FINISH_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
