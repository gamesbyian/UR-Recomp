#!/usr/bin/env python3
"""Short-raw recovery captures must not weaken normal SRAM evidence."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from baldosa_win32_interactive_recovery_q import snapshot


class RecoverySnapshotRawLengthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / "saves/profile-native-ci-rider/save.srm"
        self.raw.parent.mkdir(parents=True)
        (self.root / "host-state-v1.txt").write_bytes(b"selector")
        (self.root / "profiles-v1.txt").write_bytes(b"catalog")
        (self.raw.parent / "host-profile.txt").write_bytes(b"typed")

    def test_normal_snapshot_enforces_8192_and_reads_all_canonical_files(self):
        self.raw.write_bytes(b"r" * 8192)
        observed = snapshot(self.root)
        self.assertEqual(len(observed["raw"]), 8192)
        self.assertEqual(observed["selector"], b"selector")
        self.assertEqual(observed["catalog"], b"catalog")
        self.assertEqual(observed["typed"], b"typed")

    def test_synthetic_513_byte_snapshot_requires_explicit_opt_in(self):
        self.raw.write_bytes(b"r" * 513)
        with self.assertRaisesRegex(ValueError, "8192 bytes"):
            snapshot(self.root)
        self.assertEqual(snapshot(self.root, expected_raw_bytes=513)["raw"],
                         b"r" * 513)

    def test_short_witness_still_checks_exact_length_and_missing_files(self):
        self.raw.write_bytes(b"r" * 512)
        with self.assertRaisesRegex(ValueError, "513 bytes"):
            snapshot(self.root, expected_raw_bytes=513)
        self.raw.write_bytes(b"r" * 8192)
        with self.assertRaisesRegex(ValueError, "513 bytes"):
            snapshot(self.root, expected_raw_bytes=513)
        (self.root / "profiles-v1.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or redirected"):
            snapshot(self.root, expected_raw_bytes=513)

    def test_other_sizes_may_not_bypass_canonical_validation(self):
        self.raw.write_bytes(b"r" * 600)
        with self.assertRaisesRegex(ValueError, "Unsupported recovery snapshot"):
            snapshot(self.root, expected_raw_bytes=600)


if __name__ == "__main__":
    unittest.main()
