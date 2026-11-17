#!/usr/bin/env python3
"""Pure ZIP and CI-wiring checks for the source-bound Win32 crash seam."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from assemble_baldosa_windows_candidate import EXE, PREFIX, LAUNCHER, README, MANIFEST
import qa02_exact_owner_win32_seam as qa


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


class SourceBoundCrashSeamTests(unittest.TestCase):
    def make_candidate(self, root: Path, *, duplicate: bool = False):
        package = root / "candidate.zip"
        payload = b"MZ-source-bound-payload"
        names = [PREFIX + x for x in (EXE, LAUNCHER, README, MANIFEST)]
        with zipfile.ZipFile(package, "w") as z:
            for name in sorted(names):
                z.writestr(name, payload if name == PREFIX + EXE else b"fixture")
            if duplicate:
                z.writestr(PREFIX + EXE, payload)
        binding = root / "identity.json"
        binding.write_text(json.dumps({
            "source_sha": "a" * 40,
            "zip_sha256": sha(package.read_bytes()),
            "exe_sha256": sha(payload),
        }), encoding="utf-8")
        return package, binding, payload

    def test_exact_packaged_pe_identity_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, binding, payload = self.make_candidate(root)
            target = root / "extract"
            target.mkdir()
            exe = qa.extract_source_bound(package, target, binding)
            self.assertEqual(exe.read_bytes(), payload)
            self.assertEqual(qa.digest(exe), sha(payload))

    def test_tamper_and_duplicate_members_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, binding, _ = self.make_candidate(root)
            package.write_bytes(package.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "ZIP does not match"):
                qa.extract_source_bound(package, root, binding)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, binding, _ = self.make_candidate(root, duplicate=True)
            with self.assertRaisesRegex(ValueError, "Duplicate or corrupt"):
                qa.extract_source_bound(package, root, binding)

    def test_hosted_workflow_runs_seam_after_package_binding_and_keeps_bytes(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text("utf-8")
        binding = workflow.index("name: Bind journeys to the nominated ZIP and executable hashes")
        seam = workflow.index("name: QA-02 source-bound packaged PE crash seam")
        archive = workflow.index("name: Retain QA-02 packaged PE crash seam evidence")
        self.assertLess(binding, seam)
        self.assertLess(seam, archive)
        self.assertIn("--candidate-zip", workflow[seam:archive])
        self.assertIn("--candidate-receipt", workflow[seam:archive])
        self.assertIn('--rom "reference/roms/retail/Uniracers_USA.sfc"', workflow[seam:archive])
        self.assertIn("qa02-source-bound-crash-seam-20261117", workflow[seam:archive])
        self.assertIn("native_post_raw_pre_typed_crash/seam", workflow[archive:archive + 800])


if __name__ == "__main__":
    unittest.main()
