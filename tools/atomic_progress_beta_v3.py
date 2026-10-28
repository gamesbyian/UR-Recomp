#!/usr/bin/env python3
"""Read-only source-pinned playable Windows beta v3 projection of frozen v2.

The only excluded criterion is legacy QA-09, a final all-release-gates
signoff. This is a different denominator, NOT additional engineering progress.
No source, inventory, authority, release ledger or review history is mutated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from . import atomic_progress_v2 as v2
except ImportError:
    import atomic_progress_v2 as v2


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "docs/progress/windows-beta-v3-scope.json"
POINTER = ROOT / "docs/progress/current-v2-review.json"
EXCLUDED = ("QA-09",)
PROJECTED_FINGERPRINT = "c231f49c"
TOTAL_UNITS = 4455
EXPECTED_KEYS = frozenset({
    "schema", "version", "base_inventory", "base_inventory_schema",
    "base_inventory_fingerprint", "review_pointer",
    "source_snapshot_policy", "included_criterion_count", "excluded_criteria",
    "excluded_criteria_policy", "projected_fingerprint",
    "fixed_denominator_units", "independent_review_policy",
    "release_quality_policy", "caution",
})


def require(condition: bool, reason: str):
    if not condition:
        raise ValueError("INVALID_BETA_V3: " + reason)


def validate_scope(scope: dict, criteria: list[dict]) -> list[dict]:
    require(type(scope) is dict and set(scope) == EXPECTED_KEYS,
            "invalid versioned beta scope")
    require(scope["schema"] == "ur-beta-scope/3"
            and scope["version"] == "windows-playable-beta-v3",
            "unrecognized beta version")
    require(scope["base_inventory"] == "docs/progress/windows-beta-v2-inventory.json"
            and scope["base_inventory_schema"] == "ur-atomic-progress/2"
            and scope["base_inventory_fingerprint"] == v2.CONTRACT_FINGERPRINT
            and scope["review_pointer"] == "docs/progress/current-v2-review.json",
            "not the frozen source-reviewed v2 baseline")
    require(scope["included_criterion_count"] == 134
            and type(scope["fixed_denominator_units"]) is int
            and scope["fixed_denominator_units"] == TOTAL_UNITS,
            "beta denominator or population changed")
    require(type(scope["excluded_criteria"]) is list
            and len(scope["excluded_criteria"]) == 1
            and scope["excluded_criteria"][0] == {
                "id": "QA-09",
                "legacy_criterion": "Independent QA signs all mandatory release gates against candidate",
                "weight_units": 45,
                "reason": ("Mandatory all-release-gate signoff belongs to the separately "
                           "qualified release-quality milestone, not playable Windows beta."),
            }, "only QA-09 may leave this beta denominator")
    require(scope["excluded_criteria_policy"] ==
            "exact_QA-09_only; retain all individual physical beta QA-02_through_QA-08_and_QA-10; retain all 45 original_native USA event slots",
            "physical beta or USA content bypass attempted")
    require(scope["source_snapshot_policy"] ==
            "read_only_projection_of_latest_independently_reviewed_v2_inventory_not_live_main",
            "must remain explicitly source-bound")
    require(scope["independent_review_policy"] ==
            "Preserve each v2 recorded status/audit receipt and exact USA event to release ledger cross-check; no new admissions or mechanical promotions",
            "independent review contract changed")
    require(scope["release_quality_policy"] ==
            "Three dissimilar Windows setups including two physical PCs and final QA-09 signoff remain independent release milestones and never beta-only shortcuts.",
            "release-quality milestone suppressed")
    require(type(scope["caution"]) is str and "DIFFERENT denominators" in scope["caution"],
            "missing score reconciliation disclaimer")
    rows = [c for c in criteria if c["id"] not in EXCLUDED]
    require(len(rows) == 134
            and sum(c["weight_units"] for c in rows) == TOTAL_UNITS,
            "projection cardinality/weights changed")
    require(scope["projected_fingerprint"] == PROJECTED_FINGERPRINT
            and v2._fingerprint(rows) == PROJECTED_FINGERPRINT,
            "projection scope IDs/descriptions/weights have changed")
    require(sum(c["area"] == "FID" for c in rows) == 45
            and all(x in {c["id"] for c in rows}
                    for x in ("QA-01", "QA-02", "QA-03", "QA-04",
                              "QA-05", "QA-06", "QA-07", "QA-08", "QA-10",
                              "WIDE-03", "WIDE-06", "RECOVERY-09", "UX-04")),
            "beta physical or original/native criteria were dropped")
    return rows


def score(scope: dict, inventory: dict, ledger: dict, pointer: dict):
    # Validate ALL frozen v2 criteria, 45 USA event slots and sole QA authority
    # *before* applying the single explicit release-signoff-only exclusion.
    historic = v2.validate(inventory, ledger)
    require(type(pointer) is dict and pointer.get("schema") == "ur-v2-review-pointer/1",
            "missing source review pointer")
    require(pointer.get("reviewed_main_sha") == inventory.get("source_sha"),
            "v2 inventory and reviewed main source do not match")
    require(type(pointer.get("previous")) is str
            and pointer["previous"].startswith("docs/progress/v2-review-")
            and type(pointer.get("interval")) is str
            and pointer["interval"].startswith("docs/progress/v2-review-"),
            "missing source-bound historical review interval")
    rows = validate_scope(scope, inventory["criteria"])
    completed = sum(c["weight_units"] for c in rows
                    if c["status"] == "bounded_verified")
    audited = sum(c["weight_units"] for c in rows
                  if c["audit_state"] == "independent_reviewed")
    release_qa09 = next(c for c in inventory["criteria"] if c["id"] == "QA-09")
    release_qa04 = next(g for g in ledger["gates"] if g["id"] == "QA-04")
    group = {
        g: {
            "total": sum(c["id"].startswith(g + "-") for c in rows),
            "verified": sum(c["id"].startswith(g + "-")
                            and c["status"] == "bounded_verified" for c in rows),
            "independently_reviewed": sum(c["id"].startswith(g + "-")
                                          and c["audit_state"] == "independent_reviewed"
                                          for c in rows),
        }
        for g in v2.GROUP_COUNTS
    }
    return {
        "schema": "ur-playable-windows-beta-progress/3",
        "version": scope["version"],
        "source_reviewed_sha": inventory["source_sha"],
        "historical_v2_snapshot": {
            "criteria": historic["total_criteria"],
            "denominator_units": historic["weight_units_total"],
            "bounded_percent": historic["bounded_product_coverage_percent"],
            "independently_audited_percent": historic["independently_audited_coverage_percent"],
        },
        "beta": {
            "criteria": len(rows),
            "denominator_units": TOTAL_UNITS,
            "bounded_verified_units": completed,
            "independently_audited_units": audited,
            "bounded_percent": round(100 * completed / TOTAL_UNITS, 3),
            "independently_audited_percent": round(100 * audited / TOTAL_UNITS, 3),
            "excluded_release_only": list(EXCLUDED),
            "by_group": group,
        },
        "release_quality_separate": {
            "legacy_qa09_status": release_qa09["status"],
            "release_qa04_three_environment_gate_status": release_qa04["status"],
            "formal_release_gates_passed": historic["formal_windows_gates_passed"],
            "formal_release_gates_total": historic["formal_windows_gates_total"],
            "individual_beta_physical_criteria_still_required": True,
            "three_environments_including_two_physical_pcs_still_release_required": True,
        },
        "original_native_events": {
            "accepted": historic["independent_USA_complete_events"],
            "required": historic["independent_USA_total_events"],
        },
        "new_engineering_work_claimed": False,
        "newly_admitted_criteria_claimed": 0,
        "denominator_reclassification_only": True,
        "source_snapshot_not_current_main_attestation": True,
        "caution": ("V3 differs from V2 solely because QA-09 final-release "
                    "signoff is excluded. Comparing percentages is NOT "
                    "measured engineering progress. Beta state is a "
                    "source-reviewed snapshot, not a live-main assertion."),
    }


def markdown(view):
    old = view["historical_v2_snapshot"]
    beta = view["beta"]
    release = view["release_quality_separate"]
    lines = [
        "# Playable Windows beta v3 | historical source-reviewed projection",
        "",
        "Reviewed source: `" + view["source_reviewed_sha"] + "`",
        "",
        f"**Beta bounded: {beta['bounded_percent']:.3f}%** "
        f"({beta['bounded_verified_units']}/{beta['denominator_units']} evidence units)",
        f"**Beta independently audited: {beta['independently_audited_percent']:.3f}%** "
        f"({beta['independently_audited_units']}/{beta['denominator_units']} evidence units)",
        "",
        f"Frozen v2 (different denominator): **{old['bounded_percent']:.3f}%** "
        f"of {old['denominator_units']} units / {old['criteria']} criteria.",
        "**Excluded from beta only:** QA-09, final all-release-gates signoff.",
        "",
        "| Area | Beta verified / total | Independently reviewed |",
        "|---|---:|---:|",
    ]
    for group, counts in beta["by_group"].items():
        lines.append(f"| {group} | {counts['verified']}/{counts['total']} "
                     f"| {counts['independently_reviewed']}/{counts['total']} |")
    lines += [
        "",
        f"Independent original/native events: **{view['original_native_events']['accepted']}/45**",
        f"Formal release gates: **{release['formal_release_gates_passed']}/12**",
        "Separate three-machine release gate QA-04: **"
        + str(release["release_qa04_three_environment_gate_status"]) + "**",
        "Individual real-hardware beta requirements remain in the denominator.",
        "",
        "**No new engineering points or new acceptance credited by this projection.**",
        view["caution"],
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope", type=Path, default=SCOPE)
    p.add_argument("--inventory", type=Path, default=v2.INV_PATH)
    p.add_argument("--ledger", type=Path, default=v2.LEDGER_PATH)
    p.add_argument("--review-pointer", type=Path, default=POINTER)
    p.add_argument("--reviewed-head", help="Optional exact source SHA, rejects stale reviewed inventories")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = p.parse_args()
    inv = json.loads(args.inventory.read_text(encoding="utf-8"))
    if args.reviewed_head:
        v2.require_reviewed_head(inv, args.reviewed_head)
    result = score(
        json.loads(args.scope.read_text(encoding="utf-8")),
        inv, json.loads(args.ledger.read_text(encoding="utf-8")),
        json.loads(args.review_pointer.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, sort_keys=True, indent=2) if args.format == "json"
          else markdown(result))


if __name__ == "__main__":
    main()
