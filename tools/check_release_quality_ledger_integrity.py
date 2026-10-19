#!/usr/bin/env python3
"""Release-authority structural audit; never awards event/hardware gate credit.

Treats docs/RELEASE-QUALITY-LEDGER.json as the sole admission authority.
Prevents silent promotion from source log text, synthetic tests, fixture
receipts, a stale product-PR head or mere reported ZIP hashes.
A legitimate future accepted original/native witness must update the
explicit gate, source pin and coverage together.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from validate_release_quality_ledger import qa04_physical_coverage

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs/RELEASE-QUALITY-LEDGER.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
GATE_IDS = tuple(f"QA-{i:02d}" for i in range(1, 13))
LAYER = frozenset(("L4", "L5"))
ACCEPTED_GATE = frozenset(("passed", "failed", "waived"))
RELEASE_POSITIVE = frozenset(("ready", "passed", "approved", "release_approved"))
RELEASE_NEGATIVE = frozenset(("not_assessed", "not_ready", "blocked", "failed", "deferred"))


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("release ledger integrity: " + msg)


def full_hex(value: object, matcher: re.Pattern) -> bool:
    return type(value) is str and matcher.fullmatch(value) is not None


def audit(ledger: dict) -> dict[str, object]:
    require(type(ledger) is dict and
            ledger.get("schema") == "UR-RELEASE-QUALITY-LEDGER/1",
            "wrong ledger schema")
    definitions = ledger.get("status_definitions")
    require(type(definitions) is dict and
            {"unverified", "in_progress", "passed", "failed",
             "blocked", "waived"} <= set(definitions) and
            all(type(v) is str and bool(v.strip())
                for v in definitions.values()),
            "no explicit gate status semantics")
    gates = ledger.get("gates")
    require(type(gates) is list and len(gates) == len(GATE_IDS)
            and [g.get("id") if type(g) is dict else None
                 for g in gates] == list(GATE_IDS),
            "missing, duplicated or reordered release QA gate")
    candidate = ledger.get("candidate")
    require(type(candidate) is dict, "missing exact release candidate")
    src, zip_digest = candidate.get("commit_sha"), candidate.get("zip_sha256")
    require((src is None and zip_digest is None) or
            (full_hex(src, HEX40) and full_hex(zip_digest, HEX64)),
            "release candidate must be fully pinned by BOTH source and inner ZIP")
    pinned = src is not None
    require(type(candidate.get("physical_hardware_verified")) is bool,
            "physical release hardware status must be boolean")
    decision = candidate.get("release_decision")
    require(type(decision) is str and
            decision in RELEASE_POSITIVE | RELEASE_NEGATIVE,
            "unknown release decision, review required")
    requires_hardware = False
    passed = []
    waived = []
    pending = []
    for gate in gates:
        id = gate["id"]
        status = gate.get("status")
        require(type(status) is str and status in definitions,
                id + " has unknown gate status")
        require(type(gate.get("required_layer")) is str and
                gate["required_layer"] in LAYER,
                id + " lacks L4/L5 layer")
        require(type(gate.get("evidence_refs")) is list and
                all(type(x) is str and bool(x.strip())
                    for x in gate["evidence_refs"]),
                id + " evidence references missing or malformed")
        require(type(gate.get("witnesses")) is list,
                id + " witnesses must be an explicit list")
        require(type(gate.get("next_action")) is str,
                id + " missing adjudication/next action")
        claim_commit = gate.get("candidate_commit")
        require(claim_commit is None or full_hex(claim_commit, HEX40),
                id + " source revision malformed")
        if status in ("passed", "failed"):
            require(pinned and claim_commit == src and
                    len(gate["witnesses"]) > 0,
                    id + " claims exact acceptance/failure without "
                    "pinned candidate and independent witnesses")
            require(gate.get("waiver_reason") is None,
                    id + " accepted/failure gate carries waiver")
        if status == "waived":
            reason = gate.get("waiver_reason")
            require(type(reason) is str and len(reason.strip()) >= 20,
                    id + " waiver lacks documented substantive rationale")
            waived.append(id)
        else:
            require(gate.get("waiver_reason") is None,
                    id + " nonwaived gate retains contradictory waiver")
        if status == "passed":
            if id == "QA-04":
                require(qa04_physical_coverage(gate["witnesses"]),
                        "QA-04 cannot accept fewer than three dissimilar "
                        "L5 candidate-bound physical/clean-machine witnesses")
            passed.append(id)
            requires_hardware |= gate["required_layer"] == "L5"
        elif status != "waived":
            pending.append(id)
    usa_gate = gates[0]
    coverage = usa_gate.get("coverage")
    require(type(coverage) is dict, "QA-01 authoritative USA coverage absent")
    usa_fields = ("denominator", "complete_event_passes", "partial", "unverified")
    require(all(type(coverage.get(f)) is int and coverage[f] >= 0
                for f in usa_fields), "USA coverage integer counts malformed")
    require(coverage["denominator"] == 45 and
            coverage["complete_event_passes"] + coverage["partial"]
            + coverage["unverified"] == 45,
            "original USA course census is not precisely 45")
    region_fields = ("regional_comparison_denominator",
                     "regional_comparison_complete",
                     "regional_comparison_unverified",
                     "total_tracked_course_rom_pairs")
    require(all(type(coverage.get(f)) is int and coverage[f] >= 0
                for f in region_fields) and
            coverage["regional_comparison_denominator"] == 90 and
            coverage["regional_comparison_complete"]
            + coverage["regional_comparison_unverified"] == 90 and
            coverage["total_tracked_course_rom_pairs"] == 135,
            "PAL/prototype comparative census changed without review")
    full_events = coverage["complete_event_passes"]
    require(full_events == 0 or
            (usa_gate["witnesses"] and len(usa_gate["evidence_refs"]) > 0),
            "USA completed course count promoted without independent oracle witness")
    if usa_gate["status"] == "passed":
        require(full_events == 45,
                "QA-01 whole USA course gate passed with unfinished events")
    require(type(gates[6].get("coverage")) is dict and
            type(gates[6]["coverage"].get("complete_expert_event_passes")) is int
            and gates[6]["coverage"]["complete_expert_event_passes"] >= 0,
            "QA-07 complete expert event scope malformed")
    ready = decision in RELEASE_POSITIVE
    if ready:
        require(pinned and not pending and
                candidate["physical_hardware_verified"] and
                all(g["candidate_commit"] in (src, None)
                    for g in gates),
                "release decision claims ready with pending gates, "
                "unpinned ZIP or unverified hardware")
    if requires_hardware:
        require(candidate["physical_hardware_verified"],
                "L5 gate passed without physical release-hardware acceptance")
    return {
        "schema": "UR-RELEASE-LEDGER-STRUCTURAL-DISPOSITION/1",
        "candidate_fully_pinned": pinned,
        "source_commit": src,
        "inner_zip_sha256": zip_digest,
        "physical_hardware_verified": candidate["physical_hardware_verified"],
        "approved_gate_count": len(passed),
        "explicit_waiver_count": len(waived),
        "pending_or_failed_gate_count": len(pending),
        "original_USA_complete_event_passes": full_events,
        "original_USA_total": 45,
        "candidate_release_decision": decision,
        "release_decision_structurally_admissible": ready,
        "independently_executed_original_emulator_here": False,
        "physical_windows_executed_here": False,
        "outcome": "consistent_gate_structure_only_not_new_release_evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.ledger.read_text(encoding="utf-8")))
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        # Never silently overwrite a previously adjudicated immutable receipt.
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
