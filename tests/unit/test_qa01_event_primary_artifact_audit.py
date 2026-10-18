"""ROM-free negative tests for actual QA-01 case and aggregate artifact integrity."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_event_campaign as campaign
import qa01_event_primary_artifact_audit as receipts


def producer(case: str, *, matched: bool) -> dict:
    rel = 5163
    return {
        "schema_version": 1, "name": case,
        "course_id": campaign.CASES[case]["course_id"],
        "family": campaign.CASES[case]["family"],
        "native_backend": "pinned-baldosa",
        "admission": "investigative candidate; not a release-ledger pass",
        "original_source_event": {
            "original_entry_frame": 3190,
            "original_result_frame": 3190 + rel,
            "source_active_frames_to_result": rel,
        },
        "reference_entry": 984, "native_entry": 986, "native_frame_shift": 2,
        "comparison": {
            "paired_event_candidate": matched,
            "terminal_result_frame_matched": matched,
            "terminal_result_guest_frame": {
                "reference_relative": rel,
                "native_relative": rel if matched else rel - 1,
            },
            "first_sample_disagreement": None if matched else {"relative_frame": 100},
            **{gate: True for gate in campaign.STRICT_PRODUCER_GATES},
            "diagnostic_exit_success_without_full_event_parity": False,
        },
        **{key: "a" * 64 for key in (
            "rom_sha256", "original_movie_sha256", "native_executable_sha256",
            "reference_core_sha256", "input_sha256", "source_sram_sha256",
            "original_movie_window_sha256", "reference_script_sha256")},
    }


class PrimaryArtifactAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = campaign.make_plan("bowl", "b" * 40)
        self.folder = self.root / "qa01-campaign-case-bowl"
        self.folder.mkdir()
        self.primary = self.folder / "producer-report.json"
        self.receipt = self.folder / "case-result.json"
        self.put_case(matched=True)

    def put_case(self, *, matched: bool):
        campaign.write_json(self.primary, producer("bowl", matched=matched))
        row = campaign.classify("bowl", 0 if matched else 1,
                                self.primary, self.plan)
        campaign.write_json(self.receipt, row)

    def inspect(self, with_aggregate: bool = False):
        aggregate = campaign.aggregate(self.plan, self.root)[0] if with_aggregate else None
        return receipts.audit(self.plan, self.root, aggregate)

    def test_positive_primary_and_aggregate_are_transport_only(self):
        observed = self.inspect(with_aggregate=True)
        self.assertTrue(observed["primary_artifact_audit_complete"])
        self.assertEqual(observed["release_admissions"], 0)
        self.assertEqual(observed["primary_receipts_verified"], 1)
        self.assertTrue(observed["campaign_aggregate_matches_sources"])
        self.assertEqual(observed["cases"][0]["disposition"], "strict_candidate")

    def test_real_strict_divergence_is_valid_negative_evidence(self):
        self.put_case(matched=False)
        observed = self.inspect(with_aggregate=True)
        self.assertTrue(observed["primary_artifact_audit_complete"])
        self.assertEqual(observed["cases"][0]["disposition"], "strict_divergence")
        self.assertEqual(observed["release_admissions"], 0)

    def test_missing_primary_denied_even_when_summary_is_complete(self):
        self.primary.unlink()
        observed = self.inspect(with_aggregate=True)
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertIn("missing original", observed["cases"][0]["reason"])

    def test_modified_primary_after_classification_denied(self):
        obj = json.loads(self.primary.read_text())
        obj["reference_entry"] += 1
        campaign.write_json(self.primary, obj)
        observed = self.inspect()
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertIn("SHA-256", observed["cases"][0]["reason"])

    def test_rehashed_but_forged_case_receipt_denied(self):
        row = campaign.load_json(self.receipt)
        row["reason"] = "independently accepted game!"
        campaign.write_json(self.receipt, row)
        observed = self.inspect()
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertIn("recomputed", observed["cases"][0]["reason"])

    def test_invalid_exit_and_missing_receipt_denied(self):
        row = campaign.load_json(self.receipt)
        row["producer_exit_code"] = True
        campaign.write_json(self.receipt, row)
        self.assertFalse(self.inspect()["primary_artifact_audit_complete"])
        self.receipt.unlink()
        self.assertFalse(self.inspect()["primary_artifact_audit_complete"])

    def test_unexpected_directory_and_tampered_aggregate_denied(self):
        self.folder.parent.joinpath("qa01-campaign-case-unsolicited").mkdir()
        self.assertFalse(self.inspect()["primary_artifact_audit_complete"])
        self.assertEqual(self.inspect()["unexpected_case_directories"],
                         ["qa01-campaign-case-unsolicited"])
        self.folder.parent.joinpath("qa01-campaign-case-unsolicited").rmdir()
        published, _ = campaign.aggregate(self.plan, self.root)
        published["release_admissions"] = 1
        observed = receipts.audit(self.plan, self.root, published)
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertFalse(observed["campaign_aggregate_matches_sources"])


if __name__ == "__main__":
    unittest.main()
