"""Read-only source-bound agent integration control regression tests."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import agent_release_control as m

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
OTHER = "b" * 40

def snapshot():
    return {
        "schema": "UR-GITHUB-PR-SNAPSHOT/1", "repository": "gamesbyian/UR-Recomp",
        "main_sha": SHA, "open_census_complete": True,
        "closed_census_complete": False, "closed_prs_sample": [
            {"number": 3, "created_at": "2026-10-20T00:00:00Z",
             "merged_at": "2026-10-20T02:00:00Z"}],
        "open_prs": [
            {"number": 10, "title": "Approved candidate", "head_sha": OTHER,
             "base_sha": SHA, "draft": False, "mergeable_state": "clean",
             "files": ["tools/foo.py"], "files_complete": True,
             "checks_complete": True,
             "checks": [{"head_sha": OTHER, "name": "unit",
                         "status": "completed", "conclusion": "success"}]},
            {"number": 11, "title": "Draft", "head_sha": OTHER,
             "base_sha": OTHER, "draft": True, "mergeable_state": "dirty",
             "files": ["tools/foo.py"], "files_complete": True,
             "checks_complete": True, "checks": []},
        ],
    }

class AgentReleaseControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())

    def test_bound_advisory_integration(self):
        view = m.assess(snapshot(), self.ledger, "release-qa", "QA-04")
        self.assertEqual(view["release"]["decision"],
                         "HOLD_independent_source_zip_hardware_and_gameplay_review")
        self.assertEqual(view["release"]["passed_recorded"], 0)
        self.assertTrue(view["open_prs"][0]["integration_review_candidate"])
        self.assertFalse(view["open_prs"][1]["integration_review_candidate"])
        self.assertEqual(view["open_prs"][0]["overlaps_with"], [11])
        self.assertEqual(view["integration_metrics"]["sample_median_creation_to_merge_hours"], 2)
        self.assertIn("zero gate credit", m.markdown(view))

    def test_check_states_do_not_promote_stale_or_pending(self):
        record = snapshot()["open_prs"][0]
        for checks, expected in [
            ([{"head_sha": SHA, "status": "completed", "conclusion": "success"}], "unknown"),
            ([{"head_sha": OTHER, "status": "in_progress", "conclusion": None}], "pending"),
            ([{"head_sha": OTHER, "status": "completed", "conclusion": "failure"}], "failed"),
            ([], "unknown"),
        ]:
            with self.subTest(state=expected):
                record["checks"] = checks
                self.assertEqual(m.checks_state(checks, True, OTHER), expected)

    def test_missing_census_and_attachments_not_silent_success(self):
        s = snapshot()
        s["open_census_complete"] = False
        s["open_prs"][0]["files_complete"] = False
        view = m.assess(s, self.ledger, "ci")
        self.assertFalse(view["open_census_complete"])
        self.assertIsNone(view["open_prs"][0]["overlaps_with"])
        self.assertFalse(view["open_prs"][0]["integration_review_candidate"])

    def test_no_duplicate_pr_and_no_cross_lane_gate(self):
        s = snapshot()
        s["open_prs"][1]["number"] = 10
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.assess(s, self.ledger, "release-qa")
        with self.assertRaisesRegex(ValueError, "gate outside"):
            m.assess(snapshot(), self.ledger, "racer-hd", "QA-02")

    def test_indexed_evidence_stays_source_bound_and_diagnostic(self):
        receipt = {"schema": "UR-CI-UNIT-RESULT/1", "source_sha": SHA,
                   "digest": "c" * 64, "outcome": "pass",
                   "observed": 1, "failures": 0, "missing": 0, "release_gate_credit": 0}
        result = m.assess(snapshot(), self.ledger, "ci", receipts=[receipt])
        self.assertEqual(len(result["indexed_main_producer_receipts"]), 1)
        for changed in ({**receipt, "source_sha": OTHER},
                        {**receipt, "release_gate_credit": 1}):
            with self.assertRaisesRegex(ValueError, "receipt"):
                m.assess(snapshot(), self.ledger, "ci", receipts=[changed])

    def test_recorded_release_change_distinct_from_merged_pr_sample(self):
        import hashlib
        from tools.release_evidence_brief import briefing
        older = briefing(self.ledger, source_sha=OTHER)
        older["ledger_file_sha256"] = "a" * 64
        current_sha = "b" * 64
        view = m.assess(snapshot(), self.ledger, "release-qa",
                        previous_brief=older, ledger_digest=current_sha)
        delta = view["recorded_release_status_delta"]
        self.assertEqual(delta["state"],
                         "diagnostic_only_not_independent_gate_adjudication")
        self.assertEqual(delta["passed_status_change"], 0)
        self.assertTrue(delta["ledger_bytes_changed"])
        self.assertEqual(view["integration_metrics"]["merged_sample_count"], 1)
        self.assertIn("not independent QA", m.markdown(view))
        older["checked_source_commit"] = None
        with self.assertRaisesRegex(ValueError, "previous brief missing"):
            m.assess(snapshot(), self.ledger, "release-qa",
                     previous_brief=older, ledger_digest=current_sha)

    def test_ci_cost_sampling_is_explicit(self):
        ci = {"schema_version": 3, "window_census_complete": False,
              "workflows": [{"workflow": "Windows", "runner_seconds": 100,
                             "runs_missing_job_timing": 1}]}
        result = m.assess(snapshot(), self.ledger, "ci", ci=ci)
        self.assertEqual(result["ci_cost"]["coverage"], "sample_only")
        self.assertEqual(result["ci_cost"]["observed_top_workflows"][0]["missing_job_timing"], 1)

    def test_existing_ops_reader_is_used_without_second_http_client(self):
        from unittest.mock import MagicMock
        getter = MagicMock(return_value={"commit": {"sha": SHA}})
        with patch.object(m, "github_reader", return_value=getter) as reader:
            result = m.api("gamesbyian/UR-Recomp",
                           "repos/gamesbyian/UR-Recomp/branches/main")
        self.assertEqual(result["commit"]["sha"], SHA)
        reader.assert_called_once()
        getter.assert_called_once_with("/repos/gamesbyian/UR-Recomp/branches/main")
        with self.assertRaisesRegex(ValueError, "foreign API"):
            m.api("gamesbyian/UR-Recomp", "repos/other/repo/branches/main")

    def test_live_ledger_preflight_rejects_stale_or_dirty_checkout(self):
        import subprocess
        from unittest.mock import MagicMock
        def completed(stdout):
            return MagicMock(stdout=stdout)
        with patch.object(m.subprocess, "run", side_effect=[
            completed("b" * 40 + "\n"), completed("")]):
            with self.assertRaisesRegex(ValueError, "differ"):
                m.require_local_main(SHA)
        with patch.object(m.subprocess, "run", side_effect=[
            completed(SHA + "\n"), completed(" M docs/RELEASE-QUALITY-LEDGER.json")]):
            with self.assertRaisesRegex(ValueError, "modified"):
                m.require_local_main(SHA)
        with patch.object(m.subprocess, "run", side_effect=[
            completed(SHA + "\n"), completed("")]):
            m.require_local_main(SHA)

    def test_live_pr_head_change_and_valid_snapshot(self):
        pr = {"number": 10, "title": "One", "head": {"sha": OTHER},
              "base": {"sha": SHA}, "draft": False}
        responses = [
            {"commit": {"sha": SHA}}, [pr], [{"filename": "tools/a.py"}],
            {"check_runs": [], "total_count": 0},
            {"head": {"sha": SHA}, "base": {"sha": SHA}, "mergeable_state": "clean"},
        ]
        with patch.object(m, "api", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "PR advanced"):
                m.live_snapshot()
        responses[4]["head"]["sha"] = OTHER
        responses.extend([[], [pr], {"commit": {"sha": SHA}}])
        with patch.object(m, "api", side_effect=responses):
            got = m.live_snapshot()
        self.assertEqual(got["main_sha"], SHA)
        self.assertEqual(len(got["open_prs"]), 1)
        changed = {**pr, "head": {"sha": SHA}}
        with patch.object(m, "api", side_effect=responses[:-2] + [[changed],
                {"commit": {"sha": SHA}}]):
            with self.assertRaisesRegex(ValueError, "changed during census"):
                m.live_snapshot()
        with patch.object(m, "api", side_effect=responses[:-2] + [[pr, changed],
                {"commit": {"sha": SHA}}]):
            with self.assertRaisesRegex(ValueError, "changed during census"):
                m.live_snapshot()


if __name__ == "__main__":
    unittest.main()
