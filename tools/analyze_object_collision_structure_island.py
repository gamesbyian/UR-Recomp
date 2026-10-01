#!/usr/bin/env python3
"""Recover the bank-81 object/collision dispatch island across all preserved builds."""
from __future__ import annotations
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu
ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/object-collision-structure-island.json"
OUTM=ROOT/"analysis/generated/object-collision-structure-island.md"
REGIONS=[
 ("long_entry_wrapper","81:82E2","81:82E5","code"),
 ("dispatcher_head","81:82E6","81:831F","code"),
 ("handler_pointer_prefix","81:8320","81:833D","data"),
 ("dispatcher_tail","81:833E","81:8340","code"),
 ("handler_8341","81:8341","81:8371","code"),
 ("lookup_8372","81:8372","81:83A3","data"),
 ("handler_83A4","81:83A4","81:84D1","code"),
]

def best_shift(src,dst,start,end,radius=192):
 block=src[start:end+1]; best=(0,-1.0)
 for shift in range(-radius,radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def roles(d,start,end):
 op=param=other=0
 for off in range(start,end+1):
  r=d.code_map[off]
  if r & d.OP_CODE: op+=1
  elif r & d.OP_PARAM: param+=1
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
   per[name]={"shift":shift,"similarity":round(sim,6),"start":offset_to_cpu(st+shift),"end":offset_to_cpu(en+shift)}
  aligns[build]=per
 analyzers={}
 for build,blob in blobs.items():
  d=trace(blob)
  seeds=[]
  for name,s,e,kind in REGIONS:
   if kind=="code": seeds.append(cpu_to_offset(s)+aligns[build][name]["shift"])
  seed_entries(d,seeds)
  analyzers[build]={}
  for name,s,e,kind in REGIONS:
   st=cpu_to_offset(s)+aligns[build][name]["shift"]; en=cpu_to_offset(e)+aligns[build][name]["shift"]
   analyzers[build][name]=roles(d,st,en)
 rows=[]
 for name,s,e,kind in REGIONS:
  us=cpu_to_offset(s); ue=cpu_to_offset(e); row={"name":name,"kind":kind,"size":ue-us+1,"usa_start":s,"usa_end":e,"builds":{}}
  for build,blob in blobs.items():
   a=aligns[build][name]; bs=us+a["shift"]; be=ue+a["shift"]
   row["builds"][build]={**a,**analyzers[build][name],"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
  rows.append(row)
 jt=usa[cpu_to_offset("81:8320"):cpu_to_offset("81:833D")+1]
 jtwords=[int.from_bytes(jt[i:i+2],"little") for i in range(0,len(jt),2)]
 jt_by_build={}
 for build,blob in blobs.items():
  st=cpu_to_offset(aligns[build]["handler_pointer_prefix"]["start"])
  raw=blob[st:st+len(jt)]
  jt_by_build[build]=[f"{int.from_bytes(raw[i:i+2],'little'):04X}" for i in range(0,len(raw),2)]
 lut=usa[cpu_to_offset("81:8372"):cpu_to_offset("81:83A3")+1]
 lutwords=[int.from_bytes(lut[i:i+2],"little",signed=True) for i in range(0,len(lut),2)]
 gap_info={}
 for build,blob in blobs.items():
  tail_end=cpu_to_offset(aligns[build]["dispatcher_tail"]["end"])
  next_start=cpu_to_offset(aligns[build]["handler_8341"]["start"])
  if next_start>tail_end+1:
   gap=blob[tail_end+1:next_start]
   gap_info[build]={"size":len(gap),"start":offset_to_cpu(tail_end+1),"end":offset_to_cpu(next_start-1),"hex":gap.hex(" ")}
  else:
   gap_info[build]={"size":0,"start":None,"end":None,"hex":""}
 return {"schema_version":2,"island":"bank-81 object/collision dispatch structure","regions":rows,"post_dispatch_gap":gap_info,
   "handler_pointer_prefix":{"size":len(jt),"entries":len(jtwords),"usa_words":[f"{x:04X}" for x in jtwords],"words_by_build":jt_by_build,"caveat":"JSR ($8320,X) is guarded only by X < 0x003C, so this 30-byte run is a proven pointer prefix, not yet a proven complete indirect domain."},
   "lookup_8372":{"size":len(lut),"entries":len(lutwords),"usa_signed_words":lutwords}}

def render(r):
 lines=["# Object/collision structural island: 81:82E2..84D1","",
 "Boundaries come from direct long-entry calls, explicit RTS/RTL instructions, the indexed indirect dispatch at `81:831B`, and four-ROM structural alignment.","",
 "| Region | Kind | Size | USA | PAL prototype | Europe | Legacy beta |","|---|---|---:|---|---|---|---|"]
 for x in r["regions"]:
  def cell(build):
   b=x["builds"][build]; return "{}..{} ({:+d}, sim {:.3f}; op {}, data/unreached {})".format(b["start"],b["end"],b["shift"],b["similarity"],b["opcode_bytes"],b["unreached_or_data_bytes"])
  lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(x["name"],x["kind"],x["size"],cell("usa-retail"),cell("pal-prototype-1994-11-29"),cell("europe-retail"),cell("legacy-beta")))
 jt=r["handler_pointer_prefix"]; lut=r["lookup_8372"]
 lines+=["","## Post-dispatch gap",""]
 for build,g in r["post_dispatch_gap"].items():
  if g["size"]:
   lines.append(f"- {build}: {g['start']}..{g['end']} ({g['size']} bytes): {g['hex']}")
  else:
   lines.append(f"- {build}: none")
 lines+=["","## Embedded handler table","",f"- {jt['size']} bytes / {jt['entries']} little-endian words.","- USA entries: "+" ".join(jt["usa_words"]),"- PAL prototype entries: "+" ".join(jt["words_by_build"]["pal-prototype-1994-11-29"]),"- Europe entries: "+" ".join(jt["words_by_build"]["europe-retail"]),"- `JSR ($8320,X)` proves these words are an embedded handler-pointer prefix. Because the guard is only `X < 0x003C`, do **not** treat the 30-byte prefix as the complete indirect domain without a tighter X-value proof.","","## Lookup table after handler_8341","",f"- {lut['size']} bytes / {lut['entries']} signed words.","- USA signed values: "+" ".join(str(x) for x in lut["usa_signed_words"]),"- The next executable entry begins at `81:83A4`; linear disassembly beginning at `83A3` is a one-byte code/data boundary error.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("OBJECT_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
