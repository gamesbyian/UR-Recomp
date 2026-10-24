#!/usr/bin/env python3
"""Windows-beta v2 atomic product coverage: screened evidence vs independent acceptance.

Only Python standard library. v1 and historic subjective scores are separate scales.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV_PATH = ROOT / "docs/progress/windows-beta-v2-inventory.json"
LEDGER_PATH = ROOT / "docs/RELEASE-QUALITY-LEDGER.json"
GROUP_COUNTS = {"WIN": 6, "ONE": 10, "TWO": 8, "MENU": 10, "DATA": 10,
                "RECOVERY": 10, "WIDE": 10, "ART": 10, "QA": 10, "UX": 6, "FID": 45}
CONTRACT_FINGERPRINT = "32c62b80"
STATUS = {"unverified", "bounded_verified", "regressed"}
AUDIT_STATES = {"pending", "inherited_pr_screening", "independent_reviewed"}

def _fingerprint(criteria):
    s = "\n".join(f"{c['id']}|{c['criterion']}|{c['weight_units']}" for c in criteria)
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xffffffff
    return f"{h:08x}"

def validate(inventory, ledger):
    if inventory.get("schema") != "ur-atomic-progress/2" or inventory.get("version") != "windows-beta-v2-candidate":
        raise ValueError("Unsupported v2 inventory")
    if inventory.get("fixed_denominator_units") != 4500:
        raise ValueError("Frozen v2 denominator altered")
    rows = inventory.get("criteria")
    if not isinstance(rows, list) or len(rows) != 135:
        raise ValueError("Exactly 135 frozen criteria required")
    if _fingerprint(rows) != CONTRACT_FINGERPRINT or inventory.get("frozen_contract_fnv1a32") != CONTRACT_FINGERPRINT:
        raise ValueError("Frozen criterion IDs, text or weights changed; create new version instead")
    expected = [f"{g}-{i:02d}" for g, n in GROUP_COUNTS.items() for i in range(1, n + 1)]
    if [x.get("id") for x in rows] != expected or len(set(expected)) != 135:
        raise ValueError("Criterion identities/order altered")
    group_units = {g: 0 for g in GROUP_COUNTS}
    seen_events = set()
    scored = audited = 0
    classified = {}
    for c in rows:
        area = c.get("area")
        if area not in GROUP_COUNTS or not c["id"].startswith(area + "-"):
            raise ValueError("Unknown criterion group")
        weight = 10 if area == "FID" else 45
        if type(c.get("weight_units")) is not int or c["weight_units"] != weight:
            raise ValueError("Criterion weight drift")
        group_units[area] += weight
        state, audit = c.get("status"), c.get("audit_state")
        if state not in STATUS or audit not in AUDIT_STATES:
            raise ValueError("Invalid criterion/audit status")
        evidence = c.get("evidence")
        if not isinstance(evidence, list):
            raise ValueError("Evidence must be a list")
        if state == "bounded_verified":
            if not evidence or not all(isinstance(u, str) and
                    u.startswith("https://github.com/gamesbyian/UR-Recomp/") for u in evidence):
                raise ValueError("Verification requires repository evidence URLs")
            scored += weight
        if audit == "independent_reviewed":
            if state != "bounded_verified" or not isinstance(c.get("audit_receipt"), str) or not c["audit_receipt"].startswith("https://"):
                raise ValueError("Independent audit needs verified status and separate audit receipt")
            audited += weight
        elif c.get("audit_receipt"):
            raise ValueError("Unreviewed criterion cannot carry independent receipt")
        if area == "FID":
            event_key = c.get("course_event_key")
            if state == "bounded_verified":
                if not isinstance(event_key, str) or not event_key.strip() or event_key in seen_events:
                    raise ValueError("Accepted USA event requires a unique named source event key")
                if audit != "independent_reviewed":
                    raise ValueError("USA course admission must be independently reviewed")
                seen_events.add(event_key)
            elif event_key:
                raise ValueError("Unverified USA slot cannot claim event identity")
        classified[state] = classified.get(state, 0) + 1
    if sum(group_units.values()) != 4500:
        raise ValueError("Wrong overall weight")
    for group, units in group_units.items():
        if inventory.get("groups", {}).get(group, {}).get("weight_units") != units:
            raise ValueError("Group total drift: " + group)
    gates = ledger.get("gates")
    if not isinstance(gates, list) or len(gates) != 12:
        raise ValueError("12 authoritative Windows release gates required")
    if {x.get("id") for x in gates} != {f"QA-{i:02d}" for i in range(1, 13)}:
        raise ValueError("Duplicate or invalid QA gate ID")
    qa01 = next(x for x in gates if x["id"] == "QA-01")
    coverage = qa01.get("coverage", {})
    count = coverage.get("complete_event_passes")
    if type(count) is not int or not 0 <= count <= 45:
        raise ValueError("No authoritative USA event count")
    if len(seen_events) != count:
        raise ValueError("USA inventory events must exactly match independent QA-01 count")
    passed = sum(g.get("status") == "passed" for g in gates)
    return {
        "inventory_version":inventory["version"],
        "inventory_source_sha":inventory["source_sha"],
        "total_criteria":135, "weight_units_total":4500,
        "bounded_product_coverage_percent":round(scored * 100 / 4500, 3),
        "independently_audited_coverage_percent":round(audited * 100 / 4500, 3),
        "evidence_status_counts":classified,
        "independent_USA_complete_events":count,
        "independent_USA_total_events":45,
        "formal_windows_gates_passed":passed, "formal_windows_gates_total":12,
        "unsatisfied_items_by_group":{g:sum(c["area"] == g and c["status"] != "bounded_verified" for c in rows) for g in GROUP_COUNTS},
        "status":"v2 candidate screening; independent audit not finished; old 48.5% maturity baseline not comparable"
    }

def report(d):
    lines = ["# Windows beta v2 | atomic progress",
             "", f"Candidate bounded product coverage: **{d['bounded_product_coverage_percent']:.3f}%**",
             f"Independently audited criterion coverage: **{d['independently_audited_coverage_percent']:.3f}%**",
             f"Accepted full USA events: **{d['independent_USA_complete_events']}/45**",
             f"Accepted Windows release gates: **{d['formal_windows_gates_passed']}/12**",
             "", "Unmet atomic requirements by category:"]
    for k, v in d["unsatisfied_items_by_group"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "Caution: v2 is a candidate binary-evidence scale, not equivalent to v1's 48.5%",
              "maturity estimate or formal sign-off. PR-screened evidence can be overturned by review."]
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory", type=Path, default=INV_PATH)
    p.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    p.add_argument("--format", choices=["json","markdown"], default="markdown")
    a = p.parse_args()
    value = validate(json.loads(a.inventory.read_text(encoding="utf-8")),
                     json.loads(a.ledger.read_text(encoding="utf-8")))
    print(json.dumps(value, indent=2) if a.format == "json" else report(value))

if __name__ == "__main__":
    main()
