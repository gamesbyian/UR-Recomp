"""Reject drift, missing files and false release claims in an artifact copy."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_retained_owner_playtest as mod

WORKFLOW = ROOT / ".github/workflows/retain-nominated-owner-playtest.yml"


class NominationRetentionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.zip = self.root / mod.ZIP
        self.zip.write_bytes(b"Fixture, not a real game")
        (self.root / (mod.ZIP + ".sha256")).write_text(
            mod.CANDIDATE_SHA256 + "  " + mod.ZIP + "\n", encoding="ascii")
        self.prov = {
            "schema": "ur-windows-romfree-playtest-provenance/1",
            "source_commit": mod.SOURCE_COMMIT,
            "zip_sha256": mod.CANDIDATE_SHA256,
            "tested_and_packaged_executable_sha256": mod.EXE_SHA256,
            "fixture_sha256": "1" * 64,
            "github_release_tag": "playtest-" + mod.SOURCE_COMMIT[:12],
            "accepted_original_native_complete_events": 0,
            "independent_release_gates_accepted": 0,
            "physical_gamepad_or_audio_verified": False,
            "release_gate_credit": 0,
            "candidate_only": True,
            "not_a_certified_beta": True,
        }
        self.save_provenance()
        (self.root / "RELEASE-NOTES.md").write_text(
            "Provisional ROM-free source " + mod.SOURCE_COMMIT +
            " original ZIP " + mod.CANDIDATE_SHA256, encoding="utf-8")
        self.audit_result = {
            "all_immutable_members_verified": True,
            "rom_bundled": False,
            "profile_data_bundled": False,
            "exe_sha256": mod.EXE_SHA256,
        }

    def save_provenance(self):
        (self.root / "PLAYTEST-PROVENANCE.json").write_text(
            json.dumps(self.prov), encoding="utf-8")

    def validated(self):
        with (mock.patch.object(mod, "sha256", return_value=mod.CANDIDATE_SHA256),
              mock.patch.object(mod.candidate_audit, "inspect",
                                return_value=self.audit_result) as audit):
            output = mod.validate(self.root)
            audit.assert_called_once_with(
                self.zip, expected_revision=mod.SOURCE_COMMIT,
                expected_zip_sha256=mod.CANDIDATE_SHA256)
            return output

    def test_preserves_one_exact_original_and_zero_release_credit(self):
        result = self.validated()
        self.assertEqual(result["original_run_id"], 38813101482)
        self.assertEqual(result["original_artifact_id"], 12009612842)
        self.assertFalse(result["new_candidate_nominated"])
        self.assertFalse(result["github_release_created"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_extra_or_missing_files_refused(self):
        (self.root / "save.srm").write_bytes(b"private data")
        with self.assertRaisesRegex(ValueError, "four-file"):
            self.validated()
        (self.root / "save.srm").unlink()
        (self.root / "RELEASE-NOTES.md").unlink()
        with self.assertRaisesRegex(ValueError, "four-file"):
            self.validated()

    def test_symlink_and_tampered_sidecar_refused(self):
        (self.root / "RELEASE-NOTES.md").unlink()
        (self.root / "RELEASE-NOTES.md").symlink_to(self.zip)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.validated()
        (self.root / "RELEASE-NOTES.md").unlink()
        (self.root / "RELEASE-NOTES.md").write_text(
            "provisional " + mod.SOURCE_COMMIT + mod.CANDIDATE_SHA256)
        (self.root / (mod.ZIP + ".sha256")).write_text(
            "0" * 64 + "  " + mod.ZIP, encoding="ascii")
        with self.assertRaisesRegex(ValueError, "sidecar"):
            self.validated()

    def test_relabelled_source_hash_and_claimed_certification_refused(self):
        for key, bad in (
            ("source_commit", "deadbeef"),
            ("zip_sha256", "0" * 64),
            ("tested_and_packaged_executable_sha256", "f" * 64),
            ("release_gate_credit", 1),
            ("not_a_certified_beta", False),
            ("physical_gamepad_or_audio_verified", True),
        ):
            with self.subTest(key=key):
                prior = self.prov[key]
                self.prov[key] = bad
                self.save_provenance()
                with self.assertRaisesRegex(ValueError, "noncertification"):
                    self.validated()
                self.prov[key] = prior
                self.save_provenance()

    def test_inner_executable_rom_and_profile_data_refused(self):
        for key, bad in (
            ("exe_sha256", "0" * 64),
            ("rom_bundled", True),
            ("profile_data_bundled", True),
            ("all_immutable_members_verified", False),
        ):
            with self.subTest(key=key):
                prior = self.audit_result[key]
                self.audit_result[key] = bad
                with self.assertRaisesRegex(ValueError, "embedded candidate"):
                    self.validated()
                self.audit_result[key] = prior

    def test_single_ubuntu_copy_no_scheduled_build_or_publishing(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "run-id: 38813101482", "artifact-ids: 12009612842",
            "retention-days: 90", "actions: read", "runs-on: ubuntu-22.04",
            ".github/workflows/retain-nominated-owner-playtest.yml",
        ):
            self.assertIn(expected, content)
        for prohibited in (
            "runs-on: windows-", "  schedule:", "  push:",
            "gh release", "publish_provisional_preview",
        ):
            self.assertNotIn(prohibited, content)


if __name__ == "__main__":
    unittest.main()
