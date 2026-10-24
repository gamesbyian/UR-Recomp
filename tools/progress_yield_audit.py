#!/usr/bin/env python3
"""Classify the work mix in a complete, pinned main-commit interval."""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs/progress/merge-outcome-audit-20261024.json"
LANES = {"direct_product", "release_risk_reduction", "enabling_infrastructure",
         "operations", "documentation", "deferred_or_research"}

def summarize(data):
    if data.get("schema") != "ur-merge-outcome-audit/1":
        raise ValueError("Unexpected audit schema")
    rows = data.get("records", [])
    if not rows:
        raise ValueError("Missing merge records")
    shas = [x.get("commit_sha") for x in rows]
    if any(not isinstance(s, str) or len(s) != 40 for s in shas) or len(shas) != len(set(shas)):
        raise ValueError("Missing/duplicate merge SHA")
    for item in rows:
        if item.get("primary_effect") not in LANES:
            raise ValueError("Invalid primary work classification")
        if item.get("agent_hours") is not None:
            raise ValueError("Do not invent effort hours in a commit-based survey")
        n = item.get("pr_number")
        if n is not None and item.get("github_pr") != f"https://github.com/gamesbyian/UR-Recomp/pull/{n}":
            raise ValueError("PR URL does not match source PR")
    by_lane = dict(sorted(Counter(x["primary_effect"] for x in rows).items()))
    return {
        "base_sha": data["base_sha"], "through_sha": data["through_sha"],
        "total_main_commits": len(rows), "by_intended_effect": by_lane,
        "product_or_risk_related_commits": by_lane.get("direct_product", 0) + by_lane.get("release_risk_reduction", 0),
        "unmeasurable_from_commits": ["agent hours", "cost", "actual bug severity", "downstream unblock duration", "causal engineering ROI"],
        "disclaimer": "Commit counts classify work mix, not relative effort, productivity, released features or completed acceptance criteria. Titles/PR descriptions are first-pass evidence only."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit", type=Path, default=DEFAULT)
    p.add_argument("--format", choices=["json", "markdown"], default="markdown")
    a = p.parse_args()
    result = summarize(json.loads(a.audit.read_text(encoding="utf-8")))
    if a.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print("# Merge outcome screening\n")
        print(f"Pinned interval: {result['base_sha']} to {result['through_sha']}")
        print(f"Main commits: {result['total_main_commits']}")
        for k, v in result["by_intended_effect"].items():
            print(f"- {k}: {v}")
        print("\n" + result["disclaimer"])

if __name__ == "__main__":
    main()
