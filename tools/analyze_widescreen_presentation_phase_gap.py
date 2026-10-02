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
PRESENTATION_PHASE_FIELDS = {
    # 82:DF40 increments this modulo four before selecting presentation updates.
    "phase_0300": 0x0300,
    # 82:DF4E/DF51 saves the current P2 ID here on phase wrap; DEEE/DEF1 restores it.
    "saved_p2_12e9": 0x12E9,
    # 82:DF54..DF63 advances this cursor and selects it into $0FEB on phase wrap.
    "alternate_p2_12eb": 0x12EB,
    # Race_UpdateRacersFrame mirrors persistent $0FEB through this shared working slot.
    "working_presentation_0f97": 0x0F97,
    # Known P2 orientation input omitted from the earlier compact meaningful-state set.
    "faced_direction_0ba3": 0x0BA3,
    # Inputs on the ordinary per-racer selector path ending at 83:EF0C -> $0F97.
    "selector_0f21": 0x0F21,
    "selector_0f33": 0x0F33,
    "selector_0f43": 0x0F43,
    "working_facing_0f47": 0x0F47,
    "selector_override_0f4f": 0x0F4F,
    "presentation_base_0f77": 0x0F77,
    "orientation_index_0f83": 0x0F83,
    "selector_motion_0f89": 0x0F89,
    "selector_delta_0f8f": 0x0F8F,
    "animation_phase_0fd9": 0x0FD9,
    # Inputs to the two concrete $0F4F override producers at 82:961D and 82:A45A.
    "override_progress_123f": 0x123F,
    "override_takeoff_facing_120f": 0x120F,
    "override_angle_0f49": 0x0F49,
    "override_airtime_0f29": 0x0F29,
    "override_anim_step_0f57": 0x0F57,
    "override_anim_limit_0f81": 0x0F81,
    "override_anim_table_0f85": 0x0F85,
    # Persistent/shared inputs surrounding the P2 tabletop/override path.
    "p2_persistent_progress_1247": 0x1247,
    "p2_persistent_takeoff_facing_1213": 0x1213,
    "p2_persistent_angle_1237": 0x1237,
    "p2_persistent_latch_120d": 0x120D,
    "p2_misc_040f": 0x040F,
    "working_misc_0f7b": 0x0F7B,
    "global_swap_0c7b": 0x0C7B,
    "p2_persistent_override_0deb": 0x0DEB,
}
P1_PRESENTATION = 0x0FE9
P2_PRESENTATION = 0x0FEB

def u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr+1] << 8)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def first_difference(rows: list[dict], key: str) -> dict | None:
    return next((r for r in rows if not r[key]), None)

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
                "presentation_phase":{k:u16(w,a) for k,a in PRESENTATION_PHASE_FIELDS.items()},
                "_wram":w,
                "vram_sha256":sha(d/f"{tag}.vram.bin"),
                "oam_sha256":sha(d/f"{tag}.oam.bin"),
                "cgram_sha256":sha(d/f"{tag}.cgram.bin"),
            }
        a,b=sides["0"],sides["8"]
        wram_diffs=[i for i,(av,bv) in enumerate(zip(a["_wram"],b["_wram"])) if av != bv]
        del a["_wram"], b["_wram"]
        phase_equal={
            k:a["presentation_phase"][k]==b["presentation_phase"][k]
            for k in PRESENTATION_PHASE_FIELDS
        }
        rows.append({
            "tag":tag,
            "guest_frame_delta":b["frame"]-a["frame"],
            "p1_presentation_equal":a["p1_presentation"]==b["p1_presentation"],
            "p2_presentation_equal":a["p2_presentation"]==b["p2_presentation"],
            "p2_presentation_delta":(b["p2_presentation"]-a["p2_presentation"]) & 0xffff,
            "p2_state_equal":a["p2_state"]==b["p2_state"],
            "wram_diff_count":len(wram_diffs),
            "wram_diff_addresses":[f"7E:{addr:04X}" for addr in wram_diffs[:64]],
            "presentation_phase_equal":phase_equal,
            "all_presentation_phase_equal":all(phase_equal.values()),
            "vram_equal":a["vram_sha256"]==b["vram_sha256"],
            "oam_equal":a["oam_sha256"]==b["oam_sha256"],
            "cgram_equal":a["cgram_sha256"]==b["cgram_sha256"],
            "control":a,"plus8":b,
        })
    first_pres=first_difference(rows,"p2_presentation_equal")
    first_vram=first_difference(rows,"vram_equal")
    first_oam=first_difference(rows,"oam_equal")
    first_phase={
        k:next((r for r in rows if not r["presentation_phase_equal"][k]),None)
        for k in PRESENTATION_PHASE_FIELDS
    }
    report={
        "first_p2_presentation_divergence":first_pres,
        "first_vram_divergence":first_vram,
        "first_oam_divergence":first_oam,
        "first_presentation_phase_divergence":{
            k:(None if r is None else r["tag"]) for k,r in first_phase.items()
        },
        "all_p2_meaningful_state_equal":all(r["p2_state_equal"] for r in rows),
        "first_any_wram_divergence":next((r["tag"] for r in rows if r["wram_diff_count"]),None),
        "rows":rows,
    }
    lines=["# +8 presentation-phase onset","",
      f"- first P2 presentation-ID divergence: **{first_pres['tag'] if first_pres else 'none'}**",
      f"- first VRAM divergence: **{first_vram['tag'] if first_vram else 'none'}**",
      f"- first OAM divergence: **{first_oam['tag'] if first_oam else 'none'}**",
      f"- P2 meaningful state equal throughout: **{report['all_p2_meaningful_state_equal']}**",
      f"- first full-WRAM divergence in this window: **{report['first_any_wram_divergence'] or 'none'}**","",
      "First event-relative divergence in candidate presentation-stage state:"]
    for k in PRESENTATION_PHASE_FIELDS:
        lines.append(f"- `{k}`: **{report['first_presentation_phase_divergence'][k] or 'none'}**")
    lines += ["",
      "| tag | Δframe | P2 present | Δpresent | P2 state | phase | saved | alternate | working | facing | VRAM | OAM |",
      "|---|---:|---|---:|---|---|---|---|---|---|---|---|"]
    for r in rows:
        eq=r["presentation_phase_equal"]
        lines.append(
            f"| {r['tag']} | {r['guest_frame_delta']} | "
            f"{'match' if r['p2_presentation_equal'] else 'DIFF'} | {r['p2_presentation_delta']:#06x} | "
            f"{'match' if r['p2_state_equal'] else 'DIFF'} | "
            f"{'match' if eq['phase_0300'] else 'DIFF'} | "
            f"{'match' if eq['saved_p2_12e9'] else 'DIFF'} | "
            f"{'match' if eq['alternate_p2_12eb'] else 'DIFF'} | "
            f"{'match' if eq['working_presentation_0f97'] else 'DIFF'} | "
            f"{'match' if eq['faced_direction_0ba3'] else 'DIFF'} | "
            f"{'match' if r['vram_equal'] else 'DIFF'} | {'match' if r['oam_equal'] else 'DIFF'} |"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True); args.json_out.write_text(json.dumps(report,indent=2)+"\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True); args.md_out.write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    return 0

if __name__=="__main__": raise SystemExit(main())
