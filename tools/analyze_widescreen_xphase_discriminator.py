#!/usr/bin/env python3
"""Compare bounded A59E X-phase perturbations against stock preparation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import analyze_widescreen_strip_schedule as base

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("variants",nargs="+",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()

    control=base.parse(args.control)
    results={}
    for path in args.variants:
        name=path.parent.name
        rows=base.parse(path)
        report,matches=base.analyze_rows(control,rows)
        results[name]={
            "successful_future_stock_matches":report["successful_future_stock_matches"],
            "additional_strip_prepared":report["additional_strip_prepared"],
            "expected_descriptor_consumed_by_nmi":report["expected_descriptor_consumed_by_nmi"],
            "widened_edge_matches_future_stock_data":report["widened_edge_matches_future_stock_data"],
            "authoritative_gameplay_state_equal":report["authoritative_gameplay_state_equal"],
            "camera_state_restored":report["camera_state_restored"],
            "gameplay_difference_count":len(report["gameplay_differences"]),
            "camera_difference_count":len(report["camera_restore_differences"]),
            "examples":[{
                "plus8_frame":m["plus8"]["frame"],
                "control_frame":m["control_future"]["frame"],
                "camera_x_advance":m["camera_x_advance"],
                "vram":m["plus8"]["descriptor"]["vram"],
                "source":m["plus8"]["descriptor"]["source"],
            } for m in matches[:12]],
        }

    viable=[
        k for k,v in results.items()
        if v["successful_future_stock_matches"]>0
        and v["authoritative_gameplay_state_equal"]
        and v["camera_state_restored"]
    ]
    report={
        "schema_version":1,
        "classification":"phase-lever-found" if viable else "tested-x-phase-deltas-negative",
        "viable_variants":viable,
        "results":results,
    }

    lines=["# A59E X-phase discriminator","",
           f"- classification: **{report['classification']}**",
           f"- viable variants: **{', '.join(viable) or 'none'}**","",
           "| variant | future-stock matches | gameplay equal | camera equal |",
           "|---|---:|---|---|"]
    for name,v in results.items():
        lines.append(
            f"| {name} | {v['successful_future_stock_matches']} | "
            f"{v['authoritative_gameplay_state_equal']} | {v['camera_state_restored']} |"
        )
    md="\n".join(lines)+"\n"
    payload=json.dumps(report,indent=2)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    # This is a discriminator, not an acceptance gate. Only state corruption fails it.
    bad=[k for k,v in results.items()
         if not v["authoritative_gameplay_state_equal"] or not v["camera_state_restored"]]
    return 2 if bad else 0

if __name__=="__main__":
    raise SystemExit(main())
