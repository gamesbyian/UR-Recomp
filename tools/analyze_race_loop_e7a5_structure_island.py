#!/usr/bin/env python3
"""Recover the race-loop support routine at USA 83:E7A5..EBCB."""
from __future__ import annotations
import hashlib,json,difflib
from compare_europe_usa_snes2asm_homologs import ROOT,trace,seed_entries,cpu_to_offset,offset_to_cpu

ROMS={
 "usa-retail":ROOT/"reference/roms/retail/Uniracers_USA.sfc",
 "pal-prototype-1994-11-29":ROOT/"reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
 "europe-retail":ROOT/"reference/roms/retail/Unirally_Europe.sfc",
 "legacy-beta":ROOT/"reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ=ROOT/"analysis/generated/race-loop-e7a5-structure-island.json"
OUTM=ROOT/"analysis/generated/race-loop-e7a5-structure-island.md"
EC46=ROOT/"analysis/generated/ec46-coordinate-window-structure-island.json"
START,END="83:E7A5","83:EBCB"
CALLSITE="83:CD3D"

def best_shift(src,dst,start,end,center=0,radius=128):
 block=src[start:end+1]; best=(center,-1.0)
 for sh in range(center-radius,center+radius+1):
  lo=start+sh; hi=lo+len(block)
  if lo<0 or hi>len(dst): continue
  score=sum(a==b for a,b in zip(block,dst[lo:hi]))/len(block)
  if score>best[1]: best=(sh,score)
 return best

def edit_script(src,dst,start,end,initial_shift,extra=128):
 usa=src[start:end+1]
 other_start=start+initial_shift
 other=dst[other_start:other_start+len(usa)+extra]
 sm=difflib.SequenceMatcher(None,usa,other,autojunk=False)
 ops=[]
 for tag,i1,i2,j1,j2 in sm.get_opcodes():
  if tag=="equal" and i2-i1<8:
   continue
  ops.append({
   "tag":tag,
   "usa_start":offset_to_cpu(start+i1) if i1<len(usa) else None,
   "usa_end":offset_to_cpu(start+i2-1) if i2>i1 else None,
   "usa_size":i2-i1,
   "other_start":offset_to_cpu(other_start+j1) if j1<len(other) else None,
   "other_end":offset_to_cpu(other_start+j2-1) if j2>j1 else None,
   "other_size":j2-j1,
  })
 return ops

def local_profile(src,dst,start,end,center,window=48,radius=160):
 out=[]; pos=start
 while pos<=end:
  hi=min(end,pos+window-1)
  sh,sim=best_shift(src,dst,pos,hi,center,radius)
  out.append({"usa_start":offset_to_cpu(pos),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sim,6)})
  center=sh
  pos=hi+1
 return out

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
 adjacent=json.loads(EC46.read_text())
 table=next(r for r in adjacent["regions"] if r["name"]=="coordinate_step_table")
 us,ue=cpu_to_offset(START),cpu_to_offset(END)
 centers={"usa-retail":0,"legacy-beta":0,"pal-prototype-1994-11-29":-10,"europe-retail":28}
 bounds={}
 for build,blob in blobs.items():
  if build in ("usa-retail","legacy-beta"):
   bs,be=us,ue
  else:
   prefix_end=min(ue,us+239)
   sh,_=best_shift(usa,blob,us,prefix_end,centers[build],64)
   bs=us+sh
   table_start=cpu_to_offset(table["builds"][build]["start"])
   be=table_start-27
  bounds[build]={"start_offset":bs,"end_offset":be,"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift_start":bs-us,"shift_end":be-ue,"size":be-bs+1,"size_delta":(be-bs+1)-(ue-us+1)}
 ds={}
 for build,blob in blobs.items():
  d=trace(blob); seed_entries(d,[bounds[build]["start_offset"]]); ds[build]=d
 builds={}
 usa_block=usa[us:ue+1]
 for build,blob in blobs.items():
  q=bounds[build]; bs,be=q["start_offset"],q["end_offset"]
  block=blob[bs:be+1]
  sm=difflib.SequenceMatcher(None,usa_block,block,autojunk=False)
  matching=sum(m.size for m in sm.get_matching_blocks())
  ops=sm.get_opcodes()
  edits=[{
    "tag":tag,
    "usa_start":offset_to_cpu(us+i1) if i1<len(usa_block) else None,
    "usa_end":offset_to_cpu(us+i2-1) if i2>i1 else None,
    "usa_size":i2-i1,
    "other_start":offset_to_cpu(bs+j1) if j1<len(block) else None,
    "other_end":offset_to_cpu(bs+j2-1) if j2>j1 else None,
    "other_size":j2-j1,
   } for tag,i1,i2,j1,j2 in ops if tag!="equal"]
  info={
   "start":q["start"],"end":q["end"],"shift":q["shift_start"],"shift_start":q["shift_start"],"shift_end":q["shift_end"],
   "size":q["size"],"size_delta":q["size_delta"],
   "similarity":round(matching/max(len(usa_block),len(block)),6),
   **roles(ds[build],bs,be),
   "sha256":hashlib.sha256(block).hexdigest(),
   "matching_bytes":matching,
   "edit_count":len(edits),
   "edit_script":edits,
  }
  if build not in ("usa-retail","legacy-beta"):
   info["local_shift_profile_48byte"]=local_profile(usa,blob,us,ue,centers[build])
  builds[build]=info
 return {
  "schema_version":1,
  "island":"RaceLoopE7A5",
  "usa_start":START,"usa_end":END,"next_entry":"83:EBCC",
  "boundary_basis":{
   "entry":"83:E7A5 is called directly from the accepted race-frame orchestrator at 83:CD3D.",
   "usa_exit":"83:EBCB is RTS; 83:EBCC begins a separate 26-byte helper.",
   "regional_exit":"The accepted EC46 island fixes the following step-table start in each build; subtracting the 26-byte EBCC helper and one byte yields the regional E7A5 exit."
  },
  "known_callers":[{"callsite":CALLSITE,"source":"race-frame-orchestrator"}],
  "regions":[{"name":"race_loop_e7a5_body","kind":"code","usa_start":START,"usa_end":END,"size":ue-us+1,"builds":builds}],
 }

def render(r):
 x=r["regions"][0]
 def cell(b):
  q=x["builds"][b]
  return f"{q['start']}..{q['end']} (size {q['size']}; delta {q['size_delta']:+d}; shifts {q['shift_start']:+d}->{q['shift_end']:+d}; match {q['matching_bytes']}/{max(x['size'],q['size'])}; edits {q['edit_count']}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
 return "\n".join([
  "# Race-loop E7A5 structural island","",
  "USA `83:E7A5..EBCB` is a race-loop support routine called from the recovered orchestrator at `83:CD3D`. USA/legacy beta end at `83:EBCB`; the PAL-line builds contain inserted/rewritten blocks and therefore grow before the separate 26-byte helper that precedes the already-recovered EC46 step table.","",
  "| USA bytes | PAL prototype | Europe | Legacy beta |","|---:|---|---|---|",
  f"| {x['size']} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |","",
  "## Boundary and divergence result","",
  "- USA retail and legacy beta are byte-identical at 1,063 bytes.",
  "- PAL prototype starts at shift `-10` but ends at `+36`, yielding 1,109 bytes (+46).",
  "- Europe starts at `+28` but ends at `+72`, yielding 1,107 bytes (+44).",
  "- All four regional extents are fully analyzer-reached code. The PAL-line variants contain many small operand/code edits plus several inserted blocks, so a single constant-shift opcode comparison is invalid for this routine.",
  "- The regional exits are anchored by the accepted EC46 step-table homologs: the excluded EBCC helper remains 26 bytes immediately before that table in each build.",""
 ])

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("RACE_LOOP_E7A5_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
