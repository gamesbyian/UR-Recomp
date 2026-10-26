#!/usr/bin/env python3
"""Read-only live GitHub PR / release / evidence / CI-cost control preflight.

All conclusions are advisory. No game execution, workflow dispatch,
artifact download, branch mutation, release promotion or automatic merge.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from datetime import datetime
import json
from pathlib import Path
import re
import statistics
import subprocess

try:
    from .build_agent_context import LANE_RELEASE_GATES
    from .index_ci_receipts import query as query_receipts
    from .release_evidence_brief import briefing
    from .release_evidence_delta import compare as compare_briefs
    from .ops_live_status import reader as github_reader
except ImportError:
    from build_agent_context import LANE_RELEASE_GATES
    from index_ci_receipts import query as query_receipts
    from release_evidence_brief import briefing
    from release_evidence_delta import compare as compare_briefs
    from ops_live_status import reader as github_reader

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "UR-LIVE-AGENT-RELEASE-PREFLIGHT/1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
MAX_PRS = 25


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def api(repo, endpoint):
    """Reuse the repository's canonical read-only live GitHub API client."""
    require(bool(REPO.fullmatch(repo)), "invalid repository")
    require(endpoint.startswith("repos/" + repo + "/"), "foreign API repository")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    # ops_live_status.reader already owns URL allowlisting, timeout,
    # GitHub API version, token transport and safe failure classification.
    result = github_reader(token)("/" + endpoint)
    require(len(json.dumps(result, ensure_ascii=True)) < 3_000_000,
            "API response oversized")
    return result


def live_snapshot(repo="gamesbyian/UR-Recomp"):
    """Bounded head-safe snapshot. Truncated collections are explicitly unknown."""
    main = api(repo, f"repos/{repo}/branches/main")["commit"]["sha"]
    require(bool(HEX40.fullmatch(main)), "invalid main commit")
    pulls = api(repo, f"repos/{repo}/pulls?state=open&per_page=100")
    require(isinstance(pulls, list), "invalid PR page")
    result = []
    for pr in pulls[:MAX_PRS]:
        number = pr["number"]
        sha = pr["head"]["sha"]
        require(type(number) is int and bool(HEX40.fullmatch(sha)), "invalid PR")
        files = api(repo, f"repos/{repo}/pulls/{number}/files?per_page=100")
        checks = api(repo, f"repos/{repo}/commits/{sha}/check-runs?per_page=100")
        require(isinstance(files, list) and isinstance(checks, dict), "invalid PR evidence")
        detail = api(repo, f"repos/{repo}/pulls/{number}")
        require(detail["head"]["sha"] == sha, "PR advanced during census")
        result.append({
            "number": number, "title": str(pr.get("title", ""))[:160],
            "head_sha": sha, "base_sha": detail["base"]["sha"],
            "draft": bool(pr.get("draft")),
            "mergeable_state": detail.get("mergeable_state"),
            "files": [item["filename"] for item in files],
            "files_complete": len(files) < 100,
            "checks": [
                {"name": c.get("name"), "head_sha": c.get("head_sha"),
                 "status": c.get("status"), "conclusion": c.get("conclusion")}
                for c in checks["check_runs"]
            ],
            "checks_complete": len(checks["check_runs"]) < 100
                               and checks.get("total_count", 0) <= 100,
        })
    closed = api(repo, f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30")
    require(isinstance(closed, list), "invalid closed sample")
    # An agent may update a PR after its individual head/check check. A
    # complete final list re-read refuses to publish a stale review candidate.
    # This is a bounded repeat of an existing read, not a second API client.
    final_pulls = api(repo, f"repos/{repo}/pulls?state=open&per_page=100")
    require(isinstance(final_pulls, list), "invalid final PR census")
    def identity(rows):
        return [(item["number"], item["head"]["sha"],
                 item.get("draft"), item["base"]["sha"])
                for item in rows[:MAX_PRS]]
    require(identity(final_pulls) == identity(pulls)
            and len(final_pulls) == len(pulls),
            "open PR head, draft, base or population changed during census")
    require(api(repo, f"repos/{repo}/branches/main")["commit"]["sha"] == main,
            "main advanced during census")
    return {
        "schema": "UR-GITHUB-PR-SNAPSHOT/1", "repository": repo,
        "main_sha": main, "open_census_complete": len(pulls) < 100 and len(pulls) <= MAX_PRS,
        "open_prs": result,
        "closed_prs_sample": [
            {"number": x["number"], "created_at": x.get("created_at"),
             "merged_at": x.get("merged_at")} for x in closed[:30]],
        "closed_census_complete": False,
    }


def require_local_main(expected_main):
    """Prevent joining live GitHub heads to stale or modified local ledger."""
    require(isinstance(expected_main, str) and bool(HEX40.fullmatch(expected_main)),
            "invalid expected main")
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, text=True,
            capture_output=True, timeout=12, check=True).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
            text=True, capture_output=True, timeout=12, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError("local Git provenance unavailable") from exc
    require(head == expected_main, "live GitHub main and local ledger checkout differ")
    require(not status, "local tracked files modified; ledger attribution unsafe")


def checks_state(rows, complete, head):
    if not complete or not isinstance(rows, list) or not rows:
        return "unknown"
    if any(not isinstance(x, dict) or x.get("head_sha") != head for x in rows):
        return "unknown"
    if any(x.get("conclusion") in
           ("failure", "timed_out", "action_required", "startup_failure") for x in rows):
        return "failed"
    if any(x.get("status") != "completed" for x in rows):
        return "pending"
    if any(x.get("conclusion") not in ("success", "neutral", "skipped") for x in rows):
        return "unknown"
    return ("passed_observed_not_required_set" if
            any(x.get("conclusion") == "success" for x in rows) else "unknown")


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def assess(snapshot, ledger, lane, gate=None, receipts=None, ci=None,
           previous_brief=None, ledger_digest=None):
    require(isinstance(snapshot, dict)
            and snapshot.get("schema") == "UR-GITHUB-PR-SNAPSHOT/1",
            "invalid snapshot schema")
    main = snapshot.get("main_sha")
    require(isinstance(main, str) and bool(HEX40.fullmatch(main)), "invalid main SHA")
    require(lane in LANE_RELEASE_GATES, "unknown agent lane")
    allowed = LANE_RELEASE_GATES[lane]
    require(gate is None or
            (isinstance(gate, str) and re.fullmatch(r"QA-(0[1-9]|1[0-2])", gate)
             and (allowed is None or gate in allowed)),
            "gate outside lane scope")
    view = briefing(ledger, source_sha=main)
    status_delta = {"state": "no_previous_brief",
                    "tracked_gates_changed": None, "passed_status_change": None}
    if previous_brief is not None:
        require(isinstance(previous_brief, dict)
                and isinstance(previous_brief.get("checked_source_commit"), str)
                and bool(HEX40.fullmatch(previous_brief["checked_source_commit"])),
                "previous brief missing exact source")
        require(isinstance(ledger_digest, str)
                and bool(re.fullmatch(r"[0-9a-f]{64}", ledger_digest)),
                "current ledger byte fingerprint unavailable")
        view["ledger_file_sha256"] = ledger_digest
        delta = compare_briefs(previous_brief, view)
        old_passed = sum(g["status"] == "passed" for g in previous_brief["gates"])
        status_delta = {
            "state": "diagnostic_only_not_independent_gate_adjudication",
            "tracked_gates_changed": delta["changed_gate_count"],
            "passed_status_change": view["accepted_gate_count"] - old_passed,
            "ledger_bytes_changed": not delta["same_ledger_bytes"],
            "unexplained_ledger_byte_change": delta["unexplained_ledger_byte_change"],
            "changed_gate_ids": [row["id"] for row in delta["gate_changes"]],
        }
    relevant = [row for row in view["gates"]
                if allowed is None or row["id"] in allowed]
    prs = snapshot.get("open_prs")
    require(isinstance(prs, list) and len(prs) <= MAX_PRS, "invalid PR census")
    numbers = set()
    output = []
    for p in prs:
        require(isinstance(p, dict), "invalid PR row")
        n, sha = p.get("number"), p.get("head_sha")
        require(type(n) is int and n > 0 and n not in numbers, "duplicate PR")
        numbers.add(n)
        require(isinstance(sha, str) and bool(HEX40.fullmatch(sha)), "invalid PR source")
        paths = p.get("files")
        require(isinstance(paths, list) and len(paths) <= 100
                and all(isinstance(v, str) and 0 < len(v) < 500 for v in paths)
                and len(paths) == len(set(paths)), "invalid changed-file set")
        checked = checks_state(p.get("checks"),
                               p.get("checks_complete") is True, sha)
        complete = p.get("files_complete") is True
        current_base = p.get("base_sha") == main
        output.append({
            "number": n, "title": str(p.get("title") or "")[:160],
            "head_sha": sha, "draft": p.get("draft") is True,
            "mergeable_state": p.get("mergeable_state") or "unknown",
            "base_is_current_main": current_base, "check_state": checked,
            "files_complete": complete, "paths": paths,
            "integration_review_candidate": (
                p.get("draft") is False and p.get("mergeable_state") == "clean"
                and current_base and complete
                and checked == "passed_observed_not_required_set"),
        })
    for x in output:
        x["overlaps_with"] = (
            [y["number"] for y in output if y["number"] != x["number"]
             and y["files_complete"] and set(x["paths"]) & set(y["paths"])]
            if x["files_complete"] else None
        )
    local = []
    for row in receipts or []:
        require(isinstance(row, dict) and row.get("source_sha") == main
                and row.get("release_gate_credit") == 0,
                "nonmatching or promoted receipt")
        local.append({k: row[k] for k in
                      ("schema", "digest", "outcome", "observed", "failures", "missing")})
    durations = []
    for x in snapshot.get("closed_prs_sample", []):
        require(isinstance(x, dict), "invalid closed sample")
        start, end = parse_date(x.get("created_at")), parse_date(x.get("merged_at"))
        if start is not None and end is not None and end >= start:
            durations.append((end - start).total_seconds() / 3600)
    cost = {"coverage": "not_supplied", "observed_top_workflows": []}
    if ci is not None:
        require(isinstance(ci, dict) and ci.get("schema_version") == 3,
                "unknown CI report version")
        cost = {
            "coverage": ("complete_requested_window" if ci.get("window_census_complete")
                         else "sample_only"),
            "observed_top_workflows": [{
                "workflow": r["workflow"],
                "runner_seconds_lower_bound": r.get("runner_seconds", 0),
                "missing_job_timing": r.get("runs_missing_job_timing", 0)}
                for r in sorted(ci.get("workflows", []),
                                key=lambda r: -r.get("runner_seconds", 0))[:5]],
        }
    return {
        "schema": SCHEMA, "authority": "read_only_advisory_no_release_credit",
        "repository": snapshot.get("repository"), "main_sha": main,
        "lane": lane, "gate": gate,
        "open_census_complete": snapshot.get("open_census_complete") is True,
        "open_prs": output,
        "release": {
            "nominated_source": view["ledger_candidate_commit"],
            "nominated_zip_sha256": view["ledger_zip_sha256"],
            "main_matches_nominee": view["source_matches_ledger"],
            "passed_recorded": view["accepted_gate_count"],
            "pending_recorded": view["pending_gate_count"],
            "relevant": [r for r in relevant if gate is None or r["id"] == gate],
            "decision": "HOLD_independent_source_zip_hardware_and_gameplay_review",
        },
        "indexed_main_producer_receipts": local,
        "evidence_index_scope": ("local_only" if receipts is not None else "unknown_not_supplied"),
        "ci_cost": cost,
        "recorded_release_status_delta": status_delta,
        "integration_metrics": {
            "closed_sample_count": len(snapshot.get("closed_prs_sample", [])),
            "merged_sample_count": len(durations),
            "sample_median_creation_to_merge_hours": (
                round(statistics.median(durations), 2) if durations else None),
            "complete_population": snapshot.get("closed_census_complete") is True,
            "qualifier": "sampled PR flow is not feature completion",
        },
        "next": [
            "Re-read hourly board and current PRs before selecting owner work",
            "Review exact-head green PRs; GitHub required checks and human QA are separate",
            "Reuse matching producer receipts only after verifying original evidence",
            "Dispatch one existing build-once Windows fan-out only if a new witness is needed",
            "Acquire complete original/native event and physical Windows witnesses",
        ],
        "limitations": [
            "No automatic merge, acceptance, gameplay or hardware testing",
            "PR overlap is a changed-file hint, not a proven conflict",
            "Observed check-runs are not independently verified required checks",
            "Missing local receipts do not imply nonexistent evidence",
            "Partial GitHub samples never imply full-week CI or throughput totals",
        ],
    }


def markdown(result):
    v = result["release"]
    lines = [
        "# Agent live release preflight", "",
        "Read-only integration navigation; not permission to merge or deploy.",
        "Current main: " + result["main_sha"],
        "PR census: " + ("complete" if result["open_census_complete"] else "PARTIAL"),
        f"Recorded gate status: {v['passed_recorded']}/12 passed, {v['pending_recorded']} pending.",
        "Nominated candidate equals main: " + str(v["main_matches_nominee"]),
        "Deployment: " + v["decision"], "",
        "## Active PR integration preflight", "",
    ]
    for p in result["open_prs"]:
        overlaps = p["overlaps_with"]
        lines.append(
            f"- #{p['number']}: " + ("DRAFT " if p["draft"] else "")
            + p["check_state"] + "; mergeable=" + p["mergeable_state"]
            + "; base-current=" + str(p["base_is_current_main"])
            + "; overlaps=" + ("unknown" if overlaps is None else str(overlaps))
            + "; owner-review=" + str(p["integration_review_candidate"]))
    lines.extend(["", "## Candidate-bound gates", ""])
    for g in v["relevant"]:
        lines.append("- " + g["id"] + ": " + g["status"]
                     + "; " + g["required_layer"] + "; "
                     + ",".join(g["blockers"]))
    lines.extend(["", "## Reuse and measured cost", "",
                  "Indexed exact-main producer receipts: "
                  + str(len(result["indexed_main_producer_receipts"]))
                  + " (" + result["evidence_index_scope"] + ", zero gate credit)",
                  "CI runtime coverage: " + result["ci_cost"]["coverage"]])
    for x in result["ci_cost"]["observed_top_workflows"]:
        lines.append("- " + x["workflow"] + ": runner seconds >= "
                     + str(x["runner_seconds_lower_bound"])
                     + "; missing jobs=" + str(x["missing_job_timing"]))
    status = result["recorded_release_status_delta"]
    lines.append(
        "Recorded release metadata delta: " + status["state"]
        + "; changed gates=" + str(status["tracked_gates_changed"])
        + "; recorded passed-status change=" + str(status["passed_status_change"])
        + " (not independent QA)."
    )
    m = result["integration_metrics"]
    lines.append(
        f"Recent closed sample {m['closed_sample_count']}, merged {m['merged_sample_count']}, "
        f"median merge turnaround {m['sample_median_creation_to_merge_hours']} h "
        "(sample only, not product progress).")
    lines.extend(["", "## Next owner actions", ""])
    lines.extend("- " + x for x in result["next"])
    lines.extend(["", "## Limits", ""])
    lines.extend("- " + x for x in result["limitations"])
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default="gamesbyian/UR-Recomp")
    selection = p.add_mutually_exclusive_group(required=True)
    selection.add_argument("--live", action="store_true")
    selection.add_argument("--snapshot", type=Path)
    p.add_argument("--lane", required=True, choices=sorted(LANE_RELEASE_GATES))
    p.add_argument("--gate")
    p.add_argument("--receipt-db", type=Path)
    p.add_argument("--ci-runtime-report", type=Path)
    p.add_argument("--previous-brief", type=Path)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    args = p.parse_args()
    data = live_snapshot(args.repo) if args.live else json.loads(
        args.snapshot.read_text(encoding="utf-8"))
    if args.live:
        require_local_main(data["main_sha"])
    ledger_bytes = (ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_bytes()
    ledger = json.loads(ledger_bytes)
    existing = (query_receipts(args.receipt_db, data["main_sha"], 100)
                if args.receipt_db else None)
    costing = (json.loads(args.ci_runtime_report.read_text(encoding="utf-8"))
               if args.ci_runtime_report else None)
    previous = (json.loads(args.previous_brief.read_text(encoding="utf-8"))
                if args.previous_brief else None)
    result = assess(data, ledger, args.lane, args.gate, existing, costing,
                    previous, hashlib.sha256(ledger_bytes).hexdigest())
    rendered = markdown(result)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
