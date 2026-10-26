#!/usr/bin/env python3
"""Read-only release gate handoff. References are pointers, never accepted proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "docs/RELEASE-QUALITY-LEDGER.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
STATUSES = {"unverified", "in_progress", "passed", "failed", "blocked", "waived"}


def briefing(ledger: dict, *, source_sha: str | None = None) -> dict:
    if not isinstance(ledger, dict) or ledger.get("schema") != "UR-RELEASE-QUALITY-LEDGER/1":
        raise ValueError("unsupported release ledger")
    if source_sha is not None and not HEX40.fullmatch(source_sha):
        raise ValueError("source SHA must be an exact lowercase commit")
    candidate = ledger.get("candidate")
    gates = ledger.get("gates")
    if not isinstance(candidate, dict) or not isinstance(gates, list):
        raise ValueError("missing candidate or gate inventory")
    pinned = candidate.get("commit_sha")
    digest = candidate.get("zip_sha256")
    if not (isinstance(pinned, str) and HEX40.fullmatch(pinned) and
            isinstance(digest, str) and HEX64.fullmatch(digest)):
        raise ValueError("candidate must be pinned by source and ZIP")
    if len(gates) != 12 or [g.get("id") for g in gates if isinstance(g, dict)] != [
            f"QA-{i:02d}" for i in range(1, 13)]:
        raise ValueError("incomplete or reordered gate inventory")
    rows = []
    for gate in gates:
        status = gate.get("status")
        if status not in STATUSES or gate.get("required_layer") not in ("L4", "L5"):
            raise ValueError("invalid gate status or evidence layer")
        refs = gate.get("evidence_refs")
        witnesses = gate.get("witnesses")
        action = gate.get("next_action")
        if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
            raise ValueError("malformed evidence references")
        if not isinstance(witnesses, list) or not isinstance(action, str):
            raise ValueError("malformed witness inventory or next action")
        claimed = gate.get("candidate_commit")
        if claimed is not None and (not isinstance(claimed, str) or not HEX40.fullmatch(claimed)):
            raise ValueError("malformed gate candidate commit")
        blockers = []
        if status not in ("passed", "waived"):
            blockers.append("gate_not_accepted")
        if not witnesses:
            blockers.append("no_registered_independent_witness")
        if claimed is not None and claimed != pinned:
            blockers.append("gate_candidate_mismatch")
        if source_sha is None:
            blockers.append("requested_source_not_checked")
        elif source_sha != pinned:
            blockers.append("requested_source_differs_from_nominated_candidate")
        rows.append({
            "id": gate["id"], "status": status, "required_layer": gate["required_layer"],
            "reference_count": len(refs), "witness_count": len(witnesses),
            "candidate_commit": claimed, "blockers": blockers,
            "next_action": " ".join(action.split())[:240],
        })
    return {
        "schema": "UR-RELEASE-READONLY-BRIEF/1",
        "authority": "diagnostic_only_no_acceptance_promotion",
        "ledger_candidate_commit": pinned,
        "ledger_zip_sha256": digest,
        "checked_source_commit": source_sha,
        "source_matches_ledger": None if source_sha is None else source_sha == pinned,
        "accepted_gate_count": sum(r["status"] == "passed" for r in rows),
        "pending_gate_count": sum(r["status"] not in ("passed", "waived") for r in rows),
        "gates": rows,
    }


def markdown(result: dict) -> str:
    match_state = result["source_matches_ledger"]
    source_comparison = (
        "UNKNOWN (no checked source supplied)" if match_state is None
        else "MATCH" if match_state else "MISMATCH"
    )
    lines = [
        "# Release evidence handoff (read-only)",
        "",
        "Diagnostic inventory only. **References, completed tests and witness counts do not award release credit.**",
        f"Ledger candidate: `{result['ledger_candidate_commit']}`; ZIP SHA256: `{result['ledger_zip_sha256']}`.",
        f"Gate status: {result['accepted_gate_count']}/12 accepted; {result['pending_gate_count']} pending (excluding explicit waivers).",
        f"Source comparison: {source_comparison}.",
        "",
        "| Gate | Status | Layer | References | Witnesses | Blockers |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in result["gates"]:
        lines.append(f"| {row['id']} | {row['status']} | {row['required_layer']} | "
                     f"{row['reference_count']} | {row['witness_count']} | "
                     f"{', '.join(row['blockers']) or 'none recorded'} |")
    lines.extend(["", "## Next actions (ledger excerpts)", ""])
    for row in result["gates"]:
        lines.append(f"- **{row['id']}**: {row['next_action']}")
    lines.extend(["", "Cross-check authoritative ledger and independent evidence before any adjudication.",
                  "No tests, GitHub API calls, hardware checks or evidence authentication were performed."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT)
    parser.add_argument("--source-sha")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    raw = args.ledger.read_bytes()
    result = briefing(json.loads(raw), source_sha=args.source_sha)
    result["ledger_file_sha256"] = hashlib.sha256(raw).hexdigest()
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
