"""Proof that original QA artifact wrappers remain byte-identical and unpromoted."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_retained_windows_qa_artifacts as mod


class OriginalEvidencePreservationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.entries = []
        for i in sorted(mod.QA_IDS):
            path = self.root / f"{i}.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("report.txt", f"fixture for {i}")
            self.entries.append([i, mod.digest(path)])
        self.report = {
            "schema": "qa-exact-main-38813101482-independent-cross-artifact/1",
            "workflow_run": mod.RUN,
            "candidate": {"source_commit": mod.SOURCE,
                          "portable_zip_sha256": mod.ZIP_SHA},
            "assertions": {"full_qa_gate_witnesses": 0,
                           "strict_original_native_usa_events_accepted": 0},
            "outer_artifacts": [[mod.OWNER_ID, "a" * 64], *self.entries],
        }

    def pins(self):
        return mod.pins(self.report)

    def test_verified_original_wrappers_and_zero_release_credit(self):
        self.assertEqual(len(self.pins()), 9)
        output = mod.verify_wrappers(self.root, self.pins())
        self.assertEqual(output["original_run"], 38813101482)
        self.assertEqual(output["candidate_zip_sha256"], mod.ZIP_SHA)
        self.assertFalse(output["new_windows_executable_compiled"])
        self.assertEqual(output["release_gate_credit"], 0)

    def test_refuse_extra_or_missing_archive(self):
        extra = self.root / "Uniracers_USA.sfc"
        extra.write_bytes(b"not a real ROM")
        with self.assertRaisesRegex(ValueError, "missing/extra"):
            mod.verify_wrappers(self.root, self.pins())
        extra.unlink()
        (self.root / f"{self.entries[0][0]}.zip").unlink()
        with self.assertRaisesRegex(ValueError, "missing/extra"):
            mod.verify_wrappers(self.root, self.pins())

    def test_refuse_modified_original_wrapper(self):
        (self.root / f"{self.entries[0][0]}.zip").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "original wrapper changed"):
            mod.verify_wrappers(self.root, self.pins())

    def test_refuse_wrong_artifact_identity_or_source(self):
        self.report["outer_artifacts"][1][0] = 1234
        with self.assertRaisesRegex(ValueError, "identity"):
            self.pins()
        self.report["outer_artifacts"][1][0] = self.entries[0][0]
        self.report["candidate"]["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source/ZIP"):
            self.pins()

    def test_no_new_qa_gate_or_incorrect_outer_digest(self):
        self.report["assertions"]["full_qa_gate_witnesses"] = 1
        with self.assertRaisesRegex(ValueError, "certified"):
            self.pins()
        self.report["assertions"]["full_qa_gate_witnesses"] = 0
        self.report["outer_artifacts"][1][1] = "0" * 63
        with self.assertRaisesRegex(ValueError, "malformed"):
            self.pins()

    def test_bounded_safe_archive_contents(self):
        target = self.root / f"{self.entries[0][0]}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("../escape", "bad")
        expected = [[n, mod.digest(self.root / f"{n}.zip")]
                    for n in sorted(mod.QA_IDS)]
        with self.assertRaisesRegex(ValueError, "unsafe original wrapper member"):
            mod.verify_wrappers(self.root, expected)


if __name__ == "__main__":
    unittest.main()
