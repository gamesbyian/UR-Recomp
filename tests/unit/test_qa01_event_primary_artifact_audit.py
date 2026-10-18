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
    frames = [0, 1, 2, 4, 8, 16, 32, 100]
    original_rows = [
        {"relative_frame": f, "menu": 0x16, "p1_laps": 2, "in_race": 1}
        for f in frames
    ]
    native_rows = [dict(row) for row in original_rows]
    if not matched:
        native_rows[-1]["p1_laps"] = 1
    first = None if matched else {
        "relative_frame": 100, "fields": ["p1_laps"],
        "reference": {"p1_laps": 2},
        "native": {"p1_laps": 1},
    }
    terminal = {
        "onset": {"menu": 0x18, "in_race": 0x3C},
        "result": {"menu": 0x18, "in_race": 0x3C},
        "result_text": {"final": ["MIKE", "123"]},
    }
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
        "relative_sample_frames": frames,
        "reference": {"samples": original_rows, **terminal},
        "native": {"samples": native_rows, **terminal},
        "original_source_vs_fresh_entry": {
            "fresh_reference_native_equivalent": True,
            "source_original_state_equivalent": True,
        },
        "reference_entry": 984, "native_entry": 986, "native_frame_shift": 2,
        "comparison": {
            "paired_event_candidate": matched,
            "fresh_guest_entry_equivalent": True,
            "original_source_entry_equivalent": True,
            "terminal_result_frame_matched": matched,
            "terminal_result_guest_frame": {
                "reference_relative": rel,
                "native_relative": rel if matched else rel - 1,
            },
            "first_sample_disagreement": first,
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
        (self.folder / "SHA256SUMS").write_text(
            "c" * 64 + "  snesref\n"
            + "a" * 64 + "  native\n"
            + "a" * 64 + "  snes9x_libretro.so\n",
            encoding="ascii",
        )

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

    def test_missing_and_malformed_shared_binary_manifest_fail_closed(self):
        manifest = self.folder / "SHA256SUMS"
        initial = manifest.read_text(encoding="ascii")
        manifest.unlink()
        self.assertFalse(self.inspect()["primary_artifact_audit_complete"])
        self.assertIn("manifest", self.inspect()["cases"][0]["reason"].lower())
        for modified in (
            initial.replace("  snesref", "  ../snesref"),
            initial.replace("  native", " *native"),
            initial.replace("snes9x_libretro.so", "native"),
            initial.replace("a" * 64, "A" * 64),
            initial.rstrip("\n"),
        ):
            with self.subTest(modified=modified[:32]):
                manifest.write_text(modified, encoding="ascii")
                self.assertFalse(self.inspect()["primary_artifact_audit_complete"])

    def test_case_cannot_claim_replaced_native_or_snes9x_binary(self):
        for name in ("native_executable_sha256", "reference_core_sha256"):
            with self.subTest(name=name):
                original = campaign.load_json(self.primary)
                original[name] = "d" * 64
                campaign.write_json(self.primary, original)
                # Recreate a superficially self-consistent case receipt.
                campaign.write_json(self.receipt, campaign.classify(
                    "bowl", 0, self.primary, self.plan))
                observed = self.inspect()
                self.assertFalse(observed["primary_artifact_audit_complete"])
                self.assertIn("executable identities", observed["cases"][0]["reason"])
                self.put_case(matched=True)

    def test_multi_case_same_original_binary_manifest_required(self):
        self.plan = campaign.make_plan("all", "b" * 40)
        for case in ("zoom-zoo", "switcher"):
            folder = self.root / ("qa01-campaign-case-" + case)
            folder.mkdir()
            raw = folder / "producer-report.json"
            campaign.write_json(raw, producer(case, matched=True))
            receipt = campaign.classify(case, 0, raw, self.plan)
            campaign.write_json(folder / "case-result.json", receipt)
            (folder / "SHA256SUMS").write_bytes(
                (self.folder / "SHA256SUMS").read_bytes())
        # Existing synthetic Bowl was classified using the single-case plan.
        campaign.write_json(self.receipt, campaign.classify(
            "bowl", 0, self.primary, self.plan))
        self.assertTrue(self.inspect(with_aggregate=True)["primary_artifact_audit_complete"])
        switched = self.root / "qa01-campaign-case-switcher" / "SHA256SUMS"
        switched.write_text(switched.read_text().replace(
            "c" * 64 + "  snesref", "d" * 64 + "  snesref"))
        broken = self.inspect()
        self.assertFalse(broken["primary_artifact_audit_complete"])
        self.assertIn("do not share", broken["cases"][-1]["reason"])

    def test_real_strict_divergence_is_valid_negative_evidence(self):
        self.put_case(matched=False)
        observed = self.inspect(with_aggregate=True)
        self.assertTrue(observed["primary_artifact_audit_complete"])
        self.assertEqual(observed["cases"][0]["disposition"], "strict_divergence")
        self.assertEqual(observed["release_admissions"], 0)

    def test_unrecorded_sample_is_invalid_even_with_rehashed_coherent_receipt(self):
        altered = campaign.load_json(self.primary)
        altered["native"]["samples"].pop()
        campaign.write_json(self.primary, altered)
        # Existing campaign transport classifier consumes derived predicates;
        # the primary-artifact checker must reject omitted raw observations.
        row = campaign.classify("bowl", 0, self.primary, self.plan)
        campaign.write_json(self.receipt, row)
        observed = self.inspect()
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertIn("sample frames", observed["cases"][0]["reason"])

    def test_forged_first_difference_is_invalid_even_when_rehashed(self):
        self.put_case(matched=False)
        altered = campaign.load_json(self.primary)
        altered["comparison"]["first_sample_disagreement"]["reference"]["p1_laps"] = 123
        campaign.write_json(self.primary, altered)
        row = campaign.classify("bowl", 1, self.primary, self.plan)
        campaign.write_json(self.receipt, row)
        observed = self.inspect()
        self.assertFalse(observed["primary_artifact_audit_complete"])
        self.assertIn("first sampled divergence", observed["cases"][0]["reason"])

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
