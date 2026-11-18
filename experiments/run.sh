#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json,os,pathlib,re
out=pathlib.Path(os.environ["UR_EXPERIMENT_OUTPUT_DIR"]);out.mkdir(parents=True,exist_ok=True)
# Third and final source-scan tactic: production C/C++ only, never test fixtures.
roots=[pathlib.Path(p) for p in ("native","src","research") if pathlib.Path(p).exists()]
patterns={"pixel_pack":re.compile(r"(rgb565|rgb555|bgrx|rgb888|0xf800|0x07e0|0x001f|<<\s*11|>>\s*11)",re.I),
"clock_input":re.compile(r"(master_clock|guest_frame|frame_counter|input_timeline|joypad|controller|frame_tick|vblank|nmi)",re.I)}
results={}
for label,pattern in patterns.items():
 matches=[]
 for root in roots:
  for path in root.rglob("*"):
   if path.suffix.lower() not in (".c",".cc",".cpp",".h",".hpp") or not path.is_file() or path.stat().st_size>500000:continue
   if any(part in ("test","tests","fixtures","build","vendor","third_party") for part in path.parts):continue
   lines=path.read_text(errors="replace").splitlines()
   for i,line in enumerate(lines):
    if pattern.search(line):
     context="\n".join(f"{j+1}: {lines[j][:220]}" for j in range(max(0,i-2),min(len(lines),i+3)))
     matches.append({"path":str(path),"line":i+1,"context":context})
 results[label]=matches
 print("PRODUCTION",label,"MATCHES",len(matches),"FILES",len(set(x["path"] for x in matches)))
 for item in matches[:65]:
  print("SOURCE",item["path"],"LINE",item["line"])
  print(item["context"])
(out/"production-only-producer-clock.json").write_text(json.dumps({"source_sha":os.environ["UR_EXPERIMENT_SOURCE_SHA"],"matches":results},indent=2)+"\n")
if not results["pixel_pack"] or not results["clock_input"]:raise SystemExit("PRODUCTION_PRODUCER_OR_CLOCK_NOT_LOCATED")
PY
