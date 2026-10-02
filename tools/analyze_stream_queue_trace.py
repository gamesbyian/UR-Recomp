#!/usr/bin/env python3
"""Summarize event-relative active race streaming queue production and consumption."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

LINE=re.compile(
 r"STREAMTRACE frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) pc=(?P<pc>[0-9A-Fa-f]{6}) "
 r"ready=(?P<ready>\d+) camx=(?P<camx>\d+) camy=(?P<camy>\d+) edgex=(?P<edgex>\d+) edgey=(?P<edgey>\d+) "
 r"camdx=(?P<camdx>\d+) r0=(?P<r0>[0-9A-Fa-f]{4}) r1=(?P<r1>[0-9A-Fa-f]{4}) "
 r"c0=(?P<c0>[0-9A-Fa-f]{4}) c1=(?P<c1>[0-9A-Fa-f]{4}) f0=(?P<f0>\d+) f1=(?P<f1>\d+) q=(?P<q>.*)$"
)

SITES={0xF0BB:"producer_entry",0xF292:"producer_commit",0xB8AB:"consumer_entry"}

def parse_queue(s:str):
 out=[]
 for item in s.split(","):
  if not item: continue
  if item=="END":
   out.append({"end":True}); break
  p=item.split(":")
  if len(p)!=3: continue
  out.append({"bank":int(p[0],16),"source":int(p[1],16),"vram":int(p[2],16)})
 return out

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("log",type=Path)
 ap.add_argument("--json-out",type=Path)
 ap.add_argument("--md-out",type=Path)
 args=ap.parse_args()
 rows=[]
 for line in args.log.read_text(encoding="utf-8",errors="replace").splitlines():
  m=LINE.search(line)
  if not m: continue
  g=m.groupdict(); pc=int(g["pc"],16); pcw=pc&0xffff
  q=parse_queue(g["q"])
  rows.append({
   "frame":int(g["frame"]),"v":int(g["v"]),"cycles":int(g["cycles"]),
   "pc":pc,"site":SITES.get(pcw,"unknown"),"ready":int(g["ready"]),
   "camera_x":int(g["camx"]),"camera_y":int(g["camy"]),
   "camera_edge_x":int(g["edgex"]),"camera_edge_y":int(g["edgey"]),
   "camera_dx_raw":int(g["camdx"]),
   "renderer_primary":int(g["r0"],16),"renderer_secondary":int(g["r1"],16),
   "course_window_primary":int(g["c0"],16),"course_window_secondary":int(g["c1"],16),
   "window_flag_primary":int(g["f0"]),"window_flag_secondary":int(g["f1"]),
   "queue":q,
   "queue_entries":sum(1 for x in q if "bank" in x),
  })
 if not rows: raise SystemExit("no STREAMTRACE observations")
 commits=[x for x in rows if x["site"]=="producer_commit"]
 consumers=[x for x in rows if x["site"]=="consumer_entry"]
 pairs=[]
 for c in commits:
  nxt=next((x for x in consumers if (x["frame"],x["v"],x["cycles"])>(c["frame"],c["v"],c["cycles"])),None)
  if nxt:
   pairs.append({
    "producer_frame":c["frame"],"producer_v":c["v"],"producer_cycles":c["cycles"],
    "consumer_frame":nxt["frame"],"consumer_v":nxt["v"],"consumer_cycles":nxt["cycles"],
    "frame_delta":nxt["frame"]-c["frame"],
    "queue_entries_at_producer":c["queue_entries"],
    "queue_entries_at_consumer":nxt["queue_entries"],
    "camera_x":c["camera_x"],"camera_edge_x":c["camera_edge_x"],
    "renderer_primary":c["renderer_primary"],"course_window_primary":c["course_window_primary"],
    "first_vram":next((x["vram"] for x in c["queue"] if "vram" in x),None),
    "last_vram":next((x["vram"] for x in reversed(c["queue"]) if "vram" in x),None),
   })
 report={"schema_version":1,"observations":len(rows),"producer_commits":len(commits),
         "consumer_entries":len(consumers),"pairs":pairs,"rows":rows}
 lines=["# Active race streaming queue runtime trace","",
  f"- producer commits: **{len(commits)}**",
  f"- consumer entries: **{len(consumers)}**",
  f"- paired producer→consumer events: **{len(pairs)}**","",
  "| prod frame | consumer frame | Δframe | entries | camera X | edge X | renderer coord | window coord | VRAM span |",
  "|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
 for p in pairs[:80]:
  span="--" if p["first_vram"] is None else f"{p['first_vram']:04X}..{p['last_vram']:04X}"
  lines.append(f"| {p['producer_frame']} | {p['consumer_frame']} | {p['frame_delta']} | {p['queue_entries_at_producer']} | {p['camera_x']} | {p['camera_edge_x']} | {p['renderer_primary']:04X} | {p['course_window_primary']:04X} | {span} |")
 payload=json.dumps(report,indent=2)+"\n"; md="\n".join(lines)+"\n"
 if args.json_out:
  args.json_out.parent.mkdir(parents=True,exist_ok=True); args.json_out.write_text(payload,encoding="utf-8")
 if args.md_out:
  args.md_out.parent.mkdir(parents=True,exist_ok=True); args.md_out.write_text(md,encoding="utf-8")
 print(md,end="")
 return 0 if pairs else 2

if __name__=="__main__":
 raise SystemExit(main())
