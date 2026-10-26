#!/usr/bin/env python3
"""Compare two immutable release briefings; diagnostics never award evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "UR-RELEASE-READONLY-BRIEF/1"
DELTA_SCHEMA = "UR-RELEASE-INVENTORY-DELTA/1"
FIELDS = (
    "status", "required_layer", "reference_count", "witness_count",
    "candidate_commit", "blockers", "next_action",
)
META_FIELDS = (
    "ledger_file_sha256", "ledger_candidate_commit",
    "ledger_zip_sha256", "checked_source_commit",
)
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
STATUSES = {"unverified", "in_progress", "passed", "failed", "blocked", "waived"}


def _validate(packet: dict) -> None:
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("unsupported release briefing schema")
    if packet.get("authority") != "diagnostic_only_no_acceptance_promotion":
        raise ValueError("untrusted release briefing authority")
    for key in ("ledger_file_sha256", "ledger_zip_sha256"):
        val = packet.get(key)
        if not isinstance(val, str) or not HEX64.fullmatch(val):
            raise ValueError("missing exact fingerprint: " + key)
    val = packet.get("ledger_candidate_commit")
    if not isinstance(val, str) or not HEX40.fullmatch(val):
        raise ValueError("invalid nominated source")
    source = packet.get("checked_source_commit")
    if source is not None and (not isinstance(source, str) or not HEX40.fullmatch(source)):
        raise ValueError("invalid checked source")
    expected_match = None if source is None else source == val
    if packet.get("source_matches_ledger") is not expected_match:
        raise ValueError("source comparison conflicts with exact source pins")
    gates = packet.get("gates")
    if not isinstance(gates, list) or len(gates) != 12:
        raise ValueError("incomplete release gate inventory")
    if [g.get("id") for g in gates if isinstance(g, dict)] != [
        "QA-%02d" % n for n in range(1, 13)
    ]:
        raise ValueError("noncanonical release gate IDs")
    for gate in gates:
        if gate.get("status") not in STATUSES or gate.get("required_layer") not in ("L4", "L5"):
            raise ValueError("invalid release gate metadata")
        if any(type(gate.get(k)) is not int or gate[k] < 0
               for k in ("reference_count", "witness_count")):
            raise ValueError("invalid reference or witness count")
        if (not isinstance(gate.get("blockers"), list)
                or not all(isinstance(x, str) for x in gate["blockers"])):
            raise ValueError("invalid blockers")
        if not isinstance(gate.get("next_action"), str):
            raise ValueError("missing next action")
        claimed = gate.get("candidate_commit")
        if claimed is not None and (not isinstance(claimed, str) or not HEX40.fullmatch(claimed)):
            raise ValueError("invalid gate source")


def compare(before: dict, after: dict) -> dict:
    """Show tracked changes, without asserting that refs or witnesses are valid."""
    _validate(before)
    _validate(after)
    metadata_changes = {
        key: {"before": before[key], "after": after[key]}
        for key in META_FIELDS if before[key] != after[key]
    }
    gate_changes = []
    for old, new in zip(before["gates"], after["gates"]):
        changes = {
            key: {"before": old[key], "after": new[key]}
            for key in FIELDS if old[key] != new[key]
        }
        if changes:
            gate_changes.append({"id": old["id"], "changes": changes})
    fingerprint_changed = (
        before["ledger_file_sha256"] != after["ledger_file_sha256"]
    )
    return {
        "schema": DELTA_SCHEMA,
        "authority": "diagnostic_only_no_evidence_or_acceptance_promotion",
        "before_source": before["checked_source_commit"],
        "after_source": after["checked_source_commit"],
        "same_ledger_bytes": not fingerprint_changed,
        "changed_gate_count": len(gate_changes),
        "unexplained_ledger_byte_change": fingerprint_changed
            and not any("ledger_candidate_commit" == x or "ledger_zip_sha256" == x
                        for x in metadata_changes)
            and not gate_changes,
        "metadata_changes": metadata_changes,
        "gate_changes": gate_changes,
        "limits": [
            "Only metadata recorded in saved read-only briefings is compared.",
            "Equal reference/witness counts cannot prove identical reference identities or contents.",
            "No original/native replay, build, runtime, hardware, witness authentication, or gate acceptance is performed.",
        ],
    }


def markdown(result: dict) -> str:
    lines = [
        "# Release briefing metadata delta (diagnostic only)", "",
        "No release credit is granted, even when a recorded ledger status changes.",
        "Before checked source: " + str(result["before_source"]),
        "After checked source: " + str(result["after_source"]),
        "Same exact ledger bytes: " + str(result["same_ledger_bytes"]),
        "Gates with tracked metadata changes: " + str(result["changed_gate_count"]) + "/12",
    ]
    if result["unexplained_ledger_byte_change"]:
        lines.append("WARNING: Ledger bytes changed without a tracked field difference; inspect original ledgers.")
    lines += ["", "## Changed header fields"]
    if not result["metadata_changes"]:
        lines.append("None")
    for key, change in result["metadata_changes"].items():
        lines.append("- " + key + ": " + json.dumps(change, sort_keys=True))
    lines += ["", "## Changed gate fields"]
    if not result["gate_changes"]:
        lines.append("None")
    for row in result["gate_changes"]:
        lines.append("- " + row["id"] + ": " + ", ".join(sorted(row["changes"])))
    lines += ["", "Reference counts and witness counts are navigation metadata, not verified evidence.",
              "Compare the original ledgers, exact source, receipts and actual independent witnesses before adjudication."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))
    result = compare(before, after)
    rendered = markdown(result)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
