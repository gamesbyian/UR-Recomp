#!/usr/bin/env python3
"""Fail-closed, read-only QA-01 primary-artifact receipt audit.

Reopen the exact per-case producer JSON, recompute the *existing* campaign
classification and compare every field to the published case and aggregate.
This verifies transport integrity, not original execution or L4 admission.
No ROM, native binary, WRAM dump, or release ledger is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import qa01_event_campaign as campaign

SCHEMA = "ur-qa01-event-primary-artifact-audit/1"


def _failure(case: str, reason: str) -> dict:
    return {"case": case, "status": "invalid", "reason": reason}


def validate_capture_population(report: dict) -> None:
    """Inspect actual published observation rows, not their derived booleans.

    Only completeness and the earliest *sampled* field difference are
    re-evaluated here. Sparse frames do not prove unsampled execution.
    """
    offsets = report.get("relative_sample_frames")
    if (not isinstance(offsets, list) or len(offsets) < 8
            or any(type(f) is not int or f < 0 for f in offsets)
            or offsets != sorted(set(offsets)) or offsets[0] != 0):
        raise ValueError("missing, unordered, duplicate or invalid sampled frame population")
    sides = []
    for guest in ("reference", "native"):
        capture = report.get(guest)
        if not isinstance(capture, dict):
            raise ValueError("missing original/native raw capture: " + guest)
        samples = capture.get("samples")
        if (not isinstance(samples, list) or len(samples) != len(offsets)
                or any(not isinstance(row, dict) for row in samples)
                or [row.get("relative_frame") for row in samples] != offsets):
            raise ValueError("missing or misregistered original/native sample frames: " + guest)
        for phase in ("onset", "result"):
            state = capture.get(phase)
            if (not isinstance(state, dict) or
                    type(state.get("menu")) is not int or
                    type(state.get("in_race")) is not int):
                raise ValueError("missing observed guest terminal state: " + guest + "/" + phase)
        texts = capture.get("result_text")
        if (not isinstance(texts, dict)
                or not isinstance(texts.get("final"), list)
                or any(not isinstance(line, str) for line in texts["final"])):
            raise ValueError("missing guest decoded source PPU result text: " + guest)
        sides.append(samples)
    first = None
    for original, native in zip(*sides):
        if set(original) != set(native):
            raise ValueError("missing named original/native sample fields")
        unequal = sorted(k for k in original if original[k] != native[k])
        if unequal:
            first = {
                "relative_frame": original["relative_frame"],
                "fields": unequal,
                "reference": {k: original[k] for k in unequal},
                "native": {k: native[k] for k in unequal},
            }
            break
    comparison = report.get("comparison")
    if not isinstance(comparison, dict) or comparison.get("first_sample_disagreement") != first:
        raise ValueError("published first sampled divergence differs from raw captures")
    baseline = report.get("original_source_vs_fresh_entry")
    if (not isinstance(baseline, dict)
            or any(type(baseline.get(key)) is not bool for key in (
                "fresh_reference_native_equivalent", "source_original_state_equivalent"))
            or comparison.get("fresh_guest_entry_equivalent") is not
                baseline["fresh_reference_native_equivalent"]
            or comparison.get("original_source_entry_equivalent") is not
                baseline["source_original_state_equivalent"]):
        raise ValueError("fresh entry equivalence contradicts source observations")


def audit(plan: dict, results_dir: Path, aggregate_report: dict | None = None) -> dict:
    """Verify all selected primary reports, including source and case identity.

    A self-consistent case-result.json alone is not evidence. Even a fully
    verified result below has zero event admission and requires independent
    source execution, temporal and persistence review.
    """
    campaign.validate_plan(plan)
    selected = [row["id"] for row in plan["cases"]]
    selected_set = set(selected)
    unexpected = sorted(
        p.name for p in results_dir.glob("qa01-campaign-case-*")
        if p.is_dir() and p.name.removeprefix("qa01-campaign-case-") not in selected_set
    )
    cases = []
    for case in selected:
        directory = results_dir / ("qa01-campaign-case-" + case)
        receipt = directory / "case-result.json"
        primary = directory / "producer-report.json"
        try:
            if not receipt.is_file() or not primary.is_file():
                raise ValueError("missing original case-result.json or producer-report.json")
            if receipt.is_symlink() or primary.is_symlink():
                raise ValueError("symlinked primary artifact is not admissible")
            row = campaign.load_json(receipt)
            if type(row.get("producer_exit_code")) is not int or row["producer_exit_code"] not in (0, 1):
                raise ValueError("missing real completed producer exit code 0/1")
            if row.get("disposition") not in ("strict_candidate", "strict_divergence"):
                raise ValueError("producer-error/missing case is not a completed primary witness")
            evidence = row.get("evidence")
            if not isinstance(evidence, dict):
                raise ValueError("missing case evidence")
            sha = hashlib.sha256(primary.read_bytes()).hexdigest()
            if evidence.get("producer_sha256") != sha:
                raise ValueError("primary producer report SHA-256 differs from case receipt")
            validate_capture_population(campaign.load_json(primary))
            independently_derived = campaign.classify(
                case, row["producer_exit_code"], primary, plan
            )
            if independently_derived != row:
                raise ValueError("case receipt differs from actual producer's recomputed classification")
            cases.append({
                "case": case, "status": "verified_transport_only",
                "disposition": row["disposition"],
                "producer_sha256": sha, "release_credit": 0,
            })
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            cases.append(_failure(case, str(exc)))
    complete = not unexpected and all(
        row["status"] == "verified_transport_only" for row in cases
    )
    aggregate_matches = None
    if aggregate_report is not None:
        try:
            expected, _ = campaign.aggregate(plan, results_dir)
            aggregate_matches = expected == aggregate_report
        except (OSError, ValueError, KeyError, TypeError):
            aggregate_matches = False
        complete = complete and aggregate_matches is True
    return {
        "schema": SCHEMA,
        "source_sha": plan["source_sha"],
        "plan_sha256": plan["plan_sha256"],
        "selected_cases": len(selected),
        "primary_receipts_verified": sum(
            row["status"] == "verified_transport_only" for row in cases
        ),
        "unexpected_case_directories": unexpected,
        "campaign_aggregate_matches_sources": aggregate_matches,
        "primary_artifact_audit_complete": complete,
        "release_admissions": 0,
        "scope": "receipt/transport consistency only; no independent guest execution or USA event admission",
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--results-dir", type=Path, required=True)
    p.add_argument("--campaign-result", type=Path,
                   help="also reconstruct and compare the published aggregate")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--summary", type=Path)
    args = p.parse_args(argv)
    try:
        plan = campaign.load_json(args.plan)
        published = (campaign.load_json(args.campaign_result)
                     if args.campaign_result else None)
        report = audit(plan, args.results_dir, published)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report = {
            "schema": SCHEMA, "primary_artifact_audit_complete": False,
            "release_admissions": 0, "error": str(exc), "cases": [],
        }
    campaign.write_json(args.out, report)
    lines = [
        "### QA-01 primary source-receipt integrity",
        "",
        "Primary reports independently re-read: "
        + str(report.get("primary_receipts_verified", 0))
        + "/" + str(report.get("selected_cases", 0)),
        "Verified transport only: " + str(report["primary_artifact_audit_complete"]),
        "USA complete-event admissions: **0** (not adjudicated).",
    ]
    for case in report.get("cases", []):
        if case["status"] == "invalid":
            lines.append("- " + case["case"] + ": INVALID, " + case["reason"])
    if report.get("unexpected_case_directories"):
        lines.append("- Unexpected case directories: " +
                     ", ".join(report["unexpected_case_directories"]))
    if report.get("campaign_aggregate_matches_sources") is False:
        lines.append("- Published aggregate contradicts actual case receipts")
    if report.get("error"):
        lines.append("- Audit could not begin: " + report["error"])
    rendered = "\n".join(lines) + "\n"
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open("a", encoding="utf-8") as stream:
            stream.write("\n" + rendered)
    print(rendered, end="")
    return 0 if report["primary_artifact_audit_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
