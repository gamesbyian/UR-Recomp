#!/usr/bin/env python3
"""Summarize title->frontend snesref checkpoints."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def summarize(root: Path) -> dict:
    rows=[]
    for info in sorted(root.glob("*.info.json")):
        tag=info.name.removesuffix(".info.json")
        meta=json.loads(info.read_text())
        w=(root/f"{tag}.wram.bin").read_bytes()
        fb=root/f"{tag}.fb.bgrx"
        rows.append({
            "tag":tag,
            "frame":meta["frame"],
            "fb_frame":meta["fb_frame"],
            "menu":w[0x009F],
            "menu_hex":f"0x{w[0x009F]:02X}",
            "selected":w[0x009B],
            "in_race":w[0x0313],
            "frame_sha256":hashlib.sha256(fb.read_bytes()).hexdigest() if fb.is_file() else None,
        })
    return {"schema_version":1,"checkpoints":rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dump_dir",type=Path)
    ap.add_argument("--json-out",type=Path)
    a=ap.parse_args()
    r=summarize(a.dump_dir)
    for x in r["checkpoints"]:
        print(f"{x['tag']}: frame={x['frame']} menu={x['menu_hex']} fb={x['frame_sha256']}")
    if a.json_out:
        a.json_out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    return 0
if __name__=="__main__": raise SystemExit(main())
