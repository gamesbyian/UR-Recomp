#!/usr/bin/env python3
"""Compare frozen v2 baseline receipts to present binary criterion status."""
import argparse
import json
from pathlib import Path
from tools.atomic_progress_v2 import validate, ROOT, INV_PATH, LEDGER_PATH

BASE = ROOT/"docs/progress/windows-beta-v2-baseline.json"
def delta(inventory, baseline, ledger):
    now = validate(inventory, ledger)
    if baseline.get("version") != inventory.get("version") or baseline.get("criterion_contract_hash") != inventory.get("frozen_contract_fnv1a32"):
        raise ValueError("Cannot compare incompatible/forked scope or criterion contract")
    previous = baseline.get("verified_ids",[])
    if len(set(previous)) != len(previous):
        raise ValueError("Duplicate historical receipts")
    known = {x["id"] for x in inventory["criteria"]}
    if set(previous) - known:
        raise ValueError("Previously claimed IDs are absent from current inventory")
    current = {x["id"] for x in inventory["criteria"] if x["status"]=="bounded_verified"}
    newly = sorted(current-set(previous))
    lost = sorted(set(previous)-current)
    expected_start = 100*sum((10 if x.startswith("FID-") else 45) for x in previous)/4500
    if round(expected_start, 3) != round(baseline.get("provisional_coverage_percent",-1),3):
        raise ValueError("Historical baseline score was rewritten")
    added_units = sum(10 if x.startswith("FID-") else 45 for x in newly)
    lost_units = sum(10 if x.startswith("FID-") else 45 for x in lost)
    return {"v2_source_sha":inventory["source_sha"],
            "baseline_source_sha":baseline["reviewed_source_sha"],
            "current_provisional_coverage_percent":now["bounded_product_coverage_percent"],
            "baseline_provisional_coverage_percent":baseline["provisional_coverage_percent"],
            "change_percentage_points":round(100*(added_units-lost_units)/4500,3),
            "newly_verified_ids":newly, "regressed_or_retracted_ids":lost,
            "independently_audited_percent":now["independently_audited_coverage_percent"],
            "full_USA_events":now["independent_USA_complete_events"],
            "passed_release_gates":now["formal_windows_gates_passed"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",type=Path,default=INV_PATH)
    p.add_argument("--baseline",type=Path,default=BASE)
    p.add_argument("--ledger",type=Path,default=LEDGER_PATH)
    p.add_argument("--format",choices=["json","markdown"],default="markdown")
    a=p.parse_args()
    z=delta(json.loads(a.inventory.read_text()),json.loads(a.baseline.read_text()),json.loads(a.ledger.read_text()))
    if a.format=="json":
        print(json.dumps(z,indent=2))
    else:
        print(f"v2 product coverage: {z['baseline_provisional_coverage_percent']:.3f}% -> {z['current_provisional_coverage_percent']:.3f}% ({z['change_percentage_points']:+.3f} pp)")
        print(f"Promoted requirements: {', '.join(z['newly_verified_ids']) or 'none'}")
        print(f"Retracted requirements: {', '.join(z['regressed_or_retracted_ids']) or 'none'}")
        print(f"Independent audit coverage: {z['independently_audited_percent']:.3f}%")
        print(f"USA events: {z['full_USA_events']}/45; release gates: {z['passed_release_gates']}/12")
if __name__=="__main__":
    main()
