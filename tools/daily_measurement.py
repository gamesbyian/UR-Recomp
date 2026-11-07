#!/usr/bin/env python3
"""Daily agent work measurements, separate from certified release/criterion acceptance.

Source-controlled events update a *provisional engineering* estimate and prospective
remaining relative work. Neither PR titles nor commit counts earn progress.
No network, external modules, new CI dispatch or background worker required.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.atomic_progress_v2 import validate as validate_v2
from tools.remaining_work_forecast import calculate as forecast

DAILY = ROOT / "docs/progress/daily"
INVENTORY = ROOT / "docs/progress/windows-beta-v2-inventory.json"
PRIOR = ROOT / "docs/progress/remaining-work-prior-v1.json"
ADJUSTMENTS = ROOT / "docs/progress/remaining-work-adjustments.json"
RELEASE = ROOT / "docs/RELEASE-QUALITY-LEDGER.json"
MILESTONES = DAILY / "milestones-v1.json"
EVENTS = DAILY / "entries"
REPO_URL = "https://github.com/gamesbyian/UR-Recomp/"
SHA = re.compile(r"^[0-9a-f]{40}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
EVENT_KINDS = {"milestone", "effort_revision", "research", "risk_reduction",
               "regression", "infrastructure", "acceptance"}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def mean(triple):
    return sum(triple) / 3

def check_range(r, context):
    if (not isinstance(r, list) or len(r) != 3 or
            not all(type(n) in (float, int) and 0 <= n <= 1000 for n in r) or
            not r[0] <= r[1] <= r[2]):
        raise ValueError("Invalid [optimistic, likely, pessimistic] range: " + context)

def job_ranges(prior, inventory, adjustments):
    """Mirror original prior's jobs, including one-time shared and audit debt."""
    ids = [c["id"] for c in inventory["criteria"]]
    open_ids = {c["id"] for c in inventory["criteria"]
                if c["status"] != "bounded_verified"}
    jobs = {}
    for c in inventory["criteria"]:
        key = c["id"]
        if key in open_ids:
            tier = prior["overrides"].get(key, prior["group_tiers"].get(c["area"]))
            jobs[key] = list(prior["tier_ranges"][tier])
        elif c["audit_state"] != "independent_reviewed":
            jobs["AUDIT-" + key] = [0.25, 1, 3]
    for shared in prior["shared"]:
        dependencies = set(shared.get("dependent_ids", []))
        if shared.get("dependent_prefix"):
            dependencies.update(k for k in ids if k.startswith(shared["dependent_prefix"]))
        dependencies.update(shared.get("extra", []))
        dependencies.difference_update(shared.get("exclude", []))
        if dependencies & open_ids:
            jobs[shared["id"]] = list(shared["range"])
    for done in adjustments.get("completed_shared", []):
        jobs.pop(done["id"], None)
    for revision in adjustments.get("changes", []):
        key = revision["id"]
        if key not in jobs:
            raise ValueError("Baseline adjustment targets an absent job " + key)
        jobs[key] = list(revision["range"])
    for key, r in jobs.items():
        check_range(r, key)
    return jobs

def validate_milestones(data, inventory):
    if data.get("schema") != "ur-daily-milestones/1":
        raise ValueError("Unknown milestone schema")
    if data.get("contract") != inventory["frozen_contract_fnv1a32"]:
        raise ValueError("Frozen denominator/criterion fingerprint mismatch")
    by_id = {c["id"]: c for c in inventory["criteria"]}
    seen, totals, milestones = set(), {}, {}
    if not isinstance(data.get("milestones"), list):
        raise ValueError("Milestones must be a list")
    for m in data["milestones"]:
        mid, parent, weight = m.get("id"), m.get("criterion_id"), m.get("weight_units")
        if not isinstance(mid, str) or not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", mid):
            raise ValueError("Bad milestone ID")
        if mid in seen or parent not in by_id:
            raise ValueError("Duplicate milestone or unknown parent " + mid)
        if type(weight) is not int or weight <= 0:
            raise ValueError("Milestone weights must be positive integers")
        if not str(m.get("deliverable", "")).strip() or not str(m.get("limitation", "")).strip():
            raise ValueError("Describe observable deliverable and its limits")
        seen.add(mid)
        milestones[mid] = m
        totals[parent] = totals.get(parent, 0) + weight
    for parent, total in totals.items():
        if total > by_id[parent]["weight_units"]:
            raise ValueError("Milestone weights exceed frozen parent capacity " + parent)
    return milestones

def validate_entry(e, milestones, jobs):
    if e.get("schema") != "ur-agent-work-measurement/1":
        raise ValueError("Unknown event schema")
    if not isinstance(e.get("event_id"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{5,90}", e["event_id"]):
        raise ValueError("Event needs stable slug ID")
    if not DATE.fullmatch(str(e.get("recorded_at", ""))):
        raise ValueError("Event needs a UTC timestamp with seconds")
    if not SHA.fullmatch(str(e.get("source_main_sha", ""))):
        raise ValueError("Event needs exact 40-character main source SHA")
    if e.get("kind") not in EVENT_KINDS:
        raise ValueError("Unknown event kind")
    if not str(e.get("work_id", "")).strip() or not str(e.get("recorded_by", "")).strip():
        raise ValueError("Missing work ID or contributor")
    if not str(e.get("outcome", "")).strip() or not str(e.get("remaining", "")).strip():
        raise ValueError("Outcome and next remaining discriminator required")
    if not str(e.get("source_pr", "")).startswith(REPO_URL + "pull/"):
        raise ValueError("Event needs originating repository PR")
    links = e.get("evidence")
    if not isinstance(links, list) or not links or not all(
            isinstance(link, str) and link.startswith(REPO_URL) for link in links):
        raise ValueError("Event needs direct source-owned evidence URL(s)")
    mid = e.get("milestone_id")
    state = e.get("milestone_state")
    if e["kind"] == "milestone":
        if mid not in milestones or state not in ("provisional", "reviewed", "withdrawn"):
            raise ValueError("Milestone event must identify a registered milestone and state")
        if state == "reviewed" and (
                not str(e.get("reviewed_by", "")).strip()
                or e["reviewed_by"] == e["recorded_by"]):
            raise ValueError("Independently reviewed milestone needs a distinct reviewer")
    elif mid is not None or state is not None:
        raise ValueError("Only milestone events can affect engineering completion")
    update = e.get("effort_update")
    if update is not None:
        if not isinstance(update, dict) or update.get("job_id") not in jobs:
            raise ValueError("Effort update needs an active, uncompleted job ID")
        check_range(update.get("from"), "effort from")
        check_range(update.get("to"), "effort to")
        if update.get("reason_type") not in ("earned", "re_estimate", "regression"):
            raise ValueError("Effort update needs explicit cause classification")
        if len(str(update.get("reason", "")).strip()) < 20:
            raise ValueError("Effort revision needs an explanatory reason")
    return e

def calculate_daily(inventory, ledger, prior, adjustments, milestones_spec,
                    entries, snapshot_sha, reviewed_sha):
    accepted = validate_v2(inventory, ledger)
    if not SHA.fullmatch(snapshot_sha) or not SHA.fullmatch(reviewed_sha):
        raise ValueError("Snapshot and reviewed-source SHA must be exact")
    milestones = validate_milestones(milestones_spec, inventory)
    jobs = job_ranges(prior, inventory, adjustments)
    baseline = forecast(prior, inventory, adjustments, samples=100)
    original_total = mean([0, 0, 0]) + sum(mean(r) for r in jobs.values())
    if abs(original_total - baseline["expected_relative_work_units"]) > 0.051:
        raise ValueError("Prospective cost model drifted from frozen prior")
    by_parent = {x["id"]: x for x in inventory["criteria"]}
    seen, stage = set(), {}
    impacts, detail = [], []
    for e in sorted(entries, key=lambda x: (x["recorded_at"], x["event_id"])):
        validate_entry(e, milestones, jobs)
        if e["event_id"] in seen:
            raise ValueError("Duplicate event ID " + e["event_id"])
        seen.add(e["event_id"])
        if e["kind"] == "milestone":
            m = milestones[e["milestone_id"]]
            stage[m["id"]] = e["milestone_state"]
            detail.append({"event_id": e["event_id"], "milestone_id": m["id"],
                           "criterion_id": m["criterion_id"], "state": e["milestone_state"],
                           "source_pr": e["source_pr"]})
        if e.get("effort_update"):
            change = e["effort_update"]
            key = change["job_id"]
            if list(jobs[key]) != list(change["from"]):
                raise ValueError("Stale or duplicate effort revision for " + key)
            delta = mean(change["to"]) - mean(change["from"])
            jobs[key] = list(change["to"])
            impacts.append({"event_id": e["event_id"], "job_id": key,
                            "delta_work_units": round(delta, 2),
                            "reason_type": change["reason_type"]})
    confirmed_extra = provisional_extra = 0
    credited = []
    for mid, state in sorted(stage.items()):
        m = milestones[mid]
        if by_parent[m["criterion_id"]]["status"] == "bounded_verified":
            continue  # Strictly no second credit for a certified parent.
        units = m["weight_units"]
        if state == "reviewed":
            confirmed_extra += units
            credited.append({"milestone_id": mid, "state": state, "weight_units": units})
        elif state == "provisional":
            provisional_extra += units
            credited.append({"milestone_id": mid, "state": state, "weight_units": units})
    formal_covered_units = sum(c["weight_units"] for c in inventory["criteria"]
                               if c["status"] == "bounded_verified")
    if formal_covered_units > 4500:
        raise ValueError("Invalid formal weighted coverage")
    center = (formal_covered_units + confirmed_extra + provisional_extra * .5) / 45
    low = (formal_covered_units + confirmed_extra) / 45
    high = (formal_covered_units + confirmed_extra + provisional_extra) / 45
    delta_total = sum(x["delta_work_units"] for x in impacts)
    milestone_model_hash = hashlib.sha256(json.dumps(
        milestones_spec, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "schema": "ur-daily-engineering-report/1",
        "as_of_source": snapshot_sha,
        "formal_reviewed_source": reviewed_sha,
        "model": milestones_spec["schema"] + "/" + milestones_spec["contract"] + "/" + milestone_model_hash[:16],
        "milestone_allocation_sha256": milestone_model_hash,
        "formal_bounded_percent": accepted["bounded_product_coverage_percent"],
        "independently_reviewed_percent": accepted["independently_audited_coverage_percent"],
        "engineering_estimate_percent": round(center, 2),
        "engineering_recorded_evidence_range_percent": [round(low, 2), round(high, 2)],
        "estimate_caveat": "Partial source-linked ledger, NOT a complete calibrated uncertainty range or release acceptance",
        "relative_work_units": round(sum(mean(r) for r in jobs.values()), 1),
        "prior_only_work_units": baseline["expected_relative_work_units"],
        "work_unit_delta_from_recorded_revisions": round(delta_total, 1),
        "unit_caveat": "Expert relative-work units, not hours or completion dates",
        "review_backlog": baseline["unreviewed_provisional_criteria"],
        "remaining_criteria": baseline["product_criteria_remaining"],
        "usa_events_accepted": accepted["independent_USA_complete_events"],
        "release_gates_passed": accepted["formal_windows_gates_passed"],
        "observations_count": len(seen),
        "partial_milestones": credited,
        "effort_revision_effects": impacts,
    }

def read_entries(directory):
    files = sorted(Path(directory).glob("*.json"))
    entries = [load(p) for p in files]
    # Fail visibly on duplicate IDs or semantically conflicting revisions.
    return entries

def validate_provenance(entries, snapshot_sha):
    """Only count evidence pinned to an ancestor of current checkout."""
    if not (ROOT / ".git").exists():
        return  # library consumers/tests may not carry a working checkout
    for e in entries:
        rv = subprocess.run(["git", "-C", str(ROOT), "merge-base",
                             "--is-ancestor", e["source_main_sha"], snapshot_sha],
                            check=False, capture_output=True)
        if rv.returncode:
            raise ValueError("Event source not on inspected history: " + e["event_id"])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--entries", type=Path, default=EVENTS)
    parser.add_argument("--milestones", type=Path, default=MILESTONES)
    parser.add_argument("--source-sha", help="Reviewed latest main SHA; defaults to git HEAD")
    args = parser.parse_args()
    inv, led, prior, adj = map(load, (INVENTORY, RELEASE, PRIOR, ADJUSTMENTS))
    source = args.source_sha or subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    entries = read_entries(args.entries)
    validate_provenance(entries, source)
    report = calculate_daily(inv, led, prior, adj, load(args.milestones), entries,
                             source, inv["source_sha"])
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("# Daily engineering measurement")
        print("Current source:", report["as_of_source"])
        print("Engineering estimate: %.2f%% (recorded-source interval %s; incomplete evidence)" %
              (report["engineering_estimate_percent"],
               report["engineering_recorded_evidence_range_percent"]))
        print("Remaining relative work:", report["relative_work_units"],
              "(expert prior", report["prior_only_work_units"], ")")
        print("Formal bounded:", report["formal_bounded_percent"],
              "at", report["formal_reviewed_source"])
        print("USA:", report["usa_events_accepted"], "/45; QA gates:",
              report["release_gates_passed"], "/12")
        print("Recorded observations:", report["observations_count"],
              "; partial milestone records:", len(report["partial_milestones"]))
        print(report["estimate_caveat"])

if __name__ == "__main__":
    main()
