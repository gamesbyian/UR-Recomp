"""Manual multi-suite campaign evidence is identity bound and release-neutral."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_modern_batch_campaign as campaign  # noqa: E402
from assemble_windows_package import write_archive_checksum  # noqa: E402


SOURCE = "a" * 40
NATIVE_DIGEST = "b" * 64
PASS = dict.fromkeys(("native", "shared", "onboarding", "ui", "windows"), "success")


class ManualCampaignTest(unittest.TestCase):
    def test_all_existing_suites_pass_without_awarding_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "UR-Recomp-Windows-x64.zip"
            sidecar = root / (archive.name + ".sha256")
            archive.write_bytes(b"exact sample ZIP identity")
            digest = write_archive_checksum(archive, sidecar)
            result = campaign.make_receipt(
                source_sha=SOURCE, run_id="1234", states=PASS,
                include_windows=True, native_sha256=NATIVE_DIGEST,
                windows_zip=archive, windows_checksum=sidecar,
            )
        self.assertEqual(result["disposition"], "component_suites_passed")
        self.assertEqual(result["candidate"]["windows_portable_zip_sha256"], digest)
        self.assertEqual(result["qa01_accepted_courses"], 0)
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertFalse(result["physical_hardware_witness"])
        self.assertIn("distinct legacy-backend", campaign.render_summary(result))

    def test_windows_opt_out_is_not_a_missing_required_suite(self):
        states = {**PASS, "windows": "skipped"}
        result = campaign.make_receipt(
            source_sha=SOURCE, run_id="9", states=states,
            include_windows=False, native_sha256=NATIVE_DIGEST,
        )
        self.assertEqual(result["disposition"], "component_suites_passed")
        self.assertIsNone(result["candidate"]["windows_portable_zip_sha256"])

    def test_failure_and_incomplete_are_separate(self):
        for status, expected in (("failure", "suite_failure"),
                                 ("skipped", "incomplete"),
                                 ("cancelled", "incomplete")):
            with self.subTest(status=status):
                states = {**PASS, "shared": status, "windows": "skipped"}
                result = campaign.make_receipt(
                    source_sha=SOURCE, run_id="10", states=states,
                    include_windows=False, native_sha256=NATIVE_DIGEST,
                )
                self.assertEqual(result["disposition"], expected)

    def test_successful_build_without_digest_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "lacks its SHA-256"):
            campaign.make_receipt(
                source_sha=SOURCE, run_id="42", states={**PASS, "windows": "skipped"},
                include_windows=False,
            )

    def test_windows_success_without_exact_zip_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing its portable ZIP"):
            campaign.make_receipt(
                source_sha=SOURCE, run_id="42", states=PASS,
                include_windows=True, native_sha256=NATIVE_DIGEST,
            )

    def test_corrupt_sidecar_never_yields_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "UR-Recomp-Windows-x64.zip"
            sidecar = root / (archive.name + ".sha256")
            archive.write_bytes(b"first bytes")
            write_archive_checksum(archive, sidecar)
            archive.write_bytes(b"changed bytes")
            with self.assertRaisesRegex(ValueError, "does not match"):
                campaign.make_receipt(
                    source_sha=SOURCE, run_id="42", states=PASS,
                    include_windows=True, native_sha256=NATIVE_DIGEST,
                    windows_zip=archive, windows_checksum=sidecar,
                )

    def test_cli_retains_invalid_evidence_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = [sys.executable, str(ROOT / "tools/qa_modern_batch_campaign.py"),
                    "--source-sha", SOURCE, "--run-id", "7",
                    "--native", "success", "--shared", "success",
                    "--onboarding", "success", "--ui", "success",
                    "--windows", "skipped", "--include-windows", "false",
                    "--out", str(root / "report.json"),
                    "--summary", str(root / "summary.md")]
            done = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(done.returncode, 2, done.stderr)
            saved = json.loads((root / "report.json").read_text())
            self.assertEqual(saved["disposition"], "evidence_invalid")
            self.assertEqual(saved["release_gate_credit"], 0)
            self.assertIn("Evidence contract failure", (root / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
