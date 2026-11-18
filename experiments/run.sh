#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import os,pathlib,re,json
out=pathlib.Path(os.environ["UR_EXPERIMENT_OUTPUT_DIR"]);out.mkdir(parents=True,exist_ok=True)
patterns={"colour":re.compile(r"rgb565|bgrx8888|rgb555|fb\\.bgrx|state\\.fb\\.bmp|color.convert|colour.convert",re.I),"phase":re.compile(r"guest.frame|master.clock|frame_pairs|input.timeline|frame_count|frame_counter|snes9x",re.I)}
results=[]
for p in sorted(pathlib.Path(".").rglob("*")):
 if not p.is_file() or p.suffix.lower() not in {".c",".cc",".cpp",".h",".hpp",".py",".sh"} or p.stat().st_size>500000 or any(s in p.parts for s in (".git","node_modules","vendor","build","dist")):continue
 lines=p.read_text(errors="replace").splitlines()
 for cat,pat in patterns.items():
  for i in [i for i,l in enumerate(lines) if pat.search(l)][:8]:
   results.append({"category":cat,"file":str(p),"line":i+1,"context":"\n".join(f"{j+1}: {lines[j][:220]}" for j in range(max(0,i-2),min(len(lines),i+3)))})
report={"source_sha":os.environ["UR_EXPERIMENT_SOURCE_SHA"],"records":results}
(out/"producer-source.json").write_text(json.dumps(report,indent=2)+"\n")
print("SOURCE",report["source_sha"],"MATCHES",len(results))
for cat in patterns:
 print("CATEGORY",cat)
 for r in [x for x in results if x["category"]==cat][:18]:
  print("FILE",r["file"],"LINE",r["line"]);print(r["context"])
if not any(x["category"]=="colour" for x in results):raise SystemExit("No colour source matches")
PY
