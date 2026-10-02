#!/usr/bin/env python3
"""Analyze game-authored Uniracers SRAM mutation, checksum, and reload fidelity."""

from __future__ import annotations
import argparse, json
from pathlib import Path

MEDAL_START=0x069C
MEDAL_END=0x072C
TIER_A_START=0x10D3
TIER_A_END=0x10E3
TIER_B_START=0x10FD
TIER_B_END=0x110D
CHECKSUM_START=0x05E8
CHECKSUM_WORDS=170
CHECKSUM_ADDR=0x073C

def checksum(data: bytes) -> int:
    return sum(int.from_bytes(data[CHECKSUM_START+i*2:CHECKSUM_START+i*2+2],"little")
               for i in range(CHECKSUM_WORDS)) & 0xFFFF

def region_changes(a: bytes,b: bytes,start:int,end:int):
    return [{"offset":i,"before":a[i],"after":b[i]} for i in range(start,end) if a[i]!=b[i]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--before",type=Path,required=True)
    ap.add_argument("--after",type=Path,required=True)
    ap.add_argument("--reload",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--require-medal",action="store_true")
    args=ap.parse_args()
    before=args.before.read_bytes(); after=args.after.read_bytes(); reload=args.reload.read_bytes()
    for name,data in [("before",before),("after",after),("reload",reload)]:
        if len(data)!=8192: raise SystemExit(f"{name}: expected 8192 bytes, got {len(data)}")
    medals=region_changes(before,after,MEDAL_START,MEDAL_END)
    tier_a=region_changes(before,after,TIER_A_START,TIER_A_END)
    tier_b=region_changes(before,after,TIER_B_START,TIER_B_END)
    medal_shape=all(c["after"]==min(3,c["before"]+1) for c in medals)
    protected_changes=region_changes(before,after,CHECKSUM_START,CHECKSUM_ADDR)
    all_changes=region_changes(before,after,0,len(before))
    stored_before=int.from_bytes(before[CHECKSUM_ADDR:CHECKSUM_ADDR+2],"little")
    stored_after=int.from_bytes(after[CHECKSUM_ADDR:CHECKSUM_ADDR+2],"little")
    stored_reload=int.from_bytes(reload[CHECKSUM_ADDR:CHECKSUM_ADDR+2],"little")
    report={
      "schema_version":1,
      "changed_byte_count":len(all_changes),
      "protected_region_changes":protected_changes,
      "medal_changes":medals,
      "tier_primary_changes":tier_a,
      "tier_mirror_changes":tier_b,
      "checksum":{
        "before_stored":stored_before,"before_computed":checksum(before),
        "after_stored":stored_after,"after_computed":checksum(after),
        "reload_stored":stored_reload,"reload_computed":checksum(reload),
      },
      "observations":{
        "game_authored_medal_change_observed":bool(medals),
        "medal_changes_are_single_step_saturating":bool(medals) and medal_shape,
        "tier_change_observed":bool(tier_a or tier_b),
      },
      "checks":{
        "game_authored_sram_change_observed":bool(all_changes),
        "checksum_protected_change_observed":bool(protected_changes),
        "after_checksum_valid":stored_after==checksum(after),
        "reload_checksum_valid":stored_reload==checksum(reload),
        "full_sram_survives_reload":after==reload,
        "checksum_survives_reload":stored_after==stored_reload,
      },
      "scope_note":"This acceptance proves real game-authored SRAM mutation/reload fidelity. Medal/tier mutation remains an explicit observation, not a prerequisite; a medal-winning fixture is still required to close progression-changing acceptance."
    }
    report["all_checks_pass"]=all(report["checks"].values())
    payload=json.dumps(report,indent=2)+"\n"
    print(payload,end="")
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(payload,encoding="utf-8")
    if args.require_medal:
        report["checks"]["required_medal_change_observed"]=bool(medals) and medal_shape
        report["all_checks_pass"]=all(report["checks"].values())
        payload=json.dumps(report,indent=2)+"\n"
        print("require-medal: "+("PASS" if report["all_checks_pass"] else "FAIL"))
        if args.out:
            args.out.write_text(payload,encoding="utf-8")
    if not report["all_checks_pass"]: return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
