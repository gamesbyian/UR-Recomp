#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import os,pathlib,re,json
out=pathlib.Path(os.environ["UR_EXPERIMENT_OUTPUT_DIR"]);out.mkdir(parents=True,exist_ok=True)
roots=[pathlib.Path(x) for x in ("native","research","tools","src","scripts","experiments") if pathlib.Path(x).exists()]
terms=re.compile(r"RGB565|BGRX8888|RGB555|rgb5|rgb565|bgrx|frame_pairs|master_clock|guest_frame|frame_counter|input_timeline|snes9x",re.I)
records=[]
for root in roots:
 for p in root.rglob("*"):
  if not p.is_file() or p.suffix.lower() not in {".c",".cc",".cpp",".h",".hpp",".py",".sh"} or p.stat().st_size>400000 or any(x in p.parts for x in (".git","build","vendor","node_modules")):continue
  lines=p.read_text(errors="replace").splitlines()
  hits=[i for i,l in enumerate(lines) if terms.search(l)]
  if not hits:continue
  weight=sum(3 for i in hits if re.search(r"RGB565|BGRX8888|rgb565|bgrx",lines[i],re.I))
  records.append((weight,len(hits),str(p),lines,hits))
records.sort(key=lambda x:(-x[0],-x[1],x[2]))
print("SOURCE",os.environ["UR_EXPERIMENT_SOURCE_SHA"],"MATCHING_FILES",len(records))
result=[]
for weight,count,path,lines,hits in records[:45]:
 print("FILE",path,"HITS",count,"COLOUR_WEIGHT",weight)
 for i in hits[:5]:
  context="\n".join(f"{j+1}: {lines[j][:180]}" for j in range(max(0,i-3),min(len(lines),i+4)))
  print(context)
  result.append({"file":path,"line":i+1,"context":context})
(out/"focused-producer-source.json").write_text(json.dumps({"source_sha":os.environ["UR_EXPERIMENT_SOURCE_SHA"],"records":result},indent=2)+"\n")
if not any(weight for weight,*_ in records):raise SystemExit("NO_COLOUR_PRODUCER_SOURCE_FOUND")
PY
