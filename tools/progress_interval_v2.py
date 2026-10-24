#!/usr/bin/env python3
"""Report *previous-review to current-review* v2 progress, not just lifetime baseline.

No network, Git checkout, or third party packages required. The evidence manifest
is curated by an agent who reviewed every intervening merge; this tool checks
internal consistency and prevents silent v2 status/QA upgrades or stale claims.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.atomic_progress_v2 import validate as validate_v2

DEFAULT_INVENTORY = ROOT / "docs/progress/windows-beta-v2-inventory.json"
DEFAULT_LEDGER = ROOT / "docs/RELEASE-QUALITY-LEDGER.json"
REVIEW_POINTER = ROOT / "docs/progress/current-v2-review.json"
DEFAULT_PREVIOUS = ROOT / "docs/progress/v2-review-checkpoint-20261024T1708.json"
DEFAULT_INTERVAL = ROOT / "docs/progress/v2-review-interval-20261024T1850.json"
EFFECTS = {"direct_product", "release_risk_reduction", "enabling_infrastructure",
           "operations", "documentation", "deferred_or_research"}
STATUS_VALUES = {"unverified", "bounded_verified", "regressed"}
AUDIT_VALUES = {"pending", "inherited_pr_screening", "independent_reviewed"}

def _sha(value):
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)

def compare(previous, inventory, ledger, interval, reviewed_head):
    current = validate_v2(inventory, ledger)
    if not _sha(reviewed_head):
        raise ValueError("Provide a full reviewed upstream source SHA")
    if not _sha(previous.get("at_main_sha")) or not _sha(interval.get("from_main_sha")):
        raise ValueError("Previous checkpoint source SHA malformed")
    if (interval.get("through_main_sha") != reviewed_head or
            inventory.get("source_sha") != reviewed_head):
        raise ValueError("STALE: inventory and interval must match explicitly reviewed source SHA")
    if previous.get("at_main_sha") != interval.get("from_main_sha"):
        raise ValueError("Gap or overlap: previous checkpoint not the interval's starting commit")
    if previous.get("inventory_version") != inventory["version"] or previous.get("criterion_contract_hash") != inventory["frozen_contract_fnv1a32"]:
        raise ValueError("Incompatible frozen criterion contract")
    if previous.get("fixed_denominator_units") != 4500:
        raise ValueError("Prior denominator was modified")
    old_rows = previous.get("criteria")
    if not isinstance(old_rows, list) or len(old_rows) != 135:
        raise ValueError("Historical review must snapshot all 135 criteria")
    old = {}
    for row in old_rows:
        if not isinstance(row, dict) or row.get("id") in old or row.get("status") not in STATUS_VALUES or row.get("audit_state") not in AUDIT_VALUES:
            raise ValueError("Invalid or duplicate criterion in previous checkpoint")
        old[row["id"]] = row
    rows = inventory["criteria"]
    if set(old) != {c["id"] for c in rows}:
        raise ValueError("Frozen IDs differ across checkpoint")
    if interval.get("schema") != "ur-v2-reviewed-interval/1":
        raise ValueError("Invalid interval schema")
    merges = interval.get("merge_records")
    if not isinstance(merges, list) or not merges or len(merges) != interval.get("observed_merge_count"):
        raise ValueError("Merge record count does not match reviewed interval")
    seen_pr, seen_commit = set(), set()
    for m in merges:
        sha, n = m.get("commit_sha"), m.get("pr")
        if not _sha(sha) or type(n) is not int or n <= 0:
            raise ValueError("Missing merge SHA or PR identity")
        if sha in seen_commit or n in seen_pr:
            raise ValueError("Duplicate PR or commit in merge interval")
        seen_commit.add(sha)
        seen_pr.add(n)
        if m.get("pr_url") != f"https://github.com/gamesbyian/UR-Recomp/pull/{n}":
            raise ValueError("PR URL does not match its number")
        if m.get("effect") not in EFFECTS or not str(m.get("observation", "")).strip():
            raise ValueError("Merge effect and rationale required")
    if merges[-1]["commit_sha"] != reviewed_head:
        raise ValueError("Reviewed main head is not the last observed merge")
    transitions = []
    for c in rows:
        old_row = old[c["id"]]
        if old_row["status"] != c["status"] or old_row["audit_state"] != c["audit_state"]:
            transitions.append({"id": c["id"], "before": old_row["status"], "after": c["status"],
                                "audit_before": old_row["audit_state"], "audit_after": c["audit_state"]})
    recorded = interval.get("criterion_changes", [])
    if not isinstance(recorded, list) or len(recorded) != len(transitions):
        raise ValueError("Undocumented criterion change detected")
    matches = {x["id"]:x for x in transitions}
    if len({x.get("id") for x in recorded}) != len(recorded):
        raise ValueError("Duplicate criterion transition record")
    for change in recorded:
        expect = matches.get(change.get("id"))
        if expect is None or any(change.get(k) != v for k,v in expect.items()):
            raise ValueError("Transition history doesn't match status change")
        if not isinstance(change.get("evidence"), list) or not change["evidence"]:
            raise ValueError("Transition requires pinned evidence")
        if not str(change.get("reason", "")).strip():
            raise ValueError("Transition needs rationale")
    prev_units = sum(10 if id.startswith("FID-") else 45 for id, c in old.items()
                     if c["status"] == "bounded_verified")
    prev_audit_units = sum(10 if id.startswith("FID-") else 45 for id, c in old.items()
                           if c["audit_state"] == "independent_reviewed")
    current_qa = current["formal_windows_gates_passed"]
    current_events = current["independent_USA_complete_events"]
    for name, old_count, current_count, declared in [
        ("QA", previous.get("passed_release_gates"), current_qa, interval.get("formal_release_gates_delta")),
        ("USA", previous.get("formal_events"), current_events, interval.get("formal_events_delta"))]:
        if type(old_count) is not int or type(declared) is not int or current_count - old_count != declared:
            raise ValueError("Unsubstantiated " + name + " acceptance delta")
    mix = dict(sorted(Counter(m["effect"] for m in merges).items()))
    return {
        "from_reviewed_main": previous["at_main_sha"],
        "through_reviewed_main": reviewed_head,
        "previous_product_percent": round(prev_units * 100 / 4500, 3),
        "current_product_percent": current["bounded_product_coverage_percent"],
        "interval_product_delta_points": round((current["bounded_product_coverage_percent"] - prev_units * 100/4500), 3),
        "previous_independent_audit_percent":round(prev_audit_units * 100/4500, 3),
        "current_independent_audit_percent": current["independently_audited_coverage_percent"],
        "newly_verified": [t["id"] for t in transitions if t["before"] != "bounded_verified" and t["after"] == "bounded_verified"],
        "retracted": [t["id"] for t in transitions if t["before"] == "bounded_verified" and t["after"] != "bounded_verified"],
        "other_audit_transitions": [t["id"] for t in transitions if t["audit_before"] != t["audit_after"]],
        "accepted_USA_events":current_events,
        "accepted_USA_delta":interval["formal_events_delta"],
        "passed_release_gates":current_qa,
        "release_gate_delta":interval["formal_release_gates_delta"],
        "reviewed_merge_count":len(merges),
        "merged_work_mix":mix,
        "interpretation":"This interval's merged work mix is not a completion score or labor-hour productivity measure. QA ledger and event census remain authoritative."
    }

def markdown(r):
    lines = ["# UR-Recomp product progress | reviewed interval", "",
       f"Source: `{r['from_reviewed_main']}` → `{r['through_reviewed_main']}`",
       f"**Screened Windows beta:** {r['previous_product_percent']:.3f}% → **{r['current_product_percent']:.3f}%** ({r['interval_product_delta_points']:+.3f} pp)",
       f"**Independent criteria audit:** {r['previous_independent_audit_percent']:.3f}% → {r['current_independent_audit_percent']:.3f}%",
       f"**USA event admissions:** {r['accepted_USA_events']}/45 ({r['accepted_USA_delta']:+d})",
       f"**Windows release gates:** {r['passed_release_gates']}/12 ({r['release_gate_delta']:+d})",
       f"**Newly proven:** {', '.join(r['newly_verified']) or 'none'}",
       f"**Retracted:** {', '.join(r['retracted']) or 'none'}",
       f"Reviewed merged commits: {r['reviewed_merge_count']}", "", "Source-reviewed work mix:"]
    for k, v in r["merged_work_mix"].items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", r["interpretation"]])
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reviewed-head", required=True)
    p.add_argument("--previous", type=Path, default=None, help="Prior full status snapshot; defaults to current-v2-review pointer")
    p.add_argument("--interval", type=Path, default=None, help="Source-reviewed merge interval; defaults to current-v2-review pointer")
    p.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    a = p.parse_args()
    if a.previous is None or a.interval is None:
        pointer = json.loads(REVIEW_POINTER.read_text(encoding="utf-8"))
        if pointer.get("schema") != "ur-v2-review-pointer/1":
            raise ValueError("Invalid current review pointer")
        if pointer.get("reviewed_main_sha") != a.reviewed_head:
            raise ValueError("STALE: current review pointer differs from requested source HEAD")
        previous = a.previous or ROOT / pointer["previous"]
        interval = a.interval or ROOT / pointer["interval"]
    else:
        previous, interval = a.previous, a.interval
    for path in (previous, interval):
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Interval review paths must stay in the repository")
    files = [previous, a.inventory, a.ledger, interval]
    result = compare(*(json.loads(p.read_text(encoding="utf-8")) for p in files), a.reviewed_head)
    print(json.dumps(result, indent=2) if a.format == "json" else markdown(result))

if __name__ == "__main__":
    main()
