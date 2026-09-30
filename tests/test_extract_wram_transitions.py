#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"tools"/"extract_wram_transitions.py"
def main()->int:
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); trace=td/"t.jsonl"; out=td/"o.json"
        rows=[
          {"f":1,"adr":"0x0042b","old":"0x00","val":"0x00"},
          {"f":7,"adr":"0x0042b","old":"0x00","val":"0x01"},
          {"f":8,"adr":"0x0042b","old":"0x01","val":"0x00"},
          {"f":8,"adr":"0x00400","old":"0x00","val":"0xff"},
        ]
        trace.write_text("".join(json.dumps(r)+"\n" for r in rows))
        subprocess.run([sys.executable,str(TOOL),str(trace),"--from-frame","7","--to-frame","8","--json-out",str(out)],check=True)
        d=json.loads(out.read_text())
        assert [(e["frame"],e["addr"],e["val"]) for e in d["events"]]==[(7,"0x042B",1),(8,"0x042B",0)]
    print("PASS: selected WRAM transition extraction")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
