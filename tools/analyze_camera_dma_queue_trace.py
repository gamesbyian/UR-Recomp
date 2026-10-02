#!/usr/bin/env python3
"""Summarize camera-demand -> prepared DMA descriptors -> NMI consumption."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

RX=re.compile(
 r"CAMDMA frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) pc=(?P<pc>[0-9A-Fa-f]{6}) "
 r"camx=(?P<camx>\d+) camy=(?P<camy>\d+) camdx=(?P<camdx>-?\d+) camdy=(?P<camdy>-?\d+) "
 r"edgex=(?P<edgex>\d+) edgey=(?P<edgey>\d+) edgex2=(?P<edgex2>\d+) edgey2=(?P<edgey2>\d+) "
 r"cnt=(?P<c0>\d+),(?P<c1>\d+),(?P<c2>\d+),(?P<c3>\d+) mirror=(?P<mirror>\d+) desc=(?P<desc>.*)$"
)
SITES={0x81A59A:"before_build",0x81A59D:"after_build",0x82D19B:"before_consume",0x82D2D1:"after_consume"}

def descs(s):
 out=[]
 for i,item in enumerate(s.split(",")):
  p=item.split(":")
  if len(p)!=5: continue
  ready,dest,src,size,vmain=[int(x,16) if j else int(x) for j,x in enumerate(p)]
  out.append({"slot":i,"ready":ready,"vram":dest,"source":src,"size":size,"vmain":vmain})
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("log",type=Path)
 ap.add_argument("--json-out",type=Path); ap.add_argument("--md-out",type=Path)
 args=ap.parse_args()
 rows=[]
 for line in args.log.read_text(encoding="utf-8",errors="replace").splitlines():
  m=RX.search(line)
  if not m: continue
  g=m.groupdict(); pc=int(g["pc"],16); ds=descs(g["desc"])
  rows.append({
   "frame":int(g["frame"]),"v":int(g["v"]),"cycles":int(g["cycles"]),"pc":pc,
   "site":SITES.get(pc,"unknown"),"camera_x":int(g["camx"]),"camera_y":int(g["camy"]),
   "camera_dx":int(g["camdx"]),"camera_dy":int(g["camdy"]),
   "edge_x":int(g["edgex"]),"edge_y":int(g["edgey"]),
   "edge_x_secondary":int(g["edgex2"]),"edge_y_secondary":int(g["edgey2"]),
   "counts":[int(g[f"c{i}"]) for i in range(4)],"mirror":int(g["mirror"]),
   "descriptors":ds,"ready_slots":[d for d in ds if d["ready"]],
  })
 if not rows: raise SystemExit("no CAMDMA observations")
 built=[r for r in rows if r["site"]=="after_build" and r["ready_slots"]]
 consumes=[r for r in rows if r["site"]=="before_consume" and r["ready_slots"]]
 pairs=[]
 for b in built:
  c=next((x for x in consumes if (x["frame"],x["v"],x["cycles"])>(b["frame"],b["v"],b["cycles"])),None)
  if not c: continue
  pairs.append({
   "build_frame":b["frame"],"build_v":b["v"],"build_cycles":b["cycles"],
   "consume_frame":c["frame"],"consume_v":c["v"],"consume_cycles":c["cycles"],
   "frame_delta":c["frame"]-b["frame"],"camera_x":b["camera_x"],"camera_dx":b["camera_dx"],
   "edge_x":b["edge_x"],"edge_y":b["edge_y"],"counts":b["counts"],
   "descriptors":b["ready_slots"],
  })
 report={"schema_version":1,"rows":rows,"build_events":len(built),"consume_events":len(consumes),"pairs":pairs}
 lines=["# Camera-driven DMA preparation causal trace","",
  f"- non-empty build events: **{len(built)}**",
  f"- non-empty NMI consume events: **{len(consumes)}**",
  f"- paired events: **{len(pairs)}**","",
  "| build | consume | Δframe | camera X | dx | edge X | counts | slots | descriptors |",
  "|---:|---:|---:|---:|---:|---:|---|---:|---|"]
 for p in pairs[:120]:
  ds="; ".join(f"{d['slot']}:{d['source']:04X}->{d['vram']:04X}/{d['size']:04X}/V{d['vmain']:04X}" for d in p["descriptors"])
  lines.append(f"| {p['build_frame']} | {p['consume_frame']} | {p['frame_delta']} | {p['camera_x']} | {p['camera_dx']} | {p['edge_x']} | {','.join(map(str,p['counts']))} | {len(p['descriptors'])} | {ds} |")
 payload=json.dumps(report,indent=2)+"\n"; md="\n".join(lines)+"\n"
 if args.json_out:
  args.json_out.parent.mkdir(parents=True,exist_ok=True); args.json_out.write_text(payload,encoding="utf-8")
 if args.md_out:
  args.md_out.parent.mkdir(parents=True,exist_ok=True); args.md_out.write_text(md,encoding="utf-8")
 print(md,end="")
 return 0 if pairs else 2
if __name__=="__main__": raise SystemExit(main())
