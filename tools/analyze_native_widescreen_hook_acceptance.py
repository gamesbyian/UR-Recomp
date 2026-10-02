#!/usr/bin/env python3
"""Validate the native +8 strip hook against the accepted PR #219 contract."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

PREP_RE = re.compile(r"URWS_PREP margin=8 edge=([0-9A-Fa-f]{4}) count=(\d+)")
CLEAN_RE = re.compile(r"URWS_CLEANUP margin=8")
LIFECYCLE_LINE_RE = re.compile(r"URWS_(PREP|CLEANUP) margin=8")
LIMIT_RE = re.compile(
    r"URWS_LIMIT margin=(16|24) required_extra_columns=(\d+) "
    r"stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity"
)
PROTECTED_WORDS = {
    "player_x":0x0411,"player_y":0x0415,"camera_x":0x0419,"camera_y":0x041D,
    "camera_dx":0x04F5,"camera_dy":0x04F9,"x_speed":0x04B7,"y_speed":0x04BB,
    "pitch":0x04C7,"contact":0x0E95,"laps":0x0EF1,"checkpoint":0x1199,"finish":0x119D,
}

def read_words(path: Path) -> dict[str,int]:
    raw=path.read_bytes()
    if len(raw)<0x1200:
        raise ValueError(f"{path}: WRAM dump too small ({len(raw)} bytes)")
    return {name: raw[a] | (raw[a+1]<<8) for name,a in PROTECTED_WORDS.items()}

def cleanup_lifecycle(log: str) -> tuple[bool,bool]:
    live=False
    seen=False
    for kind in LIFECYCLE_LINE_RE.findall(log):
        if kind=="PREP":
            if live:
                return False, live
            live=True
            seen=True
        else:
            if not live:
                return False, live
            live=False
    return seen, live

def analyze(logs: dict[int,str], dumps: dict[int,Path]) -> dict:
    prep={m:PREP_RE.findall(logs[m]) for m in logs}
    cleanup={m:CLEAN_RE.findall(logs[m]) for m in logs}
    limits={m:[(int(a),int(b)) for a,b in LIMIT_RE.findall(logs[m])] for m in logs}
    states={m:read_words(dumps[m]) for m in dumps}
    control=states[0]
    diffs={}
    for m,state in states.items():
        if m==0: continue
        diffs[m]={k:{"control":control[k],f"margin_{m}":state[k]} for k in control if state[k]!=control[k]}
    plus8_edges=[int(edge,16) for edge,count in prep.get(8,[]) if int(count)==16]
    lifecycle_ok, final_payload_live = cleanup_lifecycle(logs.get(8,""))
    checks={
        "margin0_control_inert": not prep.get(0) and not cleanup.get(0) and not limits.get(0),
        "margin8_exercised": len(plus8_edges)>0,
        "margin8_all_counts_16": len(plus8_edges)==len(prep.get(8,[])),
        "margin8_cleanup_lifecycle_valid": lifecycle_ok and len(prep.get(8,[]))-len(cleanup.get(8,[])) in (0,1),
        "margin8_protected_state_equal": not diffs.get(8),
        "margin16_stops_at_capacity": not prep.get(16) and any(m==16 and c==2 for m,c in limits.get(16,[])) and not diffs.get(16),
        "margin24_stops_at_capacity": not prep.get(24) and any(m==24 and c==3 for m,c in limits.get(24,[])) and not diffs.get(24),
    }
    return {
        "schema_version":1,
        "reference_acceptance":{
            "pr":219,"workflow_run":37066327707,"accepted_adjacent_columns":309,
            "longest_consecutive_run":14,
            "mechanism":"stock-A59E-double-pass-secondary-horizontal-lane",
        },
        "native_runtime":{
            "margin8_prepare_events":len(prep.get(8,[])),
            "margin8_cleanup_events":len(cleanup.get(8,[])),
            "margin8_unique_edges":len(set(plus8_edges)),
            "margin8_final_payload_live_at_exit":final_payload_live,
            "margin16_limit_events":limits.get(16,[]),
            "margin24_limit_events":limits.get(24,[]),
        },
        "protected_state_differences":diffs,
        "checks":checks,
        "accepted":all(checks.values()),
        "first_generalization_constraint":"secondary-lane-capacity",
        "stock_extra_horizontal_lanes":1,
        "pixels_per_extra_column":8,
        "margin16_required_extra_columns":2,
        "margin24_required_extra_columns":3,
    }

def render(r: dict) -> str:
    c,n=r["checks"],r["native_runtime"]
    return "\n".join([
        "# Native +8 Widescreen strip-hook acceptance","",
        "Reference contract: PR #219 / workflow run 37066327707 "
        "(309 exact accepted future columns; longest consecutive run 14).","",
        f"- stock margin 0 inert: **{c['margin0_control_inert']}**",
        f"- +8 native preparation events: **{n['margin8_prepare_events']}**",
        f"- +8 cleanup events: **{n['margin8_cleanup_events']}**",
        f"- +8 unique prepared edges: **{n['margin8_unique_edges']}**",
        f"- +8 protected gameplay/camera/progression state equal: **{c['margin8_protected_state_equal']}**",
        f"- +16 stopped at stock lane capacity: **{c['margin16_stops_at_capacity']}**",
        f"- +24 stopped at stock lane capacity: **{c['margin24_stops_at_capacity']}**","",
        "First generalization constraint: **secondary-lane-capacity**. "
        "The stock horizontal pair has one primary lane plus one secondary lane. "
        "+8 consumes the only spare lane; +16 needs two extra columns and +24 needs three.","",
        f"Overall accepted: **{r['accepted']}**",""
    ])

def main()->int:
    ap=argparse.ArgumentParser()
    for m in (0,8,16,24):
        ap.add_argument(f"--log-{m}",type=Path,required=True)
        ap.add_argument(f"--dump-{m}",type=Path,required=True)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    logs={m:getattr(args,f"log_{m}").read_text(encoding="utf-8",errors="replace") for m in (0,8,16,24)}
    dumps={m:getattr(args,f"dump_{m}") for m in (0,8,16,24)}
    report=analyze(logs,dumps)
    md=render(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["accepted"] else 2

if __name__=="__main__":
    raise SystemExit(main())
