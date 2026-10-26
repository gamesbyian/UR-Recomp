#!/usr/bin/env python3
"""Source-bound scenario ranges for remaining UR-Recomp effort; NOT release dates."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "docs/progress/remaining-work-prior-v1.json"
INVENTORY = ROOT / "docs/progress/windows-beta-v2-inventory.json"
ADJUST = ROOT / "docs/progress/remaining-work-adjustments.json"

def _range(values, label):
    if not (isinstance(values, list) and len(values) == 3 and
            all(type(v) in (int, float) and v >= 0 for v in values) and
            values[0] <= values[1] <= values[2] and values[2] > 0):
        raise ValueError("Bad optimistic/likely/pessimistic range: " + label)
    return values

def calculate(prior, inventory, adjustments=None, samples=3000, seed=20261026):
    if prior.get("schema") != "ur-effort-prior/1":
        raise ValueError("Wrong effort prior schema")
    if inventory.get("version") != "windows-beta-v2-candidate" or (
            inventory.get("frozen_contract_fnv1a32") != prior.get("contract_hash")):
        raise ValueError("Wrong/forked 135-criterion completion contract")
    ids = [item["id"] for item in inventory["criteria"]]
    if len(ids) != 135 or len(set(ids)) != 135:
        raise ValueError("Expected 135 distinct frozen criteria")
    groups = prior["group_tiers"]
    tiers = prior["tier_ranges"]
    for name, values in tiers.items():
        _range(values, name)
    exceptions = prior["overrides"]
    if set(exceptions) - set(ids) or any(tier not in tiers for tier in exceptions.values()):
        raise ValueError("Unknown estimate exception")
    if samples < 100 or samples > 100000:
        raise ValueError("Samples must be 100..100000")
    remaining = [item for item in inventory["criteria"] if item["status"] != "bounded_verified"]
    remaining_ids = {item["id"] for item in remaining}
    jobs = []
    for item in remaining:
        key = item["id"]
        tier = exceptions.get(key, groups.get(item["area"]))
        if tier not in tiers:
            raise ValueError("Missing tier for " + key)
        jobs.append({"id": key, "group": item["area"], "range": tiers[tier], "tier": tier})
    # Separately estimate independent review debt for PR-screened (not audited)
    # criteria. This is verification effort, never another completion point.
    audit_debt = [item for item in inventory["criteria"]
                  if item["status"] == "bounded_verified" and
                  item["audit_state"] != "independent_reviewed"]
    for item in audit_debt:
        jobs.append({"id": "AUDIT-" + item["id"], "group": "AUDIT",
                     "range": [0.25, 1.0, 3.0], "tier": "review"})
    for shared in prior["shared"]:
        _range(shared["range"], shared["id"])
        dependents = set(shared.get("dependent_ids", []))
        prefix = shared.get("dependent_prefix")
        if prefix:
            dependents |= {key for key in ids if key.startswith(prefix)}
        dependents |= set(shared.get("extra", []))
        dependents -= set(shared.get("exclude", []))
        if not dependents or not dependents <= set(ids):
            raise ValueError("Shared dependency missing or invalid: " + shared["id"])
        if dependents & remaining_ids:
            jobs.append({"id": shared["id"], "group": "SHARED", "range": shared["range"], "tier": "shared"})
    if adjustments:
        if adjustments.get("schema") != "ur-effort-adjustments/1":
            raise ValueError("Bad adjustments schema")
        if adjustments.get("baseline_sha") != prior["source_sha"]:
            raise ValueError("Adjustments must name frozen initial source")
        used = set()
        for change in adjustments.get("changes", []):
            key = change["id"]
            if key in used:
                raise ValueError("Duplicate adjustment ID " + key)
            used.add(key)
            candidates = [job for job in jobs if job["id"] == key]
            if len(candidates) != 1:
                raise ValueError("Adjustment to completed or unknown job: " + key)
            if not isinstance(change.get("evidence"), str) or not change["evidence"].startswith("https://github.com/gamesbyian/UR-Recomp/"):
                raise ValueError("Adjustment needs a repository evidence link: " + key)
            if not change.get("reason") or len(change["reason"]) < 12:
                raise ValueError("Adjustment needs a reason")
            candidates[0]["range"] = _range(change["range"], key)
    # Per-job deterministic streams keep comparisons stable when a task is completed.
    streams = {job["id"]: random.Random("%s:%s" % (seed, job["id"])) for job in jobs}
    totals = []
    group_samples = defaultdict(list)
    for _ in range(samples):
        group_totals = defaultdict(float)
        for job in jobs:
            low, mode, high = job["range"]
            group_totals[job["group"]] += streams[job["id"]].triangular(low, high, mode)
        for group in set(group_totals) | {"SHARED"}:
            group_samples[group].append(group_totals[group])
        totals.append(sum(group_totals.values()))
    totals.sort()
    def percentile(sorted_values, p):
        return round(sorted_values[int((len(sorted_values)-1)*p)], 1)
    by_group = {}
    for group, values in sorted(group_samples.items()):
        values.sort()
        by_group[group] = {
            "p10": percentile(values, .10), "median": percentile(values, .50),
            "p90": percentile(values, .90),
            "jobs": sum(1 for job in jobs if job["group"] == group),
        }
    return {
        "as_of_source": inventory["source_sha"],
        "frozen_contract": prior["contract_hash"],
        "product_criteria_total": len(ids),
        "product_criteria_remaining": len(remaining),
        "unreviewed_provisional_criteria": len(audit_debt),
        "one_time_shared_tasks_remaining": sum(job["group"]=="SHARED" for job in jobs),
        "external_validation_dependencies_remaining": sum(x["id"] in remaining_ids for x in
            ({"id": v} for v in prior["external_validation"])),
        "units": prior["unit"],
        "remaining_effort_p10": percentile(totals, .10),
        "remaining_effort_median": percentile(totals, .50),
        "remaining_effort_p90": percentile(totals, .90),
        "group_estimates": by_group,
        "scenario_samples": samples,
        "forecast_dates": None,
        "calibration_status": "Expert relative-work priors ONLY; no observed agent-hours or active delivery throughput. No defensible calendar projection.",
    }

def markdown(report):
    lines = ["# Remaining engineering effort (hypothesis, not measured hours)", "",
        "Reviewed product source: " + report["as_of_source"],
        "Unfinished fixed criteria: " + str(report["product_criteria_remaining"]) +
        "; provisional criteria awaiting independent bounded review: " +
        str(report["unreviewed_provisional_criteria"]) +
        "; one-time shared blockers: " + str(report["one_time_shared_tasks_remaining"]),
        "Remaining relative units, scenario P10 / median / P90: " +
        " / ".join(str(report[k]) for k in
            ("remaining_effort_p10","remaining_effort_median","remaining_effort_p90")),
        "Outstanding tasks involving external/physical review: " +
            str(report["external_validation_dependencies_remaining"]), "",
        "| Workstream | Jobs | P10 | Median | P90 |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for g, x in report["group_estimates"].items():
        lines.append("| %s | %s | %s | %s | %s |" %
                     (g, x["jobs"], x["p10"], x["median"], x["p90"]))
    lines += ["", report["calibration_status"],
        "Percentiles describe an assumed relative-work model, NOT empirical confidence intervals. "
        "Shared dependencies are counted once. Human availability, agent concurrency and full "
        "original/native unknowns can exceed the modeled P90."]
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prior", type=Path, default=PRIOR)
    p.add_argument("--inventory", type=Path, default=INVENTORY)
    p.add_argument("--adjustments", type=Path, default=ADJUST)
    p.add_argument("--format", choices=["json","markdown"], default="markdown")
    p.add_argument("--reviewed-head", help="Require the inventory to be pinned to this exact SHA")
    p.add_argument("--samples", type=int, default=3000)
    args = p.parse_args()
    prior = json.loads(args.prior.read_text(encoding="utf-8"))
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    if args.reviewed_head and inventory["source_sha"] != args.reviewed_head:
        p.error("STALE inventory; review latest main before claiming current work forecast")
    updates = json.loads(args.adjustments.read_text(encoding="utf-8"))
    result = calculate(prior, inventory, updates, args.samples)
    print(json.dumps(result, indent=2) if args.format=="json" else markdown(result))

if __name__ == "__main__":
    main()
