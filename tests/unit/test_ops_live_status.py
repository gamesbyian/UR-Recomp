"""Live ops report must expose API loss, stale evidence and bounded sampling."""
from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, REGISTRY, extract_board, load_json
from ops_live_status import markdown, snapshot, timestamp
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

    def test_live_main_and_recency_are_explicit(self):
        result = self.report()
        self.assertTrue(result["main"]["protected"])
        self.assertEqual(result["prs"]["count"], 1)
        self.assertTrue(result["prs"]["census_complete"])
        self.assertEqual(result["prs"]["unchanged_48h_count"], 1)
        self.assertTrue(result["qa"]["source_exact_main"])

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

    def test_workflow_names_without_cancellations_are_not_inferred_as_waste(self):
        def all_green(path):
            if "/actions/runs?" in path:
                return {"workflow_runs": [{"conclusion": "success",
                                          "name": "Windows", "created_at": "2026-10-21T06:00:00Z"}]}
            return self.request(path)
        report = self.report(get=all_green)
        self.assertEqual(report["actions"]["cancelled_by_workflow"], [])
        self.assertNotIn("Cancellation leads", markdown(report))

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
        result = self.report()
        matching = next(x for x in result["recovery"] if x["candidate_id"] == "h27-qa01-sparse-transition")
        self.assertEqual(matching["check"], "MERGE_SHA_VERIFIED")
        def changed(path):
            if "/pulls/2110" in path:
                return {"merged_at": "2026-10-21T05:00:00Z", "merge_commit_sha": "f"*40}
            return self.request(path)
        result = self.report(get=changed)
        mismatch = next(x for x in result["recovery"] if x["candidate_id"] == "h27-qa01-sparse-transition")
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
        item = next(x for x in self.report(get=blocked)["recovery"]
                    if x["candidate_id"] == "h27-qa01-sparse-transition")
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
