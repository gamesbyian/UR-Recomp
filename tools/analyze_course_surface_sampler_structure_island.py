#!/usr/bin/env python3
"""Probe the per-racer course runtime surface sampler across preserved builds."""
from __future__ import annotations
import hashlib, json
from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/course-surface-sampler-structure-island.json"
OUTM=ROOT/"analysis/generated/course-surface-sampler-structure-island.md"
USA_START="81:8B95"
USA_END="81:8D13"

def best_shift(src,dst,start,end,center=0,radius=192):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def role_spans(d,start,end):
 roles=[]; current=None; span_start=start
 def label(role):
  if role & d.OP_CODE: return "opcode"
  if role & d.OP_PARAM: return "operand"
  return "unreached_or_data"
 for off in range(start,end+1):
  lab=label(d.code_map[off])
  if current is None:
   current=lab; span_start=off
  elif lab!=current:
   roles.append({"role":current,"start":offset_to_cpu(span_start),"end":offset_to_cpu(off-1),"size":off-span_start})
   current=lab; span_start=off
 if current is not None:
  roles.append({"role":current,"start":offset_to_cpu(span_start),"end":offset_to_cpu(end),"size":end-span_start+1})
 counts={"opcode_bytes":0,"operand_bytes":0,"unreached_or_data_bytes":0}
 for span in roles:
  if span["role"]=="opcode": counts["opcode_bytes"]+=span["size"]
  elif span["role"]=="operand": counts["operand_bytes"]+=span["size"]
  else: counts["unreached_or_data_bytes"]+=span["size"]
 return counts,roles

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}
 usa=blobs["usa-retail"]; us=cpu_to_offset(USA_START); ue=cpu_to_offset(USA_END)
 align={}
 for build,blob in blobs.items():
  shift,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue)
  align[build]={"shift":shift,"similarity":round(sim,6),"start":offset_to_cpu(us+shift),"end":offset_to_cpu(ue+shift)}
 out={"schema_version":1,"island":"per-racer course runtime surface sampler","usa_start":USA_START,"usa_end":USA_END,"usa_size":ue-us+1,
      "call_context":{"p1_caller":"81:8DD9","p2_caller":"81:8F2D","preceded_by":"JSR 81:9E2A collision/contact-shape construction","followed_by":"JSR 81:8FB8 later collision path"},
      "builds":{},"regions":[]}
 for build,blob in blobs.items():
  d=trace(blob); st=us+align[build]["shift"]; en=ue+align[build]["shift"]
  seed_entries(d,[st])
  counts,spans=role_spans(d,st,en)
  out["builds"][build]={**align[build],"size":en-st+1,"size_delta":0,**counts,"role_spans":spans,
      "sha256":hashlib.sha256(blob[st:en+1]).hexdigest()}
 out["regions"].append({
   "name":"Course_SampleRuntimeSurface",
   "kind":"code",
   "usa_start":USA_START,
   "usa_end":USA_END,
   "size":ue-us+1,
   "builds":{name:{k:v for k,v in info.items() if k!="role_spans"} for name,info in out["builds"].items()},
 })
 return out

def render(r):
 lines=["# Course runtime surface sampler: USA 81:8B95..8D13","",
 "This is a coarse first pass over the routine called from both player paths between collision-shape construction and the later collision path. The purpose is to establish trustworthy code/data reachability before introducing internal structural cuts.","",
 "| Build | Range | Shift | Similarity | Opcode bytes | Operand bytes | Unreached/data |",
 "|---|---|---:|---:|---:|---:|---:|"]
 for name,b in r["builds"].items():
  lines.append(f"| {name} | {b['start']}..{b['end']} | {b['shift']:+d} | {b['similarity']:.3f} | {b['opcode_bytes']} | {b['operand_bytes']} | {b['unreached_or_data_bytes']} |")
 lines+=["","## USA role spans",""]
 for span in r["builds"]["usa-retail"]["role_spans"]:
  lines.append(f"- {span['role']}: {span['start']}..{span['end']} ({span['size']} bytes)")
 return "\n".join(lines)+"\n"

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("COURSE_SURFACE_SAMPLER_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
