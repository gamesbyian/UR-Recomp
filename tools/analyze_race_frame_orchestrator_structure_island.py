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
USA_START="83:CBCC"
USA_END="83:CD9F"
OUTJ=ROOT/"analysis/generated/race-frame-orchestrator-structure-island.json"
OUTM=ROOT/"analysis/generated/race-frame-orchestrator-structure-island.md"

def best_shift(src,dst,start,end,center=0,radius=256):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best

def local_shift_profile(src,dst,start,end,center,window=16,radius=64):
 out=[]
 pos=start
 while pos<=end:
  hi=min(pos+window-1,end)
  shift,sim=best_shift(src,dst,pos,hi,center=center,radius=radius)
  out.append({"usa_start":offset_to_cpu(pos),"usa_end":offset_to_cpu(hi),"shift":shift,"similarity":round(sim,6)})
  pos=hi+1
 return out

def classify(d,start,end):
 op=param=other=0; opcode_starts=[]
 for off in range(start,end+1):
  role=d.code_map[off]
  if role & d.OP_CODE:
   op+=1; opcode_starts.append(offset_to_cpu(off))
  elif role & d.OP_PARAM: param+=1
  else: other+=1
 return {"opcode_bytes":op,"operand_bytes":param,"unreached_or_data_bytes":other,"opcode_starts":opcode_starts}

def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}
 usa=blobs["usa-retail"]; us=cpu_to_offset(USA_START); ue=cpu_to_offset(USA_END)
 result={"schema_version":1,"island":"race-frame orchestration corridor","usa_start":USA_START,"usa_end":USA_END,"usa_size":ue-us+1,
         "seed_basis":"USA 83:CBCC is SEP #$30, independently establishing 8-bit A/X before the setup and frame-loop corridor.",
         "loop":{"header":"83:CC62","back_edge":"83:CD9D JMP $CC62"},
         "known_calls":{"input":"82:AA6A","racer_update":"82:89B5 wrapper","oam":"82:ACA1","player_state_marshal":"81:8D14"},
         "builds":{},"regions":[]}
 for build,blob in blobs.items():
  shift,sim=(0,1.0) if build=="usa-retail" else best_shift(usa,blob,us,ue)
  st=us+shift; en=ue+shift
  d=trace(blob); seed_entries(d,[st])
  roles=classify(d,st,en)
  result["builds"][build]={"start":offset_to_cpu(st),"end":offset_to_cpu(en),"shift":shift,"similarity":round(sim,6),
                           "size":en-st+1,"size_delta":0,**roles,"sha256":hashlib.sha256(blob[st:en+1]).hexdigest()}
  if build!="usa-retail":
   result["builds"][build]["local_shift_profile_16byte"]=local_shift_profile(usa,blob,us,ue,shift)
 result["regions"].append({"name":"Race_FrameOrchestrationCorridor","kind":"code","usa_start":USA_START,"usa_end":USA_END,
                           "size":ue-us+1,"builds":{name:{k:v for k,v in info.items() if k!="opcode_starts"} for name,info in result["builds"].items()}})
 return result

def render(r):
 lines=["# Race-frame orchestration corridor: USA 83:CBCC..CD9F","",
 "The probe begins at an explicit SEP #$30 so M/X state is independently established before the setup and loop body. It includes the frame-loop header at CC62, the ordered service-call chain, and the JMP $CC62 back-edge at CD9D.","",
 "| Build | Range | Shift | Similarity | Opcode | Operand | Unreached/data |",
 "|---|---|---:|---:|---:|---:|---:|"]
 for name,b in r["builds"].items():
  lines.append(f"| {name} | {b['start']}..{b['end']} | {b['shift']:+d} | {b['similarity']:.3f} | {b['opcode_bytes']} | {b['operand_bytes']} | {b['unreached_or_data_bytes']} |")
 lines+=["","Known calls inside the USA corridor include input decode, racer simulation, player-state marshaling, racer OAM construction, and multiple HUD/race services. This artifact recovers orchestration structure, not semantic names for every callee.",""]
 return "\n".join(lines)

def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)+"\n"); print(render(r)); print("RACE_FRAME_ORCHESTRATOR_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
