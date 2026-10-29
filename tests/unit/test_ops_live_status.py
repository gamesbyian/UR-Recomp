"""Live ops report must expose API loss, stale evidence and bounded sampling."""
from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, REGISTRY, extract_board, load_json
from ops_live_status import markdown, required_live_sources_present, snapshot, timestamp
from validate_history_custody import load as load_custody

SHA = "a" * 40
MERGE = "5cdbbc57dc991d77df10c1a2ecabab2772c8063c"
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)

class LiveOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = extract_board(BOARD.read_text(encoding="utf8"))
        cls.registry = load_json(REGISTRY)
        cls.ledger = {
            "schema": "UR-RELEASE-QUALITY-LEDGER/1", "updated": "2026-10-21",
            "gates": [{"id": "QA-01", "status": "in_progress",
                       "coverage": {"complete_event_passes": 0, "denominator": 45}},
                      {"id": "QA-02", "status": "unverified"}],
            "candidate": {"physical_hardware_verified": False},
        }

    def request(self, path):
        if path.endswith("/branches/main"):
            return {"commit": {"sha": SHA}, "protected": True}
        if "/pulls?state=open&" in path:
            return [{"number": 101, "draft": True,
                     "updated_at": "2026-10-18T11:00:00Z", "title": "Draft test"}]
        if "/pulls/2110" in path:
            return {"state": "closed", "merged_at": "2026-10-21T05:00:00Z",
                    "merge_commit_sha": MERGE, "draft": False}
        if "/pulls/2104" in path:
            return {"state": "closed", "merged_at": "2026-10-21T05:00:00Z",
                    "merge_commit_sha": "2321f3f4b6286204be43bb2502dce6573378fc2c"}
        if "/pulls/1996" in path:
            return {"state": "open", "merged_at": None, "draft": True}
        if "/actions/workflows/" in path:
            event = "schedule" if "vault-recurring-intake" in path else "workflow_run"
            return {"workflow_runs": [
                {"id": 4000 if event == "schedule" else 4001,
                 "head_branch": "main", "event": event,
                 "created_at": "2026-10-21T10:00:00Z",
                 "status": "completed", "conclusion": "success"}]}
        if "/actions/runs" in path:
            return {"total_count": 40000, "workflow_runs": [
                {"created_at": "2026-10-21T06:00:00Z", "status": "completed",
                 "conclusion": "success"},
                {"created_at": "2026-10-21T05:59:00Z", "status": "completed",
                 "conclusion": "cancelled"},
            ]}
        raise ValueError("unexpected route")

    def report(self, get=None, local_head=SHA, registry=None):
        return snapshot(get or self.request, board=self.board,
                        registry=self.registry if registry is None else registry,
                        ledger=self.ledger, local_head=local_head, now=NOW)

    @staticmethod
    def handoff_fixture(state="blocked"):
        # Independent of the changing curated registry: #2200 legitimately
        # resolves this historical candidate and must not break CI.
        return {
            "schema": "ur-recovery-registry/1",
            "scope": "curated_not_exhaustive",
            "candidates": [{
                "candidate_id": "h27-knowledge-malformed-lanes",
                "work_id": "UR-KNOWLEDGE-01",
                "state": state,
                "drive_id": "1_RScoARFTHjfttOY87v9PKBepXmE8tK8",
                "github_pr": None,
            }],
        }

    def merged_receipt_fixture(self):
        # Isolate the fixed merge-SHA regression from the curated registry:
        # after a Vault clearout, the original historical row may disappear.
        return {
            "schema": "ur-recovery-registry/1",
            "scope": "curated_not_exhaustive",
            "candidates": [{
                "candidate_id": "fixture-pinned-merge",
                "work_id": self.board["work"][0]["work_id"],
                "drive_id": "test-verified-archive-00001",
                "state": "merged", "github_pr": 2110,
                "merge_sha": MERGE, "failure_class": "none",
                "discriminator": "independent-merge-sha-receipt",
                "next_action": "Retain source receipt", "release_gate_credit": False,
            }],
        }

    def test_live_main_and_recency_are_explicit(self):
        result = self.report()
        self.assertTrue(result["main"]["protected"])
        self.assertEqual(result["prs"]["count"], 1)
        self.assertTrue(result["prs"]["census_complete"])
        self.assertEqual(result["prs"]["unchanged_48h_count"], 1)
        self.assertTrue(result["qa"]["source_exact_main"])

    def test_recent_same_work_id_heads_are_discovery_hints_not_locks(self):
        work_id = self.board["work"][0]["work_id"]
        def fake(path):
            if "/pulls?state=open&" in path:
                return [
                    {"number": 501, "draft": False, "body": "Work ID: `" + work_id + "`",
                     "title": "Source repair", "updated_at": "2026-10-21T11:40:00Z"},
                    {"number": 502, "draft": True, "body": "**Work ID:** **" + work_id + "**",
                     "title": "Independent tester", "updated_at": "2026-10-21T11:30:00Z"},
                    {"number": 503, "draft": False, "body": "Work ID: `" + work_id + "`",
                     "title": "Expired historical patch", "updated_at": "2026-10-19T01:00:00Z"},
                    {"number": 504, "draft": False, "body": "Unassigned exploratory PR",
                     "updated_at": "2026-10-21T11:30:00Z"},
                ]
            return self.request(path)
        report = self.report(get=fake)
        hints = report["prs"]["recent_same_work_id_hints"]
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["work_id"], work_id)
        self.assertEqual([p["pr"] for p in hints[0]["prs"]], [501, 502])
        self.assertEqual([p["draft"] for p in hints[0]["prs"]], [False, True])
        self.assertIn("NOT a lock", markdown(report))
        self.assertIn("exact changed paths", markdown(report))

    def test_unknown_or_single_pr_never_claims_no_collision(self):
        def fake(path):
            if "/pulls?state=open&" in path:
                return [
                    {"number": 501, "body": "Work ID: `UR-NOT-IN-BOARD-20261021`",
                     "updated_at": "2026-10-21T11:30:00Z"},
                    {"number": 502, "body": "Work ID: `UR-NOT-IN-BOARD-20261021`",
                     "updated_at": "2026-10-21T11:30:00Z"},
                    {"number": 503, "body": "Work ID: `" + self.board["work"][0]["work_id"] + "`",
                     "updated_at": "malformed"},
                ]
            return self.request(path)
        report = self.report(get=fake)
        self.assertEqual(report["prs"]["recent_same_work_id_hints"], [])
        self.assertNotIn("REVIEW possible same-work-ID PR overlap", markdown(report))

    def test_latest_actions_is_not_day_or_full_billing(self):
        result = self.report()
        self.assertEqual(result["actions"]["outcomes"]["cancelled"], 1)
        self.assertEqual(result["actions"]["sampled"], 2)
        self.assertIn("latest_100_only", result["actions"]["scope"])
        self.assertIn("NOT daily totals", markdown(result))

    def test_cancellation_leads_ranked_only_within_latest_bounded_sample(self):
        def fake(path):
            if "/actions/runs?" in path:
                rows = [
                    {"created_at": "2026-10-21T06:00:00Z", "conclusion": "cancelled",
                     "name": name} for name in ("Windows", "Unit", "Windows", "Windows", "Unit")
                ]
                rows.append({"created_at": "2026-10-21T05:59:00Z",
                             "conclusion": "success", "name": "Windows"})
                return {"workflow_runs": rows}
            return self.request(path)
        report = self.report(get=fake)
        self.assertEqual(
            report["actions"]["cancelled_by_workflow"],
            [{"workflow": "Windows", "count": 3},
             {"workflow": "Unit", "count": 2}],
        )
        self.assertIn("Counts are NOT lost runner minutes", markdown(report))
        self.assertIn("latest_100_only", report["actions"]["scope"])

    def test_cancelled_branch_churn_requires_distinct_pr_heads_and_is_bounded(self):
        def event(branch, sha, event_name="pull_request", conclusion="cancelled"):
            return {"head_branch": branch, "head_sha": sha,
                    "event": event_name, "conclusion": conclusion,
                    "created_at": "2026-10-21T06:00:00Z", "name": "Tooling"}

        def fake(path):
            if "/actions/runs?" in path:
                return {"workflow_runs": [
                    event("agent/high-churn", "a" * 40),
                    event("agent/high-churn", "b" * 40),
                    event("agent/high-churn", "b" * 40),
                    event("agent/two-heads", "c" * 40),
                    event("agent/two-heads", "d" * 40),
                    event("agent/same-head-only", "e" * 40),
                    event("agent/same-head-only", "e" * 40),
                    event("agent/unsafe|markdown", "f" * 40),
                    event("agent/push-not-pr", "1" * 40, "push"),
                    event("agent/push-not-pr", "2" * 40, "push"),
                    event("agent/green", "3" * 40, conclusion="success"),
                ]}
            return self.request(path)

        report = self.report(get=fake)
        self.assertEqual(report["actions"]["cancelled_branch_churn_hints"], [
            {"branch": "agent/high-churn", "cancelled_runs": 3, "distinct_heads": 2},
            {"branch": "agent/two-heads", "cancelled_runs": 2, "distinct_heads": 2},
        ])
        narrative = markdown(report)
        self.assertIn("Review PR head churn", narrative)
        self.assertIn("NOT proof of wasted runner time", narrative)
        self.assertNotIn("unsafe|markdown", narrative)
        self.assertNotIn("same-head-only", narrative)

    def test_churn_hints_ignore_closed_and_fork_branches_only_with_complete_open_census(self):
        def event(branch, sha):
            return {"head_branch": branch, "head_sha": sha,
                    "event": "pull_request", "conclusion": "cancelled",
                    "created_at": "2026-10-21T06:00:00Z", "name": "Tooling"}

        def pr(branch, repo="gamesbyian/UR-Recomp"):
            return {"number": 501, "draft": False,
                    "title": "Tracked branch", "updated_at": "2026-10-21T11:30:00Z",
                    "head": {"ref": branch, "repo": {"full_name": repo}}}

        def fake(path):
            if "/pulls?state=open&" in path:
                return [pr("agent/still-open"), pr("agent/fork", "other/UR-Recomp")]
            if "/actions/runs?" in path:
                return {"workflow_runs": [
                    event("agent/still-open", "a" * 40),
                    event("agent/still-open", "b" * 40),
                    event("agent/merged", "c" * 40),
                    event("agent/merged", "d" * 40),
                    event("agent/fork", "e" * 40),
                    event("agent/fork", "f" * 40),
                ]}
            return self.request(path)

        report = self.report(get=fake)
        self.assertEqual(report["actions"]["cancelled_branch_scope"],
                         "complete_open_same_repo_pr_census")
        self.assertEqual(report["actions"]["cancelled_branch_churn_hints"], [
            {"branch": "agent/still-open", "cancelled_runs": 2, "distinct_heads": 2},
        ])
        self.assertNotIn("agent/merged", markdown(report))
        self.assertNotIn("agent/fork", markdown(report))

        # The live API may return an incomplete/malformed open-PR census.
        # Never infer that a historical branch closed from absent evidence.
        def incomplete(path):
            if "/pulls?state=open&" in path:
                return [dict(number=501, title="Partial", updated_at="2026-10-21T11:30:00Z")]
            return fake(path)
        report = self.report(get=incomplete)
        self.assertEqual(report["actions"]["cancelled_branch_scope"],
                         "latest_runs_only_open_pr_census_unavailable")
        self.assertEqual({x["branch"] for x in report["actions"]["cancelled_branch_churn_hints"]},
                         {"agent/still-open", "agent/merged", "agent/fork"})

    def test_workflow_names_without_cancellations_are_not_inferred_as_waste(self):
        def all_green(path):
            if "/actions/runs?" in path:
                return {"workflow_runs": [{"conclusion": "success",
                                          "name": "Windows", "created_at": "2026-10-21T06:00:00Z"}]}
            return self.request(path)
        report = self.report(get=all_green)
        self.assertEqual(report["actions"]["cancelled_by_workflow"], [])
        self.assertNotIn("Cancellation leads", markdown(report))

    def test_actions_api_failure_is_non_green_even_with_valid_main_and_prs(self):
        def no_actions(path):
            if "/actions/runs?" in path:
                raise ValueError("HTTP 403")
            return self.request(path)
        report = self.report(get=no_actions)
        self.assertIsNotNone(report["main"])
        self.assertIsNotNone(report["prs"])
        self.assertIsNone(report["actions"])
        self.assertEqual(report["errors"]["actions"], "HTTP 403")
        self.assertFalse(required_live_sources_present(report))
        self.assertIn("Actions: UNKNOWN", markdown(report))
        self.assertTrue(required_live_sources_present(self.report()))

    def test_recent_action_failure_and_old_inflight_run_have_source_leads(self):
        def incidents(path):
            if "/actions/runs?" in path:
                return {"workflow_runs": [
                    {"id": 1234, "name": "Tooling", "status": "completed",
                     "conclusion": "failure", "created_at": "2026-10-21T11:00:00Z"},
                    {"id": 5678, "name": "Windows", "status": "in_progress",
                     "conclusion": None, "created_at": "2026-10-21T08:00:00Z"},
                    {"id": 9012, "name": "Queued", "status": "queued",
                     "conclusion": None, "created_at": "2026-10-21T11:45:00Z"},
                ]}
            return self.request(path)
        report = self.report(get=incidents)
        actions = report["actions"]
        self.assertEqual([v["run_id"] for v in actions["failed_run_leads"]], [1234])
        self.assertEqual([v["run_id"] for v in actions["aging_in_flight_leads"]], [5678])
        self.assertEqual(actions["aging_in_flight_leads"][0]["age_minutes"], 240)
        narrative = markdown(report)
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/actions/runs/1234", narrative)
        self.assertIn("not proof of stalls", narrative)
        self.assertNotIn("/runs/9012", narrative)

    def test_vault_health_is_not_lost_when_latest_100_runs_omit_vault(self):
        report = self.report()
        self.assertEqual(report["recovery_workflows"]["intake"]["status"], "RECENT_SUCCESS")
        self.assertEqual(report["recovery_workflows"]["review"]["status"], "RECENT_SUCCESS")
        self.assertEqual(report["recovery_workflows"]["intake"]["run_id"], 4000)
        self.assertIn("/actions/runs/4001", markdown(report))
        self.assertTrue(required_live_sources_present(report))

    def test_manual_dispatch_does_not_mask_missing_recurring_vault_producer(self):
        def manually_green(path):
            if "/actions/workflows/" in path:
                return {"workflow_runs": [{
                    "id": 7000, "head_branch": "main",
                    "event": "workflow_dispatch",
                    "created_at": "2026-10-21T11:30:00Z",
                    "status": "completed", "conclusion": "success"}]}
            return self.request(path)
        report = self.report(get=manually_green)
        self.assertEqual(report["recovery_workflows"]["intake"]["status"],
                         "UNKNOWN_NO_ELIGIBLE_RUN")
        self.assertEqual(report["recovery_workflows"]["review"]["status"],
                         "UNKNOWN_NO_ELIGIBLE_RUN")
        self.assertFalse(required_live_sources_present(report))

    def test_newer_manual_intake_cannot_hide_stale_scheduled_intake(self):
        def restored_once(path):
            if "/actions/workflows/" in path:
                intake = "vault-recurring-intake" in path
                prior = "schedule" if intake else "workflow_run"
                return {"workflow_runs": [
                    {"id": 7001, "head_branch": "main", "event": "workflow_dispatch",
                     "created_at": "2026-10-21T11:30:00Z",
                     "status": "completed", "conclusion": "success"},
                    {"id": 7002, "head_branch": "main", "event": prior,
                     "created_at": "2026-10-20T10:00:00Z",
                     "status": "completed", "conclusion": "success"}]}
            return self.request(path)
        report = self.report(get=restored_once)
        self.assertEqual(report["recovery_workflows"]["intake"]["run_id"], 7002)
        self.assertEqual(report["recovery_workflows"]["review"]["run_id"], 7002)
        self.assertEqual(report["recovery_workflows"]["intake"]["status"], "OVERDUE_REVIEW")
        self.assertFalse(required_live_sources_present(report))

    def test_latest_intake_after_still_green_review_is_not_green_overall(self):
        def simulated(path):
            if "/actions/workflows/" in path:
                intake = "vault-recurring-intake" in path
                return {"workflow_runs": [{
                    "id": 5000 if intake else 5001,
                    "head_branch": "main",
                    "event": "schedule" if intake else "workflow_run",
                    "created_at": ("2026-10-21T11:00:00Z" if intake
                                   else "2026-10-21T10:30:00Z"),
                    "status": "completed", "conclusion": "success"}]}
            return self.request(path)
        report = self.report(get=simulated)
        self.assertEqual(report["recovery_workflows"]["intake"]["status"], "RECENT_SUCCESS")
        review = report["recovery_workflows"]["review"]
        self.assertEqual(review["status"], "UPSTREAM_NOT_REVIEWED")
        self.assertEqual(review["latest_intake_run_id"], 5000)
        self.assertIn("awaiting review after", markdown(report))
        self.assertFalse(required_live_sources_present(report))

    def test_review_newer_than_latest_intake_is_recent_without_claiming_bytes(self):
        def simulated(path):
            if "/actions/workflows/" in path:
                intake = "vault-recurring-intake" in path
                return {"workflow_runs": [{
                    "id": 6000 if intake else 6001,
                    "head_branch": "main",
                    "event": "schedule" if intake else "workflow_run",
                    "created_at": ("2026-10-21T10:00:00Z" if intake
                                   else "2026-10-21T10:01:00Z"),
                    "status": "completed", "conclusion": "success"}]}
            return self.request(path)
        report = self.report(get=simulated)
        self.assertEqual(report["recovery_workflows"]["review"]["status"], "RECENT_SUCCESS")
        self.assertTrue(required_live_sources_present(report))

    def test_vault_failure_and_overdue_are_visible_without_guessing_success(self):
        def broken(path):
            if "/actions/workflows/" in path:
                if "vault-recurring-intake" in path:
                    return {"workflow_runs": [
                        {"id": 4123, "head_branch": "feature", "event": "pull_request",
                         "created_at": "2026-10-21T11:30:00Z",
                         "status": "completed", "conclusion": "success"},
                        {"id": 4124, "head_branch": "main", "event": "schedule",
                         "created_at": "2026-10-21T11:00:00Z",
                         "status": "completed", "conclusion": "failure"}]}
                return {"workflow_runs": [
                    {"id": 4144, "head_branch": "main", "event": "workflow_run",
                     "created_at": "2026-10-20T10:00:00Z",
                     "status": "completed", "conclusion": "success"}]}
            return self.request(path)
        report = self.report(get=broken)
        self.assertEqual(report["recovery_workflows"]["intake"]["status"],
                         "RECENT_NON_SUCCESS")
        self.assertEqual(report["recovery_workflows"]["intake"]["run_id"], 4124)
        self.assertEqual(report["recovery_workflows"]["review"]["status"], "OVERDUE_REVIEW")
        self.assertIn("OVERDUE_REVIEW", markdown(report))
        self.assertFalse(required_live_sources_present(report))

    def test_unavailable_vault_workflow_api_cannot_make_ops_monitor_green(self):
        def forbidden(path):
            if "/actions/workflows/" in path:
                raise ValueError("HTTP 403")
            return self.request(path)
        report = self.report(get=forbidden)
        self.assertIsNotNone(report["main"])
        self.assertIsNotNone(report["actions"])
        self.assertIsNone(report["recovery_workflows"])
        self.assertIn("recovery_workflows", report["errors"])
        self.assertFalse(required_live_sources_present(report))
        self.assertIn("Critical Vault workflow health", markdown(report))

    def test_uncorroborated_drive_and_schedule_state_are_unknown(self):
        result = self.report()
        self.assertEqual(result["drive"], "UNKNOWN_NOT_CONNECTED")
        self.assertEqual(result["scheduled_agent_health"], "UNKNOWN_NOT_CONNECTED")
        self.assertIn("Drive presence UNKNOWN", markdown(result))

    def test_verified_closed_pr_census_surfaces_stale_handoff_without_mutation(self):
        def request(path):
            if "/pulls?state=closed&" in path:
                return [{
                    "number": 2194, "merged_at": "2026-10-21T19:55:59Z",
                    "merge_commit_sha": "d2ab0785cdd531f6fa26534c9597d7cdda484b23",
                    "body": "Independent archive 1_RScoARFTHjfttOY87v9PKBepXmE8tK8"
                }]
            return self.request(path)
        result = self.report(get=request, registry=self.handoff_fixture())
        drift = result["handoff_drift"]
        self.assertEqual(drift["status"], "REVIEW_HINTS")
        self.assertEqual(drift["hints"][0]["candidate_id"],
                         "h27-knowledge-malformed-lanes")
        self.assertEqual(drift["automatic_state_changes"], 0)
        self.assertIn("inspect every member", markdown(result))

    def test_closed_pr_handoff_scan_prioritizes_recent_updates(self):
        seen = []
        def capture(path):
            if "/pulls?state=closed&" in path:
                seen.append(path)
                return []
            return self.request(path)
        report = self.report(get=capture)
        self.assertEqual(report["handoff_drift"]["status"],
                         "NO_HINTS_IN_CURATED_SCOPE")
        self.assertEqual(len(seen), 1)
        self.assertIn("state=closed&sort=updated&direction=desc&per_page=100&page=1",
                      seen[0])

    def test_partial_closed_census_never_claims_no_stale_handoffs(self):
        def partial(path):
            if "/pulls?state=closed&" in path:
                return [{"number": x, "merged_at": None} for x in range(100)]
            return self.request(path)
        report = self.report(get=partial)
        self.assertEqual(report["handoff_drift"]["status"],
                         "UNKNOWN_INCOMPLETE_PR_CENSUS")
        self.assertEqual(report["handoff_drift"]["hints"], [])
        self.assertFalse(report["handoff_drift"]["census_complete"])

    def test_partial_census_preserves_positive_evidence_without_completeness(self):
        def partial(path):
            if "/pulls?state=closed&" in path:
                valid = {
                    "number": 2194, "merged_at": "2026-10-21T19:55:59Z",
                    "merge_commit_sha": "d2ab0785cdd531f6fa26534c9597d7cdda484b23",
                    "body": "Drive source 1_RScoARFTHjfttOY87v9PKBepXmE8tK8",
                }
                return [valid] + [
                    {"number": x, "merged_at": None} for x in range(99)
                ]
            return self.request(path)
        report = self.report(get=partial, registry=self.handoff_fixture())
        result = report["handoff_drift"]
        self.assertEqual(result["status"], "PARTIAL_CENSUS_REVIEW_HINTS")
        self.assertFalse(result["census_complete"])
        self.assertEqual(result["hints"][0]["linked_merged_pr"], 2194)
        self.assertEqual(result["automatic_state_changes"], 0)

    def test_actual_candidate_resolution_does_not_break_handoff_fixture(self):
        # The same exact merged-PR receipt must no longer be a hint once
        # the reviewed candidate is explicitly resolved.
        def source(path):
            if "/pulls?state=closed&" in path:
                return [{
                    "number": 2194,
                    "merged_at": "2026-10-21T19:55:59Z",
                    "merge_commit_sha": "d2ab0785cdd531f6fa26534c9597d7cdda484b23",
                    "body": "Archive 1_RScoARFTHjfttOY87v9PKBepXmE8tK8",
                }]
            return self.request(path)
        unresolved = self.report(get=source, registry=self.handoff_fixture("blocked"))
        resolved = self.report(get=source, registry=self.handoff_fixture("merged"))
        self.assertEqual(unresolved["handoff_drift"]["status"], "REVIEW_HINTS")
        self.assertEqual(resolved["handoff_drift"]["status"],
                         "NO_HINTS_IN_CURATED_SCOPE")
        self.assertEqual(resolved["handoff_drift"]["hints"], [])
        self.assertEqual(resolved["handoff_drift"]["automatic_state_changes"], 0)

    def test_failed_closed_census_is_unknown(self):
        result = self.report()
        self.assertEqual(result["handoff_drift"]["status"],
                         "UNKNOWN_API_OR_DATA_FAILURE")
        self.assertIn("handoff_drift", result["errors"])

    def test_current_ledger_never_credited_when_checkout_differs(self):
        result = self.report(local_head="b" * 40)
        self.assertFalse(result["qa"]["source_exact_main"])
        self.assertIn("historical ONLY", result["errors"]["qa"])
        self.assertIn("STALE / UNVERIFIED SOURCE", markdown(result))

    def test_merge_sha_cross_checks_the_registered_claim(self):
        result = self.report(registry=self.merged_receipt_fixture())
        matching = next(x for x in result["recovery"] if x["candidate_id"] == "fixture-pinned-merge")
        self.assertEqual(matching["check"], "MERGE_SHA_VERIFIED")
        def changed(path):
            if "/pulls/2110" in path:
                return {"merged_at": "2026-10-21T05:00:00Z", "merge_commit_sha": "f"*40}
            return self.request(path)
        result = self.report(get=changed, registry=self.merged_receipt_fixture())
        mismatch = next(x for x in result["recovery"] if x["candidate_id"] == "fixture-pinned-merge")
        self.assertEqual(mismatch["check"], "RECORDED_STATUS_OR_SHA_CONFLICT")

    def test_github_failure_is_unknown_not_zero(self):
        def offline(path):
            if "/pulls?state=open" in path or "/branches/main" in path:
                raise ValueError("HTTP 403")
            return self.request(path)
        result = self.report(get=offline)
        self.assertIsNone(result["main"])
        self.assertIsNone(result["prs"])
        self.assertFalse(result["qa"]["source_exact_main"])
        self.assertIn("Open PRs: UNKNOWN", markdown(result))

    def test_failed_individual_pr_read_is_not_automatic_merge(self):
        def blocked(path):
            if "/pulls/2110" in path:
                raise ValueError("HTTP 403")
            return self.request(path)
        item = next(x for x in self.report(get=blocked, registry=self.merged_receipt_fixture())["recovery"]
                    if x["candidate_id"] == "fixture-pinned-merge")
        self.assertEqual(item["check"], "UNKNOWN")

    def test_exact_page_boundary_does_not_claim_complete_census(self):
        def full_page(path):
            if "/pulls?state=open&" in path:
                return [{"number": i, "updated_at": "2026-10-21T06:00:00Z"}
                        for i in range(100)]
            return self.request(path)
        result = self.report(get=full_page)
        self.assertFalse(result["prs"]["census_complete"])
        self.assertEqual(result["prs"]["count"], 300)

    def test_historical_backup_is_never_live_drive_attestation(self):
        record = load_custody()
        report = snapshot(self.request, board=self.board, registry=self.registry,
                          ledger=self.ledger, local_head=SHA, now=NOW, custody=record)
        self.assertEqual(report["backup"]["source_commit"], record["source_commit"])
        self.assertEqual(report["backup"]["current_drive_integrity"], "UNKNOWN_NOT_CHECKED")
        self.assertFalse(report["backup"]["observed_main_exactly_in_backup"])
        self.assertIn("historical backup only", markdown(report))

    def test_invalid_record_does_not_launder_release_or_backup_claim(self):
        record = load_custody()
        record["release_qa_credit"] = True
        report = snapshot(self.request, board=self.board, registry=self.registry,
                          ledger=self.ledger, local_head=SHA, now=NOW, custody=record)
        self.assertIsNone(report["backup"])
        self.assertIn("invalid custody receipt", report["errors"]["backup"])
        self.assertIn("Drive backup:** UNKNOWN", markdown(report))

    def test_exact_backup_commit_never_implies_future_drive_readback(self):
        record = load_custody()
        def same_head(path):
            if path.endswith("/branches/main"):
                return {"commit": {"sha": record["source_commit"]}, "protected": True}
            return self.request(path)
        report = snapshot(same_head, board=self.board, registry=self.registry,
                          ledger=self.ledger, local_head=record["source_commit"],
                          now=NOW, custody=record)
        self.assertTrue(report["backup"]["observed_main_exactly_in_backup"])
        self.assertEqual(report["backup"]["current_drive_integrity"], "UNKNOWN_NOT_CHECKED")

    def test_bad_time_rejected_without_implicit_timezone(self):
        self.assertIsNone(timestamp("2026-10-21T12:00:00"))
        self.assertIsNone(timestamp("not-a-time"))
        self.assertIsNotNone(timestamp("2026-10-21T12:00:00Z"))

if __name__ == "__main__":
    unittest.main()
