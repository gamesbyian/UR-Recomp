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
 ("entry_time_prefix","81:8050","81:8101"),
 ("frame_normalization","81:8102","81:8117"),
 ("post_normalization","81:8118","81:8194"),
 ("lap_hud","81:8195","81:81D3"),
 ("late_handler","81:81D4","81:82E0"),
]

def best_shift(src,dst,start,end,center=0,radius=64):
 block=src[start:end+1]; best=(center,-1.0)
 for shift in range(center-radius,center+radius+1):
  a=start+shift; b=a+len(block)
  if a<0 or b>len(dst): continue
  score=sum(x==y for x,y in zip(block,dst[a:b]))/len(block)
  if score>best[1]: best=(shift,score)
 return best
def local_profile(src,dst,start,end,center,window=16):
 out=[]; pos=start
 while pos<=end:
  hi=min(end,pos+window-1)
  sh,sc=best_shift(src,dst,pos,hi,center)
  out.append({"usa_start":offset_to_cpu(pos),"usa_end":offset_to_cpu(hi),"shift":sh,"similarity":round(sc,6)})
  pos=hi+1
 return out


def opcode_starts(d,start,end):
 return [off for off in range(start,end+1) if d.code_map[off]&d.OP_CODE]

def boundary_candidates(src,dst,sd,td,start,end,centers):
 """Find instruction-aligned USA cut points where the preferred homolog shift changes."""
 starts=opcode_starts(sd,start,end)
 out=[]
 for off in starts:
  best=None
  for shift in centers:
   toff=off+shift
   if toff<0 or toff>=len(dst) or not (td.code_map[toff]&td.OP_CODE):
    continue
   # Score from this opcode through up to the next 23 bytes, stopping at region end.
   hi=min(end,off+23)
   n=hi-off+1
   score=sum(src[off+i]==dst[toff+i] for i in range(n))/n
   cand=(score,shift)
   if best is None or cand>best: best=cand
  if best:
   out.append({"usa":offset_to_cpu(off),"shift":best[1],"similarity":round(best[0],6)})
 return out

def roles(d,s,e):
 op=pa=ot=0
 for x in range(s,e+1):
  r=d.code_map[x]
  if r&d.OP_CODE: op+=1
  elif r&d.OP_PARAM: pa+=1
  else: ot+=1
 return {"opcode_bytes":op,"operand_bytes":pa,"unreached_or_data_bytes":ot}
def sim(a,b): return sum(x==y for x,y in zip(a,b))/max(len(a),len(b))
def build():
 blobs={k:p.read_bytes() for k,p in ROMS.items()}; usa=blobs["usa-retail"]
 ds={}
 for name,blob in blobs.items():
  d=trace(blob); seed_entries(d,[cpu_to_offset("81:8050")]); ds[name]=d
 rows=[]
 for idx,(name,s,e) in enumerate(REGIONS):
  us,ue=cpu_to_offset(s),cpu_to_offset(e)
  row={"name":name,"kind":"code","usa_start":s,"usa_end":e,"size":ue-us+1,"builds":{}}
  for build,blob in blobs.items():
   shift=0 if build!="europe-retail" or idx<2 else -14
   delta=-14 if build=="europe-retail" and idx==1 else 0
   bs=us+shift; be=ue+shift+delta
   row["builds"][build]={"start":offset_to_cpu(bs),"end":offset_to_cpu(be),"shift":shift,
      "size":be-bs+1,"size_delta":delta,
      "similarity":round(sim(usa[us:ue+1],blob[bs:be+1]),6),
      **roles(ds[build],bs,be),"sha256":hashlib.sha256(blob[bs:be+1]).hexdigest()}
   if idx==4 and build in {"pal-prototype-1994-11-29","europe-retail"}:
    row["builds"][build]["local_shift_profile_16byte"]=local_profile(usa,blob,us,ue,shift)
    row["builds"][build]["local_shift_profile_4byte"]=local_profile(usa,blob,us,ue,shift,window=4)
  rows.append(row)
 late_start,late_end=cpu_to_offset("81:81D4"),cpu_to_offset("81:82E0")
 proto_candidates=boundary_candidates(usa,blobs["pal-prototype-1994-11-29"],ds["usa-retail"],ds["pal-prototype-1994-11-29"],late_start,late_end,[0,-6,-12,-18,-25,-29])
 europe_candidates=boundary_candidates(usa,blobs["europe-retail"],ds["usa-retail"],ds["europe-retail"],late_start,late_end,[-14,-20,-26,-32,-39,-43])
 return {"schema_version":1,"island":"Race_HandleCheckpointFinish","usa_start":"81:8050","usa_end":"81:82E0",
 "instruction_aligned_shift_candidates":{"pal-prototype-1994-11-29":proto_candidates,"europe-retail":europe_candidates},
 "dispatch":{"object_code":"0x14","entry":"81:8050","shared_exit":"81:82E1"},
 "lineage_edits":[{"usa_span":"81:8102..8117","europe_span":"81:8102..8109","effect":"Europe retail contracts the 22-byte frame-normalization block to 8 bytes; PAL prototype and beta retain USA shape."}],
 "regions":rows}
def render(r):
 lines=["# Checkpoint / finish structural island: USA 81:8050..82E0","",
 "Object code 0x14 dispatches to 81:8050. The bounded handler exits through the shared object-handler continuation at 81:82E1.","",
 "| Region | USA bytes | PAL prototype | Europe | Legacy beta |","|---|---:|---|---|---|"]
 for x in r["regions"]:
  def c(b):
   q=x["builds"][b]; return f"{q['start']}..{q['end']} ({q['shift']:+d}; size {q['size']}; sim {q['similarity']:.3f}; op {q['opcode_bytes']}; other {q['unreached_or_data_bytes']})"
  lines.append(f"| {x['name']} | {x['size']} | {c('pal-prototype-1994-11-29')} | {c('europe-retail')} | {c('legacy-beta')} |")
 return "\n".join(lines)+"\n"
def main():
 r=build(); OUTJ.write_text(json.dumps(r,indent=2)+"\n"); OUTM.write_text(render(r)); print(render(r)); print("CHECKPOINT_FINISH_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
