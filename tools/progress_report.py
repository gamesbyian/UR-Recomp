#!/usr/bin/env python3
"""Produce a deterministic progress report including evidence throughput and staleness."""
import argparse
import json
from collections import Counter
from pathlib import Path
from tools.progress_calculator import calculate

ROOT=Path(__file__).resolve().parents[1]

def build_report(inventory, ledger, changelog, reviewed_sha):
    if not isinstance(reviewed_sha,str) or len(reviewed_sha)!=40 or any(c not in '0123456789abcdef' for c in reviewed_sha):
        raise ValueError("Expected a full source SHA")
    entries=changelog.get("entries",[])
    if not entries:
        raise ValueError("Missing changelog")
    latest=entries[-1]
    if latest.get("source_commit")!=reviewed_sha:
        raise ValueError("STALE report: reviewed SHA differs from latest evidence checkpoint")
    metric=calculate(inventory,ledger)
    previous=entries[-2] if len(entries)>1 else None
    new_evidence=latest.get("changes",[])
    if not isinstance(new_evidence,list):
        raise ValueError("Malformed evidence changes")
    seen=set()
    for change in new_evidence:
        uri=change.get("evidence")
        if not isinstance(uri,str) or not uri.startswith("https://github.com/gamesbyian/UR-Recomp/"):
            raise ValueError("Missing or invalid provenance URL")
        if uri in seen:
            raise ValueError("Duplicate evidence URL within reporting interval")
        seen.add(uri)
    prev_score=latest.get("engineering_maturity_before")
    next_score=latest.get("engineering_maturity_after")
    if prev_score is not None and next_score is not None:
        if next_score!=metric["engineering_maturity_percent"]:
            raise ValueError("Latest milestone score differs from calculator")
        delta=round(next_score-prev_score,2)
    else:
        delta=None
    categories=dict(sorted(Counter(c.get("category","unspecified") for c in new_evidence).items()))
    return {
        "reviewed_sha":reviewed_sha,"date":latest.get("date"),
        "engineering_maturity_percent":metric["engineering_maturity_percent"],
        "engineering_maturity_delta_points":delta,
        "independently_accepted_weight_percent":metric["accepted_inventory_percent"],
        "release_gates_passed":metric["windows_release_gates_passed"],
        "release_gates_total":metric["windows_release_gates_total"],
        "event_delta":latest.get("formal_event_delta"),
        "release_gate_delta":latest.get("formal_qa_gate_delta"),
        "new_unique_evidence_items":len(new_evidence),
        "evidence_by_workstream":categories,
        "previous_review_sha": previous.get("source_commit") if previous else None,
        "interpretation":"Evidence counts are traceable output, not percentage completion or independent acceptance."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reviewed-head",required=True)
    p.add_argument("--format",choices=("json","markdown"),default="markdown")
    args=p.parse_args()
    data=build_report(*[json.loads((ROOT / path).read_text(encoding="utf-8")) for path in
        ("docs/PROGRESS-INVENTORY.json","docs/RELEASE-QUALITY-LEDGER.json","docs/PROGRESS-CHANGELOG.json")],args.reviewed_head)
    if args.format=="json":
        print(json.dumps(data,indent=2))
    else:
        print("# UR-Recomp evidence-backed progress\n")
        print("Reviewed SHA:",data["reviewed_sha"])
        print("Engineering maturity:",f'{data["engineering_maturity_percent"]:.2f}%')
        print("Delta (percentage points):",data["engineering_maturity_delta_points"] if data["engineering_maturity_delta_points"] is not None else "unmeasured")
        print("New traceable engineering changes:",data["new_unique_evidence_items"])
        print("Accepted inventory:",str(data["independently_accepted_weight_percent"])+"%")
        print("Release QA gates:",str(data["release_gates_passed"])+"/12")
        print("Event change:",data["event_delta"])
        print("\nEvidence by workstream:")
        for category,count in data["evidence_by_workstream"].items():
            print("-",category+":",count)
        print("\n"+data["interpretation"])

if __name__=="__main__":
    main()
