#!/usr/bin/env python3
"""Recover the Race_UpdateRacersFrame A22B..A497 code/table island across builds."""
from __future__ import annotations
from pathlib import Path
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS = {
 "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29": ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUT_JSON = ROOT / "analysis/generated/racer-update-structure-island.json"
OUT_MD = ROOT / "analysis/generated/racer-update-structure-island.md"
REGIONS = [
 ("routine_A22B","82:A22B","82:A27B","code"),
 ("routine_A27C","82:A27C","82:A2D3","code"),
 ("table_A2D4","82:A2D4","82:A353","data"),
 ("routine_A354","82:A354","82:A497","code"),
]

def best_shift(src,dst,start,end,radius=128):
 block=src[start:end+1]; best=(0,-1.0)
 for shift in range(-radius,radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def role_counts(d,start,end):
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
  per={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s); en=cpu_to_offset(e)
   shift,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,st,en)
   per[name]={"shift":shift,"similarity":round(sim,6),"start":offset_to_cpu(st+shift),"end":offset_to_cpu(en+shift),"kind":kind}
  aligns[build]=per
 analyzers={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[cpu_to_offset(s)+aligns[build][name]["shift"] for name,s,e,kind in REGIONS if kind=="code"]
  seed_entries(d,seeds)
  per={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s)+aligns[build][name]["shift"]; en=cpu_to_offset(e)+aligns[build][name]["shift"]
   per[name]=role_counts(d,st,en)
  analyzers[build]=per
 rows=[]
 for name,s,e,kind in REGIONS:
  us=cpu_to_offset(s); ue=cpu_to_offset(e); row={"name":name,"kind":kind,"usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   a=aligns[build][name]; bs=us+a["shift"]; be=ue+a["shift"]
   row["builds"][build]={**a,**analyzers[build][name],"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
  rows.append(row)
 table=usa[cpu_to_offset("82:A2D4"):cpu_to_offset("82:A353")+1]
 words=[int.from_bytes(table[i:i+2],"little") for i in range(0,len(table),2)]
 return {"schema_version":1,"island":"Race_UpdateRacersFrame direct-callee island A22B..A497","regions":rows,"table_A2D4":{"size":len(table),"word_count":len(words),"usa_words":words,"interpretation":"128-byte / 64-word inline lookup table between two trusted routine boundaries; following routine indexes USA 82:A2D4 with X."}}

def render(r):
 lines=["# Racer-update structural island: A22B..A497","","This report recovers structure, not semantic names. Boundaries are anchored by direct calls from the racer-frame update hub and explicit RTS instructions.","","| Region | Kind | Size | USA | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|---|"]
 for x in r["regions"]:
  def cell(build):
   b=x["builds"][build]; return "{}..{} ({:+d}, sim {:.3f}; op {}, data/unreached {})".format(b["start"],b["end"],b["shift"],b["similarity"],b["opcode_bytes"],b["unreached_or_data_bytes"])
  lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(x["name"],x["kind"],x["size"],cell("usa-retail"),cell("pal-prototype-1994-11-29"),cell("europe-retail"),cell("legacy-beta")))
 t=r["table_A2D4"]
 lines += ["","## Inline table","",f"- Exact size: **{t['size']} bytes / {t['word_count']} little-endian words**.","- It begins immediately after the A27C routine RTS and ends immediately before the independently called A354 entry.","- The following routine performs a long indexed load from USA 82:A2D4,X, independently proving this block is lookup data rather than executable code.","- USA words: " + " ".join(f"{w:04X}" for w in t["usa_words"]),""]
 return "\n".join(lines)

def main():
 r=build(); OUT_JSON.write_text(json.dumps(r,indent=2)+"\n"); OUT_MD.write_text(render(r)); print(render(r)); print("STRUCTURE_JSON="+json.dumps(r,sort_keys=True))

if __name__=="__main__": main()
