#!/usr/bin/env python3
"""Find the first +8 presentation-ID/VRAM phase divergence in the Dragster gap."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

TAGS = [f"object-tail-{i:03d}" for i in range(90, 151)]
P2_FIELDS = {
    "x": 0x0413,
    "y": 0x0417,
    "xspeed": 0x04B9,
    "yspeed": 0x04BD,
    "pitch": 0x04C9,
    "contact": 0x0E97,
    "laps": 0x0EF3,
    "checkpoint": 0x119B,
    "finish_gate": 0x119F,
}
P1_PRESENTATION = 0x0FE9
P2_PRESENTATION = 0x0FEB

def u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr+1] << 8)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    rows=[]
    for tag in TAGS:
        sides={}
        for margin in (0,8):
            d=args.root/f"margin-{margin}"/"state"
            w=(d/f"{tag}.wram.bin").read_bytes()
            info=json.loads((d/f"{tag}.info.json").read_text())
            sides[str(margin)]={
                "frame":int(info["frame"]),
                "p1_presentation":u16(w,P1_PRESENTATION),
                "p2_presentation":u16(w,P2_PRESENTATION),
                "p2_state":{k:u16(w,a) for k,a in P2_FIELDS.items()},
                "vram_sha256":sha(d/f"{tag}.vram.bin"),
                "oam_sha256":sha(d/f"{tag}.oam.bin"),
                "cgram_sha256":sha(d/f"{tag}.cgram.bin"),
            }
        a,b=sides["0"],sides["8"]
        rows.append({
            "tag":tag,
            "guest_frame_delta":b["frame"]-a["frame"],
            "p1_presentation_equal":a["p1_presentation"]==b["p1_presentation"],
            "p2_presentation_equal":a["p2_presentation"]==b["p2_presentation"],
            "p2_presentation_delta":(b["p2_presentation"]-a["p2_presentation"]) & 0xffff,
            "p2_state_equal":a["p2_state"]==b["p2_state"],
            "vram_equal":a["vram_sha256"]==b["vram_sha256"],
            "oam_equal":a["oam_sha256"]==b["oam_sha256"],
            "cgram_equal":a["cgram_sha256"]==b["cgram_sha256"],
            "control":a,"plus8":b,
        })
    first_pres=next((r for r in rows if not r["p2_presentation_equal"]),None)
    first_vram=next((r for r in rows if not r["vram_equal"]),None)
    first_oam=next((r for r in rows if not r["oam_equal"]),None)
    report={
        "first_p2_presentation_divergence":first_pres,
        "first_vram_divergence":first_vram,
        "first_oam_divergence":first_oam,
        "all_p2_meaningful_state_equal":all(r["p2_state_equal"] for r in rows),
        "rows":rows,
    }
    lines=["# +8 presentation-phase onset","",
      f"- first P2 presentation-ID divergence: **{first_pres['tag'] if first_pres else 'none'}**",
      f"- first VRAM divergence: **{first_vram['tag'] if first_vram else 'none'}**",
      f"- first OAM divergence: **{first_oam['tag'] if first_oam else 'none'}**",
      f"- P2 meaningful state equal throughout: **{report['all_p2_meaningful_state_equal']}**","",
      "| tag | Δframe | P2 present | Δpresent | P2 state | VRAM | OAM |",
      "|---|---:|---|---:|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['tag']} | {r['guest_frame_delta']} | {'match' if r['p2_presentation_equal'] else 'DIFF'} | {r['p2_presentation_delta']:#06x} | {'match' if r['p2_state_equal'] else 'DIFF'} | {'match' if r['vram_equal'] else 'DIFF'} | {'match' if r['oam_equal'] else 'DIFF'} |")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True); args.json_out.write_text(json.dumps(report,indent=2)+"\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True); args.md_out.write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    return 0

if __name__=="__main__": raise SystemExit(main())
