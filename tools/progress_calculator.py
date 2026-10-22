#!/usr/bin/env python3
"""Deterministic fixed-scope UR-Recomp progress calculator (stdlib only)."""
import argparse
import json
from pathlib import Path

WEIGHTS = {
    "WIN-01": 6, "ENG-01": 10, "ENG-02": 8, "UI-01": 10,
    "DATA-01": 10, "DATA-02": 10, "VIS-01": 10, "VIS-02": 10,
    "FID-01": 10, "QA-01": 10, "UX-01": 6,
}
STAGES = {"planned": 0.0, "implemented": 0.5, "tested": 0.75, "accepted": 1.0}
ROOT = Path(__file__).resolve().parents[1]

def calculate(inventory, ledger, accepted_events=None):
    if inventory.get("schema") != "ur-progress-inventory/1" or inventory.get("version") != "windows-beta-v1":
        raise ValueError("Unsupported inventory schema/version")
    if inventory.get("scoring") != STAGES:
        raise ValueError("Scoring contract changed")
    items = inventory.get("items")
    if not isinstance(items, list) or len(items) != len(WEIGHTS):
        raise ValueError("Frozen inventory length changed")
    ids = [x.get("id") for x in items]
    if len(set(ids)) != len(ids) or set(ids) != set(WEIGHTS):
        raise ValueError("Duplicate or missing frozen IDs")
    maturity, accepted_weight, measured = 0, 0, 0
    by_stage = {stage: 0 for stage in STAGES}
    for item in items:
        key = item["id"]
        if type(item.get("weight")) is not int or item["weight"] != WEIGHTS[key]:
            raise ValueError("Frozen weight changed: " + key)
        stage = item.get("status")
        if stage not in STAGES:
            raise ValueError("Unknown status: " + key)
        url = item.get("evidence")
        if stage != "planned" and (not isinstance(url, str) or not url.startswith("https://github.com/gamesbyian/UR-Recomp/")):
            raise ValueError("Implemented/tested status lacks repository evidence: " + key)
        if stage == "accepted" and (not isinstance(item.get("accepted_evidence"), str) or
                                     not item["accepted_evidence"].startswith("https://")):
            raise ValueError("Accepted status lacks independent acceptance evidence: " + key)
        if stage == "planned" and item.get("accepted_evidence"):
            raise ValueError("Planned item carries acceptance evidence: " + key)
        by_stage[stage] += 1
        maturity += WEIGHTS[key] * STAGES[stage]
        accepted_weight += WEIGHTS[key] if stage == "accepted" else 0
        measured += 1 if stage != "planned" else 0
    gates = ledger.get("gates")
    if not isinstance(gates, list) or len(gates) != 12:
        raise ValueError("Expected exactly 12 authoritative QA gates")
    gate_ids = [g.get("id") for g in gates]
    if set(gate_ids) != {f"QA-{i:02d}" for i in range(1, 13)}:
        raise ValueError("Incorrect or duplicate release gate IDs")
    passed = sum(g["status"] == "passed" for g in gates)
    if accepted_events is not None and (type(accepted_events) is not int or not 0 <= accepted_events <= 45):
        raise ValueError("Accepted events must be an independently verified 0..45 integer")
    return {
        "version": inventory["version"],
        "scope": inventory["scope"],
        "inventory_source_sha": inventory["source_sha"],
        "engineering_maturity_percent": round(maturity, 2),
        "accepted_inventory_percent": accepted_weight,
        "evidenced_inventory_items": measured,
        "inventory_total_items": len(items),
        "items_by_stage": by_stage,
        "windows_release_gates_passed": passed,
        "windows_release_gates_total": 12,
        "independent_usa_events_passed": accepted_events,
        "independent_usa_events_total": 45,
        "historical_subjective_estimate_percent": 60,
        "disclaimer": "Engineering maturity is provisional weighted status credit, not release completion. Zero awarded QA gates does not erase implemented or tested features.",
    }

def markdown(result):
    event = "not supplied" if result["independent_usa_events_passed"] is None else str(result["independent_usa_events_passed"]) + "/45"
    return ("# UR-Recomp progress (fixed inventory v1)\n\n"
            f"- Provisional engineering maturity: **{result['engineering_maturity_percent']:.2f}%**\n"
            f"- Independently accepted inventory: **{result['accepted_inventory_percent']}%**\n"
            f"- Evidenced criteria: **{result['evidenced_inventory_items']}/{result['inventory_total_items']}**\n"
            f"- Full Windows QA gates: **{result['windows_release_gates_passed']}/12**\n"
            f"- Independently accepted complete USA events: **{event}**\n"
            f"- Historical subjective estimate: **60%**, not comparable to the new score\n\n"
            f"{result['disclaimer']}\n")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory", type=Path, default=ROOT / "docs/PROGRESS-INVENTORY.json")
    p.add_argument("--ledger", type=Path, default=ROOT / "docs/RELEASE-QUALITY-LEDGER.json")
    p.add_argument("--accepted-events", type=int, help="Verified count from authoritative original course census")
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = p.parse_args()
    result = calculate(json.loads(args.inventory.read_text(encoding="utf-8")),
                       json.loads(args.ledger.read_text(encoding="utf-8")),
                       args.accepted_events)
    print(json.dumps(result, indent=2) if args.format == "json" else markdown(result), end="\n")

if __name__ == "__main__":
    main()
