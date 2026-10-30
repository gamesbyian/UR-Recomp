"""Provenance checks for the Windows Restart audio source package."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.ci.check_windows_audio_source_binding import verify_source_binding

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/ci/check_windows_audio_source_binding.py"
SHA = "a" * 40
OTHER_SHA = "b" * 40


class WindowsAudioSourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manifest = Path(self.temp.name) / "PACKAGE-MANIFEST.json"

    def write(self, content):
        self.manifest.write_text(json.dumps(content), encoding="utf-8")

    def test_matching_exact_commit(self):
        self.write({"schema_version": 1, "source_revision": SHA})
        self.assertEqual(verify_source_binding(self.manifest, SHA), SHA)

    def test_rejects_other_valid_commit(self):
        self.write({"schema_version": 1, "source_revision": OTHER_SHA})
        with self.assertRaisesRegex(ValueError, "source revision mismatch"):
            verify_source_binding(self.manifest, SHA)

    def test_rejects_truncated_or_malformed_selected_commit(self):
        self.write({"source_revision": SHA})
        for invalid in (SHA[:12], SHA.upper(), "", None, "g" * 40):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "40 lowercase"):
                verify_source_binding(self.manifest, invalid)

    def test_rejects_missing_or_nonstring_manifest_revision(self):
        for payload in ({}, {"source_revision": None}, {"source_revision": 123}):
            with self.subTest(payload=payload):
                self.write(payload)
                with self.assertRaisesRegex(ValueError, "source revision mismatch"):
                    verify_source_binding(self.manifest, SHA)

    def test_rejects_absent_malformed_and_nonobject_manifest(self):
        with self.assertRaisesRegex(ValueError, "cannot read"):
            verify_source_binding(self.manifest, SHA)
        self.manifest.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cannot read"):
            verify_source_binding(self.manifest, SHA)
        self.write([{"source_revision": SHA}])
        with self.assertRaisesRegex(ValueError, "must be an object"):
            verify_source_binding(self.manifest, SHA)

    def test_cli_fails_closed_and_prints_producer_identity(self):
        self.write({"source_revision": SHA})
        good = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(self.manifest),
             "--expected-source-sha", SHA], text=True, capture_output=True, check=False,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn("PASS source_sha=" + SHA, good.stdout)
        bad = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(self.manifest),
             "--expected-source-sha", OTHER_SHA], text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("source revision mismatch", bad.stderr)

    def test_workflow_binds_after_package_verify(self):
        workflow_path = ROOT / ".github/workflows/windows-modern-restart-audio-probe.yml"
        if not workflow_path.is_file():
            self.skipTest("repository workflow unavailable in local source-only preflight")
        workflow = workflow_path.read_text(encoding="utf-8")
        verify = workflow.index('python tools/assemble_windows_package.py verify --package "$PACKAGE"')
        bind = workflow.index('python tools/ci/check_windows_audio_source_binding.py')
        self.assertLess(verify, bind)
        self.assertIn('--expected-source-sha "${{ steps.source-package.outputs.source_sha }}"', workflow)
        self.assertIn('"tools/ci/check_windows_audio_source_binding.py"', workflow)
        self.assertIn('"tests/unit/test_windows_audio_source_binding.py"', workflow)


if __name__ == "__main__":
    unittest.main()
