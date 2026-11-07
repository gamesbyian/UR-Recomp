#!/usr/bin/env python3
"""Append-only UTC daily engineering estimate snapshots and comparable deltas.

Provisional source-linked engineering planning, NOT a formal acceptance authority.
Run on a checked-out current main; no network, GitHub calls or CI dispatch.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.daily_measurement import (EVENTS, MILESTONES, INVENTORY, PRIOR, ADJUSTMENTS,
    RELEASE, calculate_daily, load, read_entries, validate_provenance)
from tools.atomic_progress_v2 import validate as validate_formal

SNAPSHOTS = ROOT / "docs/progress/daily/snapshots"

def canonical_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True,
            separators=(",", ":"),ensure_ascii=False).encode("utf-8")).hexdigest()

def make_snapshot(inv, ledger, prior, adjustments, milestone_spec, entries, head, date,
                  estimator_hash):
    if not isinstance(date,str) or len(date)!=10:
        raise ValueError("Snapshot needs ISO UTC day YYYY-MM-DD")
    try:
        if datetime.strptime(date,"%Y-%m-%d").date().isoformat()!=date:
            raise ValueError("Invalid snapshot UTC calendar day")
    except ValueError as exc:
        raise ValueError("Invalid snapshot UTC calendar day") from exc
    report=calculate_daily(inv,ledger,prior,adjustments,milestone_spec,
                           entries,head,inv["source_sha"])
    accepted=validate_formal(inv,ledger)
    return {
        "schema":"ur-daily-estimate-snapshot/1",
        "day_utc":date,
        "source_main_sha":head,
        "reviewed_inventory_sha":inv["source_sha"],
        "contract":inv["frozen_contract_fnv1a32"],
        "milestone_allocation_sha256":report["milestone_allocation_sha256"],
        "effort_prior_sha256":canonical_hash({
            "prior":prior,
            "active_changes":adjustments.get("changes", []),
            "completed_shared":adjustments.get("completed_shared", []),
        }),
        "calculator_source_sha256":estimator_hash,
        "engineering_estimate_percent":report["engineering_estimate_percent"],
        "engineering_recorded_evidence_range_percent":report[
            "engineering_recorded_evidence_range_percent"],
        "remaining_relative_work_units":report["relative_work_units"],
        "formal_bounded_percent":report["formal_bounded_percent"],
        "independently_reviewed_percent":report["independently_reviewed_percent"],
        "usa_events_accepted":report["usa_events_accepted"],
        "release_gates_passed":report["release_gates_passed"],
        "evidence_event_ids":sorted(e["event_id"] for e in entries),
        "effort_revision_effects":report["effort_revision_effects"],
        "caveat":report["estimate_caveat"] +
             "; source-linked milestone and effort evidence may still be incomplete",
    }

def compare(previous, current):
    fields=("schema","contract","milestone_allocation_sha256",
            "effort_prior_sha256","calculator_source_sha256")
    mismatched=[field for field in fields if previous.get(field)!=current.get(field)]
    if previous.get("schema")!="ur-daily-estimate-snapshot/1" or current.get("schema")!="ur-daily-estimate-snapshot/1":
        raise ValueError("Unknown snapshot schema")
    if previous["day_utc"]>=current["day_utc"]:
        raise ValueError("Comparison requires earlier UTC day")
    old=set(previous["evidence_event_ids"])
    now=set(current["evidence_event_ids"])
    if old-now:
        raise ValueError("Append-only event history was removed; reconcile before trend reporting")
    out={
        "previous_day":previous["day_utc"],"current_day":current["day_utc"],
        "comparable":not mismatched,"incompatible_fields":mismatched,
        "new_event_ids":sorted(now-old),
        "previous_source_sha":previous["source_main_sha"],
        "current_source_sha":current["source_main_sha"],
        "change_interpretation":"Source-linked planning estimate; NOT release velocity or statistical calibration",
    }
    if mismatched:
        out["engineering_change_pp"]=None
        out["remaining_work_change_units"]=None
        out["formal_acceptance_change_pp"]=None
        out["reason"]="Different measurement methodology; backcast both sources under one method before comparing"
    else:
        out["engineering_change_pp"]=round(current["engineering_estimate_percent"]-previous["engineering_estimate_percent"],2)
        out["remaining_work_change_units"]=round(current["remaining_relative_work_units"]-previous["remaining_relative_work_units"],1)
        out["formal_acceptance_change_pp"]=round(current["formal_bounded_percent"]-previous["formal_bounded_percent"],2)
    return out

def save_once(target, data):
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with target.open("x",encoding="utf-8") as out:
            out.write(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    except FileExistsError as exc:
        raise ValueError("Refusing to overwrite an existing dated snapshot: "+str(target)) from exc

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--day",default=None,help="UTC day YYYY-MM-DD; default today UTC")
    p.add_argument("--out",type=Path,help="Snapshot file; default docs/progress/daily/snapshots/YYYY-MM-DD.json")
    p.add_argument("--compare",type=Path,help="Earlier compatible daily snapshot to compare")
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    day=args.day or datetime.now(timezone.utc).date().isoformat()
    head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    entries=read_entries(EVENTS)
    validate_provenance(entries,head)
    source_hash=hashlib.sha256(
        (ROOT/"tools/daily_measurement.py").read_bytes()).hexdigest()
    snap=make_snapshot(load(INVENTORY),load(RELEASE),load(PRIOR),load(ADJUSTMENTS),
                       load(MILESTONES),entries,head,day,source_hash)
    result={"snapshot":snap}
    if args.compare:
        previous=load(args.compare)
        ancestry=subprocess.run(["git","-C",str(ROOT),"merge-base","--is-ancestor",
                                 previous["source_main_sha"],head],capture_output=True,
                                 check=False)
        if ancestry.returncode:
            p.error("Prior daily snapshot source SHA is not an ancestor of current head")
        result["trend"]=compare(previous,snap)
    if not args.dry_run:
        target=args.out or SNAPSHOTS/(day+".json")
        save_once(target,snap)
        result["saved_to"]=str(target)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
