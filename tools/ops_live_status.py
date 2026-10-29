#!/usr/bin/env python3
"""GitHub-live read-only operations report; never infer Drive or schedule status."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
try:
    from .agent_control import BOARD, REGISTRY, extract_board, load_json, validate_registry
    from .validate_history_custody import load as load_custody, validate as validate_custody
    from .ci_cancelled_job_sample import sample_cancelled_jobs
    from .audit_recovery_handoff_drift import scan as scan_handoff_drift
except ImportError:
    from agent_control import BOARD, REGISTRY, extract_board, load_json, validate_registry
    from validate_history_custody import load as load_custody, validate as validate_custody
    from ci_cancelled_job_sample import sample_cancelled_jobs
    from audit_recovery_handoff_drift import scan as scan_handoff_drift

REPO = "gamesbyian/UR-Recomp"
# Recurring producers: a successful manual dispatch does not prove the
# scheduler or its automatic workflow_run trigger is still working.
# Each probe examines the workflow-specific latest 30 runs, not latest 100.
CRITICAL_RECOVERY = {
    "intake": ("vault-recurring-intake.yml", {"schedule"}),
    "review": ("vault-actionable-review.yml", {"workflow_run"}),
}
RECOVERY_REVIEW_AFTER_HOURS = 18


def latest_recovery_workflows(get, base, now):
    """Observe bounded actual runs; never mistake PR-only CI for production."""
    observations = {}
    for lane, (workflow, allowed_events) in CRITICAL_RECOVERY.items():
        response = get(base + f"/actions/workflows/{workflow}/runs?per_page=30")
        runs = response.get("workflow_runs")
        if not isinstance(runs, list):
            raise ValueError("invalid critical workflow run sample")
        valid = next((run for run in runs
                      if run.get("head_branch") == "main"
                      and run.get("event") in allowed_events), None)
        if valid is None:
            observations[lane] = {"status": "UNKNOWN_NO_ELIGIBLE_RUN",
                                  "sampled_runs": len(runs)}
            continue
        when = timestamp(valid.get("created_at"))
        run_id = valid.get("id")
        if when is None or type(run_id) is not int or run_id <= 0:
            observations[lane] = {"status": "UNKNOWN_MALFORMED_RUN"}
            continue
        age_seconds = (now - when).total_seconds()
        if age_seconds < 0:
            observations[lane] = {"status": "UNKNOWN_FUTURE_TIMESTAMP"}
            continue
        if age_seconds >= RECOVERY_REVIEW_AFTER_HOURS * 3600:
            status = "OVERDUE_REVIEW"
        elif valid.get("status") != "completed":
            status = "IN_FLIGHT"
        elif valid.get("conclusion") == "success":
            status = "RECENT_SUCCESS"
        else:
            status = "RECENT_NON_SUCCESS"
        observations[lane] = {
            "status": status, "run_id": run_id,
            "url": f"https://github.com/{REPO}/actions/runs/{run_id}",
            "conclusion": valid.get("conclusion"),
            "created_at": when.isoformat(),
            "age_hours": round(age_seconds / 3600, 1),
            "sampled_runs": len(runs),
        }
    # Two independent green recent runs can conceal a missing downstream
    # trigger if the last actionable review predates the newest intake.
    intake = observations.get("intake", {})
    review = observations.get("review", {})
    if (intake.get("status") == "RECENT_SUCCESS"
            and review.get("status") in {"RECENT_SUCCESS", "IN_FLIGHT"}
            and review.get("created_at") < intake.get("created_at")):
        review["status"] = "UPSTREAM_NOT_REVIEWED"
        review["latest_intake_run_id"] = intake["run_id"]
        review["latest_intake_url"] = intake["url"]
    return observations


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None

# A recently active pair of open PRs claiming the same Work ID may duplicate
# engineering and expensive CI. This is a review hint, not a source-file lock.
# PR bodies are already present in the bounded /pulls census; no extra API
# requests, CI jobs or new coordination system are needed.
PR_WORK_ID = re.compile(
    r"(?im)^\s*(?:\*\*)?work id(?:\*\*)?\s*:(?:\*\*)?\s*(?:\*\*|`)?(UR-[A-Z0-9-]+)"
)
RECENT_HEAD_HOURS = 36


def recent_same_work_id_hints(prs, known_work_ids, now):
    """Find overlapping *claims* in fresh open PRs, never infer file writes.

    An incomplete GitHub census may prove a positive collision, but its absence
    cannot prove no other PR is active. Drafts are included for discovery, not
    presumed active, and old or malformed timestamps are not treated as locks.
    """
    groups = {}
    for row in prs:
        if not isinstance(row, dict):
            continue
        match = PR_WORK_ID.search(str(row.get("body") or ""))
        number = row.get("number")
        when = timestamp(row.get("updated_at"))
        if (not match or match.group(1) not in known_work_ids
                or type(number) is not int or number <= 0 or when is None):
            continue
        seconds = (now - when).total_seconds()
        if not 0 <= seconds <= RECENT_HEAD_HOURS * 3600:
            continue
        entry = {"pr": number, "draft": row.get("draft") is True}
        groups.setdefault(match.group(1), {})[number] = entry
    return [
        {"work_id": wid,
         "prs": [items[num] for num in sorted(items)],
         "classification": "REVIEW_POSSIBLE_DUPLICATE_NOT_A_WRITE_LOCK"}
        for wid, items in sorted(groups.items())
        if len(items) >= 2
    ]


def cancelled_branch_churn_hints(runs, limit=3):
    """Show repeated superseded PR *heads* already in the latest Actions page.

    This uses the same bounded run census; no additional API calls. A cancelled
    run is not evidence of consumed runner time, a defect, or bad agent work.
    Requiring multiple distinct head SHAs avoids treating repeated events on
    one head as a burst of editing.
    """
    groups = {}
    for run in runs:
        if (not isinstance(run, dict) or run.get("event") != "pull_request"
                or run.get("conclusion") != "cancelled"):
            continue
        branch, sha = run.get("head_branch"), run.get("head_sha")
        if (not isinstance(branch, str)
                or not re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", branch)
                or not isinstance(sha, str)
                or not re.fullmatch(r"[0-9a-f]{40}", sha)):
            continue
        row = groups.setdefault(branch, {"cancelled_runs": 0, "head_shas": set()})
        row["cancelled_runs"] += 1
        row["head_shas"].add(sha)
    leads = [
        {"branch": branch, "cancelled_runs": row["cancelled_runs"],
         "distinct_heads": len(row["head_shas"])}
        for branch, row in groups.items()
        if row["cancelled_runs"] >= 2 and len(row["head_shas"]) >= 2
    ]
    leads.sort(key=lambda x: (-x["cancelled_runs"], -x["distinct_heads"], x["branch"]))
    return leads[:limit]


def head_sha():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

def reader(token=""):
    def get(path):
        if not re.fullmatch(r"/repos/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_/?&=.,+-]*", path):
            raise ValueError("disallowed API path")
        headers = {"Accept": "application/vnd.github+json",
                   "User-Agent": "UR-Recomp-live-ops",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with urlopen(Request("https://api.github.com" + path,
                                 headers=headers), timeout=12) as response:
                return json.load(response)
        except HTTPError as err:
            raise ValueError(f"HTTP {err.code}") from None
        except (URLError, TimeoutError):
            raise ValueError("transport unavailable") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("invalid API JSON") from None
    return get

def paged(get, path, max_pages=3):
    all_rows = []
    for page in range(1, max_pages + 1):
        data = get(path + f"&per_page=100&page={page}")
        if not isinstance(data, list):
            raise ValueError("invalid paged array")
        all_rows.extend(data)
        if len(data) < 100:
            return all_rows, True
    return all_rows, False

def snapshot(get, *, board, registry, ledger, local_head=None, now=None, repo=REPO, custody=None):
    now = now or datetime.now(timezone.utc)
    base = "/repos/" + repo
    result = {
        "schema": "ur-ops-live/1", "observed_at_utc": now.isoformat().replace("+00:00", "Z"),
        "repository": repo, "main": None, "prs": None, "actions": None,
        "recovery_workflows": None, "qa": None, "backup": None, "errors": {}, "drive": "UNKNOWN_NOT_CONNECTED",
        "scheduled_agent_health": "UNKNOWN_NOT_CONNECTED",
        "dispatch": [{"agent": x["number"], "minute": x["minute"],
                      "selection": "shared_pool_top_five",
                      "candidate_work_ids": [j["work_id"] for j in board["work"]
                                             if j["state"] in {"ready", "in_review"}][:5]}
                     for x in board["agents"]],
        "recovery": [], "handoff_drift": {"status": "UNKNOWN_NOT_CHECKED"},
    }
    try:
        b = get(base + "/branches/main")
        sha = b["commit"]["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("invalid branch SHA")
        result["main"] = {"sha": sha, "protected": b.get("protected")}
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        result["errors"]["main"] = str(err)
    if custody is not None:
        try:
            receipt = validate_custody(custody)
            current = result["main"]["sha"] if result["main"] else None
            result["backup"] = {
                "source_commit": receipt["source_commit"],
                "recorded_restored_commits": receipt["commit_count"],
                "verified_at_utc_date": receipt["verification_date_utc"],
                "multipart_drive_items": receipt["part_count"] + 1,
                "status": "historical_restored_backup",
                "observed_main_exactly_in_backup": current == receipt["source_commit"] if current else None,
                "current_drive_integrity": "UNKNOWN_NOT_CHECKED",
                "scope": "main_git_history_only",
            }
        except (TypeError, ValueError, KeyError) as err:
            result["errors"]["backup"] = "invalid custody receipt: " + str(err)
    else:
        result["errors"]["backup"] = "no historical backup receipt available"
    try:
        prs, complete = paged(get, base + "/pulls?state=open")
        if not all(isinstance(x, dict) for x in prs):
            raise ValueError("invalid PR")
        stale = [{"number": x.get("number"), "hours_since_update":
                  int((now - timestamp(x.get("updated_at"))).total_seconds() // 3600)}
                 for x in prs if timestamp(x.get("updated_at"))
                 and 0 <= (now - timestamp(x.get("updated_at"))).total_seconds()
                 and (now - timestamp(x.get("updated_at"))).total_seconds() >= 172800]
        result["prs"] = {"count": len(prs), "census_complete": complete,
                         "draft": sum(x.get("draft") is True for x in prs),
                         "unchanged_48h_sample": stale[:20],
                         "unchanged_48h_count": len(stale),
                         "recent_same_work_id_hints": recent_same_work_id_hints(
                             prs, {j["work_id"] for j in board["work"]}, now),
                         "items": [{"number": x.get("number"), "title": str(x.get("title") or "")[:100],
                                    "url": x.get("html_url"), "draft": x.get("draft"),
                                    "updated_at": x.get("updated_at")} for x in prs[:25]]}
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        result["errors"]["prs"] = str(err)
    # Merge-to-vault handoff continuity is a hint, never an automatic
    # integration claim. Partial/failed closed-PR censuses are UNKNOWN.
    try:
        # Old PRs can merge today: sample by latest update rather than
        # GitHub's default creation order. A bounded scan stays incomplete.
        closed, complete = paged(get, base + "/pulls?state=closed&sort=updated&direction=desc")
        # A partial census can still prove a positive match. It cannot
        # prove absence of a match in unobserved older closed PRs.
        drift = scan_handoff_drift(registry, closed)
        if complete:
            status = "REVIEW_HINTS" if drift["hints"] else "NO_HINTS_IN_CURATED_SCOPE"
        else:
            status = ("PARTIAL_CENSUS_REVIEW_HINTS" if drift["hints"]
                      else "UNKNOWN_INCOMPLETE_PR_CENSUS")
        result["handoff_drift"] = {
            "status": status,
            "census_complete": complete,
            "observed_closed_prs": len(closed),
            "merged_prs_checked": drift["merged_prs_checked"],
            "candidates_checked": drift["candidate_count"],
            "hints": drift["hints"],
            "automatic_state_changes": 0,
        }
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        result["handoff_drift"] = {"status": "UNKNOWN_API_OR_DATA_FAILURE"}
        result["errors"]["handoff_drift"] = str(err)
    try:
        runs = get(base + "/actions/runs?per_page=100&page=1")
        latest = runs["workflow_runs"]
        if not isinstance(latest, list):
            raise ValueError("invalid workflow sample")
        cancel_groups = Counter((x.get("name") or "unnamed workflow")
                                for x in latest if x.get("conclusion") == "cancelled")
        # Preserve up to five exact run links per diagnostic class. These
        # hints are bounded by the sampled first page, not a complete census.
        failed_leads, aging_leads = [], []
        for run in latest:
            run_id = run.get("id")
            if type(run_id) is not int or run_id <= 0:
                continue
            lead = {"run_id": run_id,
                    "workflow": str(run.get("name") or "unnamed workflow")[:120],
                    "url": f"https://github.com/{repo}/actions/runs/{run_id}"}
            if run.get("conclusion") in {"failure", "timed_out", "startup_failure", "action_required"}:
                if len(failed_leads) < 5:
                    failed_leads.append({**lead, "conclusion": run["conclusion"]})
            elif run.get("status") in {"queued", "in_progress", "waiting", "pending", "requested"}:
                started = timestamp(run.get("created_at"))
                if started is not None:
                    seconds = (now - started).total_seconds()
                    if seconds >= 7200 and len(aging_leads) < 5:
                        aging_leads.append({**lead, "status": run["status"],
                                            "age_minutes": int(seconds // 60)})
        result["actions"] = {
            "scope": "latest_100_only_not_a_day_or_billing_measure",
            "cancelled_runner_job_sample": sample_cancelled_jobs(get, base, latest),
            "cancelled_branch_churn_hints": cancelled_branch_churn_hints(latest),
            "cancelled_by_workflow": [
                {"workflow": name[:120], "count": count}
                for name, count in sorted(cancel_groups.items(), key=lambda pair: (-pair[1], pair[0]))[:5]
            ],
            "sampled": len(latest),
            "failed_run_leads": failed_leads,
            "aging_in_flight_leads": aging_leads,
            "outcomes": dict(Counter(x.get("conclusion") or x.get("status") or "unknown"
                                     for x in latest)),
            "earliest_observed_at": latest[-1].get("created_at") if latest else None,
            "latest_observed_at": latest[0].get("created_at") if latest else None,
        }
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        result["errors"]["actions"] = str(err)
    try:
        result["recovery_workflows"] = latest_recovery_workflows(get, base, now)
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        result["errors"]["recovery_workflows"] = str(err)
    for item in registry["candidates"]:
        row = {"candidate_id": item["candidate_id"], "work_id": item["work_id"],
               "recorded_state": item["state"], "drive_id": item["drive_id"],
               "check": "NO_LIVE_PR_REFERENCE", "pr": item.get("github_pr")}
        if item.get("github_pr"):
            try:
                actual = get(base + "/pulls/" + str(item["github_pr"]))
                if actual.get("merged_at"):
                    if item["state"] == "merged" and item.get("merge_sha") == actual.get("merge_commit_sha"):
                        row["check"] = "MERGE_SHA_VERIFIED"
                    else:
                        row["check"] = "RECORDED_STATUS_OR_SHA_CONFLICT"
                elif item["state"] == "merged":
                    row["check"] = "RECORDED_MERGE_NOT_FOUND"
                else:
                    row["check"] = "NOT_MERGED"
                row["live_draft"] = actual.get("draft")
            except (ValueError, TypeError, KeyError, AttributeError) as err:
                row["check"] = "UNKNOWN"
                row["error"] = str(err)
        result["recovery"].append(row)
    if isinstance(ledger, dict) and ledger.get("schema") == "UR-RELEASE-QUALITY-LEDGER/1":
        gates = ledger.get("gates")
        if isinstance(gates, list):
            qa01 = next((x for x in gates if x.get("id") == "QA-01"), {})
            coverage = qa01.get("coverage", {})
            matched = bool(result["main"] and result["main"]["sha"] == local_head)
            result["qa"] = {"source_exact_main": matched, "local_commit_sha": local_head,
                            "ledger_updated": ledger.get("updated"),
                            "gate_count": len(gates),
                            "gate_statuses": dict(Counter(x.get("status", "unknown") for x in gates)),
                            "usa_events_accepted": coverage.get("complete_event_passes"),
                            "usa_events_total": coverage.get("denominator"),
                            "physical_verified": ledger.get("candidate", {}).get("physical_hardware_verified")}
            if not matched:
                result["errors"]["qa"] = "checkout and observed main SHA differ; ledger values historical ONLY"
        else:
            result["errors"]["qa"] = "invalid release gates"
    else:
        result["errors"]["qa"] = "release ledger missing or invalid"
    return result

def markdown(s):
    rows = ["# UR-Recomp live operations",
            "", "Observed UTC: " + s["observed_at_utc"],
            "GitHub live API. Drive and ChatGPT schedule health are NOT connected or inferred.",
            ""]
    main = s["main"]
    rows.append("- Main: " + (main["sha"][:12] + ", protected=" + str(main["protected"])
               if main else "UNKNOWN"))
    prs = s["prs"]
    rows.append("- Open PRs: " +
                (str(prs["count"]) + (" complete" if prs["census_complete"] else " PARTIAL") +
                 f", {prs['draft']} draft, {prs['unchanged_48h_count']} with >48h since last update (not proof of inactivity)"
                 if prs else "UNKNOWN"))
    if prs and prs.get("recent_same_work_id_hints"):
        for hint in prs["recent_same_work_id_hints"]:
            labels = ", ".join(
                "#" + str(p["pr"]) + (" (draft)" if p["draft"] else " (reviewable)")
                for p in hint["prs"]
            )
            rows.append("- **REVIEW possible same-work-ID PR overlap:** " +
                        hint["work_id"] + " " + labels +
                        ". Inspect exact changed paths and live writers before "
                        "starting a competing patch; this is NOT a lock or "
                        "proof of duplicate source.")
    actions = s["actions"]
    rows.append("- Actions: " +
                (f"latest {actions['sampled']} only " + repr(actions["outcomes"]) +
                 " (NOT daily totals or runner minutes)" if actions else "UNKNOWN"))
    if actions and actions["failed_run_leads"]:
        rows.append("- **Recent failure triage (latest sample only):** " +
                    "; ".join(f"{item['workflow']} [{item['conclusion']}] {item['url']}"
                              for item in actions["failed_run_leads"]) +
                    ". Inspect each job's first failed step; this is not a full census.")
    if actions and actions["aging_in_flight_leads"]:
        rows.append("- **Older in-flight review leads (not proof of stalls):** " +
                    "; ".join(f"{item['workflow']} [{item['status']}, "
                              f"{item['age_minutes']}m since created] {item['url']}"
                              for item in actions["aging_in_flight_leads"]) +
                    ". Check current status before intervening.")
    recovery_workflows = s["recovery_workflows"]
    if recovery_workflows is None:
        rows.append("- **Critical Vault workflow health:** UNKNOWN (GitHub API read failed).")
    else:
        for name, observed in recovery_workflows.items():
            row = f"- **Vault {name} production:** {observed['status']}"
            if observed.get("url"):
                row += (f" ({observed['url']}, age {observed['age_hours']}h, "
                        f"conclusion={observed['conclusion']})")
            if observed.get("latest_intake_url"):
                row += f"; awaiting review after {observed['latest_intake_url']}"
            rows.append(row + "; latest 30 workflow runs only, not a full history.")
    if actions and actions.get("cancelled_branch_churn_hints"):
        for lead in actions["cancelled_branch_churn_hints"]:
            rows.append(
                "- **Review PR head churn:** `" + lead["branch"] + "` had " +
                f"{lead['cancelled_runs']} cancelled runs across " +
                f"{lead['distinct_heads']} distinct PR head SHAs in the latest sample. " +
                "Consider coalescing the next coherent source/test push or using a "
                "draft while iterating. This is NOT proof of wasted runner time, "
                "fault, or active file ownership.")
    if actions and actions["cancelled_by_workflow"]:
        rows.append("- Cancellation leads (same latest sample only): " +
                    "; ".join(f"{x['workflow']}: {x['count']}" for x in actions["cancelled_by_workflow"]) +
                    ". Counts are NOT lost runner minutes.")
    if actions:
        measured = actions["cancelled_runner_job_sample"]
        rows.append(
            "- **Cancelled-runner sample:** " +
            f"{measured['observed_runner_seconds']/60:.1f} observed runner-minutes " +
            f"across {measured['verified_job_censuses']}/{measured['selected']} " +
            "selected latest cancelled runs. " +
            f"{len(measured['unknown_censuses'])} job censuses UNKNOWN; " +
            f"{measured['unselected_cancelled_runs']} other cancelled runs NOT measured. " +
            "Latest attempt only; not billable minutes, a full-day census or proof of wasted work."
        )
        for name_row in measured["workflows"][:5]:
            rows.append("- " + name_row["workflow"] + ": " +
                        f"{name_row['runner_seconds']/60:.1f} observed runner-minutes; " +
                        f"{name_row['runs']} cancelled runs sampled " +
                        f"({name_row['zero_started_jobs']} with zero started jobs)")
    qa = s["qa"]
    rows.append("- Release ledger: " +
                (("exact observed main" if qa["source_exact_main"] else "STALE / UNVERIFIED SOURCE") +
                 f"; {qa['gate_count']} gates " + repr(qa["gate_statuses"]) +
                 f"; complete USA events {qa['usa_events_accepted']}/{qa['usa_events_total']}"
                 if qa else "UNKNOWN"))
    backup = s["backup"]
    if backup:
        status = ("current main exactly matches saved backup" if backup["observed_main_exactly_in_backup"]
                  else "historical backup only; current main not proved recoverable at this SHA")
        rows.append("- **Drive backup (recorded):** " + backup["source_commit"][:12] +
                    " / " + str(backup["recorded_restored_commits"]) + " commits, " +
                    backup["verified_at_utc_date"] + "; " + status +
                    ". Current Drive file integrity UNKNOWN (not checked in this run).")
    else:
        rows.append("- **Drive backup:** UNKNOWN (no valid historical custody receipt)")
    rows.extend(["", "## Dispatch definitions, not observed scheduled-agent activity", "",
                 "| Agent | Start | Shared top-five candidate work IDs |", "| --- | --- | --- |"])
    for a in s["dispatch"]:
        rows.append(f"| {a['agent']} | :{a['minute']:02d} | " +
                    " / ".join(a["candidate_work_ids"]) + " |")
    drift = s["handoff_drift"]
    rows.append("- Recovery handoff cross-check: " + drift["status"] +
                " (closed PR descriptions vs curated registry; no Drive readback).")
    for hint in drift.get("hints", []):
        rows.append("- REVIEW: " + hint["candidate_id"] + " recorded " +
                    hint["recorded_state"] + " but merged PR #" +
                    str(hint["linked_merged_pr"]) + " references its Drive ID; " +
                    "inspect every member before revising the existing registry.")
    rows.extend(["", "## Recovery registry, curated only; Drive presence UNKNOWN", ""])
    for x in s["recovery"]:
        rows.append("- " + x["candidate_id"] + ": " + x["recorded_state"] +
                    "; live PR verification " + x["check"])
    if s["errors"]:
        rows.extend(["", "## Failed / stale inputs", ""])
        for key, value in sorted(s["errors"].items()):
            rows.append("- " + key + ": " + value)
    rows.extend(["", "Neither a successful source check nor a Drive archive awards a QA gate.", ""])
    return "\n".join(rows)

def required_live_sources_present(report):
    """Fail closed when critical GitHub data or recurring recovery is unhealthy."""
    if not all(report.get(key) is not None
               for key in ("main", "prs", "actions", "recovery_workflows")):
        return False
    return all(row["status"] in {"RECENT_SUCCESS", "IN_FLIGHT"}
               for row in report["recovery_workflows"].values())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--format", choices=("markdown", "json"), default="markdown")
    p.add_argument("--output", type=Path)
    p.add_argument("--json-output", type=Path, help="also save same observation as JSON")
    args = p.parse_args()
    board = extract_board(BOARD.read_text(encoding="utf8"))
    registry = load_json(REGISTRY)
    validate_registry(registry, board)
    try:
        recorded_custody = load_custody()
    except (OSError, ValueError):
        recorded_custody = None
    report = snapshot(reader(os.environ.get("GITHUB_TOKEN", "")), board=board,
                      registry=registry,
                      ledger=load_json(ROOT / "docs/RELEASE-QUALITY-LEDGER.json"),
                      local_head=head_sha(), custody=recorded_custody)
    output = (markdown(report) if args.format == "markdown"
              else json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    if args.output:
        args.output.write_text(output, encoding="utf8")
    else:
        print(output, end="")
    # Preserve the partial report but make absent mandatory telemetry non-green.
    return 0 if required_live_sources_present(report) else 1

if __name__ == "__main__":
    sys.exit(main())
