#!/usr/bin/env python3
"""Create a source-bound, read-only agent handoff from existing authorities.

No GitHub calls, guest execution, CI dispatch, release gate adjudication or
automatic work assignment. An explicit gate is required for a concrete next
decision; absent that, the output is navigation only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    from .build_agent_context import LANE_RELEASE_GATES
    from .release_evidence_brief import briefing
    from .release_evidence_delta import compare
except ImportError:
    from build_agent_context import LANE_RELEASE_GATES
    from release_evidence_brief import briefing
    from release_evidence_delta import compare

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "UR-AGENT-ACTION-HANDOFF/1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_CHANGED_PATHS = 16
MAX_COMMITS = 6
AUTHORITIES = (
    "docs/WORK-QUEUE.md",
    "docs/HOURLY-AGENT-LINES.md",
    "docs/RELEASE-QUALITY-LEDGER.json",
    "analysis/agent-context-lanes.json",
)


def run_git(*argv: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *argv], cwd=ROOT, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("local Git unavailable: " + str(exc)) from exc
    if proc.returncode:
        raise ValueError("Git command failed: " + " ".join(argv[:3]))
    return proc.stdout.strip()


def exact_checkout() -> tuple[str, str]:
    head = run_git("rev-parse", "--verify", "HEAD")
    if not HEX40.fullmatch(head):
        raise ValueError("cannot bind handoff to a full Git commit")
    dirty = run_git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise ValueError("tracked working tree is dirty: handoff would omit local changes")
    branch = run_git("branch", "--show-current")
    return head, branch or "(detached)"


def source_diff(since: str | None, head: str) -> dict[str, Any]:
    if since is None:
        return {
            "state": "baseline_not_supplied", "baseline": None,
            "changed_path_count": None, "changed_paths": [],
            "truncated": False, "recent_commits": [],
        }
    if not HEX40.fullmatch(since):
        raise ValueError("--since requires an exact lowercase 40-character commit")
    if run_git("cat-file", "-t", since) != "commit":
        raise ValueError("--since must identify a Git commit")
    run_git("merge-base", "--is-ancestor", since, head)
    paths = sorted(set(run_git(
        "diff", "--name-only", "--no-renames", since, head, "--"
    ).splitlines()) - {""})
    log = run_git("log", "--format=%h%x09%s",
                  "--max-count=" + str(MAX_COMMITS), since + ".." + head)
    return {
        "state": "complete", "baseline": since,
        "changed_path_count": len(paths),
        "changed_paths": paths[:MAX_CHANGED_PATHS],
        "truncated": len(paths) > MAX_CHANGED_PATHS,
        "recent_commits": [
            {"short_sha": part[0], "subject": part[1][:180]}
            for line in log.splitlines()
            if (part := line.split("\t", 1)) and len(part) == 2
        ],
    }


def authoritative_hashes(root: Path) -> dict[str, str]:
    results = {}
    for rel in AUTHORITIES:
        raw = (root / rel).read_bytes()
        results[rel] = hashlib.sha256(raw).hexdigest()
    return results


def build_handoff(
    lane: str, *, gate: str | None = None, since: str | None = None,
    previous_brief: dict | None = None,
) -> dict[str, Any]:
    config = json.loads((ROOT / "analysis/agent-context-lanes.json").read_text(encoding="utf-8"))
    if lane not in config.get("lanes", {}) or lane not in LANE_RELEASE_GATES:
        raise ValueError("unknown agent lane: " + lane)
    allowed = LANE_RELEASE_GATES[lane]
    if gate is not None and (
        not re.fullmatch(r"QA-(0[1-9]|1[0-2])", gate)
        or (allowed is not None and gate not in allowed)
    ):
        raise ValueError("gate not assigned to requested navigation lane")
    if previous_brief is not None and since is None:
        raise ValueError("--previous-brief requires --since")
    head, branch = exact_checkout()
    changes = source_diff(since, head)
    ledger_raw = (ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_bytes()
    view = briefing(json.loads(ledger_raw), source_sha=head)
    view["ledger_file_sha256"] = hashlib.sha256(ledger_raw).hexdigest()
    eligible = [
        row for row in view["gates"]
        if allowed is None or row["id"] in allowed
    ]
    selected = next((row for row in eligible if row["id"] == gate), None)
    if gate is not None and selected is None:
        raise ValueError("requested gate absent from release ledger")

    delta = None
    delta_state = "baseline_brief_not_supplied"
    if previous_brief is not None:
        if not isinstance(previous_brief, dict) or previous_brief.get("checked_source_commit") != since:
            raise ValueError("previous brief must match --since exact source commit")
        delta = compare(previous_brief, view)
        delta_state = "diagnostic_only"

    if selected is not None:
        # The owning board decides who performs this work. This is an
        # evidence-navigation prompt, not an independently validated plan.
        action = {
            "gate": selected["id"],
            "status": selected["status"],
            "required_layer": selected["required_layer"],
            "blockers": selected["blockers"],
            "ledger_next_action_excerpt": selected["next_action"],
            "action_source": "docs/RELEASE-QUALITY-LEDGER.json",
            "next_decision": (
                "Identify the smallest independent " + selected["required_layer"]
                + " witness that can change " + selected["id"]
                + " on one exact candidate, after reconciling live ownership."
            ),
            "stop_condition": (
                "Stop without gate credit if candidate/inputs are not identical,"
                " a required producer is missing, the witness is not independent,"
                " or the owning board has conflicting active work."
            ),
        }
    else:
        action = {
            "gate": None,
            "next_decision": (
                "Reconcile current PRs and the hourly assignment board; select"
                " one owned unaccepted gate with --gate before engineering."
            ),
            "action_source": "docs/HOURLY-AGENT-LINES.md",
            "stop_condition": "Do not infer ownership from lane names or assign work automatically.",
        }

    return {
        "schema": SCHEMA,
        "authority": "read_only_navigation_zero_release_credit",
        "checkout_commit": head,
        "checkout_branch": branch,
        "working_tree": "clean_tracked_files",
        "authority_sha256": authoritative_hashes(ROOT),
        "lane": lane,
        "lane_authorities": config["lanes"][lane]["authorities"],
        "release": {
            "ledger_file_sha256": view["ledger_file_sha256"],
            "nominated_candidate_commit": view["ledger_candidate_commit"],
            "nominated_candidate_zip_sha256": view["ledger_zip_sha256"],
            "checkout_matches_nominee": view["source_matches_ledger"],
            "accepted_gate_count_as_recorded": view["accepted_gate_count"],
            "pending_gate_count_as_recorded": view["pending_gate_count"],
            "eligible_gates": eligible,
        },
        "source_changes": changes,
        "brief_delta_state": delta_state,
        "brief_delta": delta,
        "next_step": action,
        "limits": [
            "Git differences are source changes, not test success or release evidence.",
            "Release status is copied from the ledger, not independently adjudicated.",
            "No network or live PR/CI/assignment-board verification was performed.",
            "Historical and new brief snapshots are diagnostic, not authenticated witnesses.",
            "Validate current ownership, exact source and the cheapest discriminator before work.",
        ],
    }


def markdown(data: dict[str, Any]) -> str:
    rel = data["release"]
    source = data["source_changes"]
    action = data["next_step"]
    lines = [
        "# Agent action handoff: " + data["lane"], "",
        "Diagnostic-only. This packet cannot assign work or accept a release gate.",
        "Checkout: " + data["checkout_commit"] + " (" + data["checkout_branch"] + ")",
        "Nominated source: " + rel["nominated_candidate_commit"],
        "Source match: " + ("yes" if rel["checkout_matches_nominee"] else "NO"),
        "Nominated inner ZIP: " + rel["nominated_candidate_zip_sha256"],
        "Recorded gates: " + str(rel["accepted_gate_count_as_recorded"])
        + "/12 passed, " + str(rel["pending_gate_count_as_recorded"]) + " pending.",
        "Ledger SHA256: " + rel["ledger_file_sha256"], "",
        "## Source changes", "",
    ]
    if source["state"] != "complete":
        lines.append("No explicit source baseline supplied. No change count is asserted.")
    else:
        lines.append(
            "Compared against " + source["baseline"] + ": "
            + str(source["changed_path_count"]) + " changed paths."
        )
        lines.extend("- " + p for p in source["changed_paths"])
        if source["truncated"]:
            lines.append("Path list truncated; full count above includes all changed paths.")
        lines.extend("- " + entry["short_sha"] + " " + entry["subject"]
                     for entry in source["recent_commits"])
    lines.extend(["", "## Saved-brief delta", ""])
    if data["brief_delta"] is None:
        lines.append("No previous briefing supplied; release metadata change is UNKNOWN.")
    else:
        delta = data["brief_delta"]
        lines.append(
            str(delta["changed_gate_count"]) + "/12 gates had tracked metadata differences."
        )
        if delta["unexplained_ledger_byte_change"]:
            lines.append("WARNING: Ledger bytes changed without a tracked field difference.")
        lines.extend("- " + entry["id"] + ": " + ", ".join(entry["changes"])
                     for entry in delta["gate_changes"])
        lines.append("Equal evidence counts do not prove identical or authentic evidence.")
    lines.extend(["", "## Relevant release gates", ""])
    for row in rel["eligible_gates"]:
        lines.append(
            "- " + row["id"] + ": " + row["status"] + "/" + row["required_layer"]
            + ", " + str(row["reference_count"]) + " references, "
            + str(row["witness_count"]) + " registered witnesses"
            + "; blockers: " + (",".join(row["blockers"]) or "none recorded")
        )
    lines.extend([
        "", "## Next decision", "", action["next_decision"],
        "Authority: " + action["action_source"],
    ])
    if action["gate"] is not None:
        lines.append("Ledger excerpt: " + action["ledger_next_action_excerpt"])
    lines.extend([
        "Stop condition: " + action["stop_condition"], "",
        "Re-read live PRs, board and owning source. Run the cheapest qualified"
        " discriminator. Record actual results and provenance in the owning PR.",
        "No tests, original/native oracle, hardware checks or CI dispatch"
        " were run by this generator.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane")
    parser.add_argument("--gate", help="explicitly choose an owned gate such as QA-02")
    parser.add_argument("--since", help="exact 40-character ancestor source SHA")
    parser.add_argument("--previous-brief", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    previous = None
    if args.previous_brief is not None:
        previous = json.loads(args.previous_brief.read_text(encoding="utf-8"))
    data = build_handoff(args.lane, gate=args.gate, since=args.since, previous_brief=previous)
    md = markdown(data)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(md, encoding="utf-8")
    print(md, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
