#!/usr/bin/env python3
"""Recover the full Race_BuildRacerOAMState structural island across preserved builds."""
from __future__ import annotations
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/racer-oam-structure-island.json"
OUTM=ROOT/"analysis/generated/racer-oam-structure-island.md"
REGIONS=[
 ("entry_mode_setup","82:ACA5","82:ACF2","code"),
 ("p1_projection","82:ACF3","82:ADA7","code"),
 ("p2_dispatch_setup","82:ADA8","82:ADC0","code"),
 ("p2_projection_shared_camera","82:ADC1","82:AE57","code"),
 ("p2_projection_alt_camera","82:AE5A","82:AF30","code"),
 ("split_mode_setup","82:AF31","82:AF4E","code"),
 ("split_p2_projection","82:AF4F","82:AFD4","code"),
 ("split_p1_projection","82:AFD5","82:B056","code"),
 ("post_mode_setup","82:B057","82:B07A","code"),
 ("post_p2_adjust","82:B07B","82:B0E5","code"),
 ("post_p1_adjust","82:B0E6","82:B150","code"),
 ("post_final_flags","82:B151","82:B17F","code"),
]

def best_shift(src,dst,start,end,center=0,radius=192):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def roles(d,start,end):
 op=param=other=0
 for off in range(start,end+1):
  role=d.code_map[off]
  if role & d.OP_CODE: op+=1
  elif role & d.OP_PARAM: param+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":param,"unreached_or_data_bytes":other}

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 aligns={}
 for build,blob in blobs.items():
  per={}; previous_shift=0
  for index,(name,s,e,kind) in enumerate(REGIONS):
   st=cpu_to_offset(s); en=cpu_to_offset(e)
   if build=="usa-retail":
    shift,sim=(0,1.0)
   elif index==0:
    shift,sim=best_shift(usa,blob,st,en,center=0,radius=192)
   else:
    shift,sim=best_shift(usa,blob,st,en,center=previous_shift,radius=12)
   previous_shift=shift
   per[name]={"shift":shift,"similarity":round(sim,6),"start":offset_to_cpu(st+shift),"end":offset_to_cpu(en+shift)}
  aligns[build]=per
 analyzers={}
 for build,blob in blobs.items():
  d=trace(blob)
  seed_entries(d,[cpu_to_offset(s)+aligns[build][name]["shift"] for name,s,e,kind in REGIONS if kind=="code"])
  analyzers[build]={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s)+aligns[build][name]["shift"]; en=cpu_to_offset(e)+aligns[build][name]["shift"]
   analyzers[build][name]=roles(d,st,en)
 rows=[]
 for name,s,e,kind in REGIONS:
  us=cpu_to_offset(s); ue=cpu_to_offset(e)
  row={"name":name,"kind":kind,"size":ue-us+1,"usa_start":s,"usa_end":e,"builds":{}}
  for build,blob in blobs.items():
   a=aligns[build][name]; bs=us+a["shift"]; be=ue+a["shift"]
   row["builds"][build]={**a,**analyzers[build][name],"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
  rows.append(row)
 return {
  "schema_version":1,
  "island":"Race_BuildRacerOAMState 82:ACA5..B17F",
  "boundary_basis":{
   "entry":"named long-entry wrapper at 82:ACA1 calls 82:ACA5",
   "known_projections":"trusted prior homologs bound USA ACF3..ADA7 and ADC1..AE57",
   "mode_branches":"control flow separates shared-camera, alternate-camera and split-camera projection paths",
   "exit":"all surviving paths converge on the adjustment tail ending RTS at 82:B17F",
  },
  "regions":rows,
 }

def render(r):
 lines=["# Racer OAM / viewport structural island: 82:ACA5..B17F","",
 "This report expands the two already-trusted racer projection homologs into the full named OAM-state builder, including alternate camera paths and the shared post-projection tail.","",
 "| Region | Size | USA | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|---|"]
 for x in r["regions"]:
  def cell(build):
   b=x["builds"][build]
   return f"{b['start']}..{b['end']} ({b['shift']:+d}, sim {b['similarity']:.3f}; op {b['opcode_bytes']}, unreached/data {b['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {cell('usa-retail')} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
 lines+=["","## Structural interpretation","",
 "- entry_mode_setup clears per-racer offscreen state and selects the initial camera/mode path.",
 "- p1_projection is the previously trusted world/camera-to-screen P1 block.",
 "- p2_dispatch_setup selects whether P2 shares camera state or follows an alternate presentation path.",
 "- p2_projection_shared_camera is the previously trusted P2 sibling block.",
 "- p2_projection_alt_camera handles a distinct P2 projection path used by another display mode.",
 "- split_mode_setup selects and clears split-camera sprite state.",
 "- split_p2_projection and split_p1_projection project the two racers against paired camera coordinates.",
 "- post_mode_setup begins the common final adjustment path.",
 "- post_p2_adjust and post_p1_adjust apply per-racer coordinate/flag correction.",
 "- post_final_flags handles the final mode-specific sprite flags and returns.",
 "","These labels describe control-flow/presentation roles visible in the routine; they do not assign semantics to every flag field."]
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("RACER_OAM_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
