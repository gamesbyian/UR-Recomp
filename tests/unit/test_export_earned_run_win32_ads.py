"""Native Windows ADS discriminator for the earned 1P Records exporter.

Issue #2103. Unlike synthetic POSIX colon filenames, these cases exercise
actual Win32 named-stream behavior on a filesystem supporting ADS. This is
bounded source/evidence QA, not a physical-device or release-gate verdict.

The exporter currently validates visible directory entries, not hidden NTFS
named streams. Keep the refusal check an expected failure until the source
implements an independently reviewed policy. Do not turn this into a passing
release claim merely because Linux skips it.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from export_baldosa_earned_1p_run import SOURCE_SCOPE, export


@unittest.skipUnless(os.name == "nt", "requires genuine Win32 named streams")
class Win32NamedStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(strict=True)
        self.journey = self.root / "journey"
        self.runs = self.journey / "Brand New Player With Spaces" / "runs" / "mike"
        self.runs.mkdir(parents=True)
        self.run = self.runs / "source.urrun"
        self.payload = b"synthetic Windows stream probe; not earned gameplay"
        self.run.write_bytes(self.payload)
        report = {
            "scope": SOURCE_SCOPE,
            "first_game_created_first_named_racer": True,
            "second_game_loaded_named_sram_and_finished_real_source_race": True,
            "third_game_reopened_exact_earned_run_read_only": True,
            "active_selector_and_catalog_preserved": True,
            "anonymous_sram_preserved": True,
            "physical_gamepad_verified": False,
            "strict_original_native_event_pass": False,
            "release_gate_credit": 0,
            "one_canonical_run_sha256": hashlib.sha256(self.payload).hexdigest(),
        }
        (self.journey / "report.json").write_text(json.dumps(report), encoding="utf-8")

    def add_named_stream(self) -> None:
        # On FAT/exFAT or a filesystem that does not support NTFS ADS, do not
        # mistake an unsupported operation for an exporter policy result.
        self.stream = Path(str(self.run) + ":agent3-probe")
        try:
            self.stream.write_bytes(b"synthetic alternate data stream")
            observed = self.stream.read_bytes()
        except OSError as exc:
            self.skipTest(f"named streams unsupported on this Windows volume: {exc}")
        if observed != b"synthetic alternate data stream":
            self.skipTest("named stream did not round-trip as an NTFS stream")
        self.assertEqual(self.run.read_bytes(), self.payload)

    def test_clean_source_exports_before_named_stream_is_added(self) -> None:
        receipt = export(self.journey, self.root / "clean")
        self.assertEqual(receipt["source_run_filename"], "source.urrun")
        self.assertEqual((self.root / "clean" / "earned.urrun").read_bytes(),
                         self.payload)

    def test_named_stream_is_invisible_to_win32_directory_iteration(self) -> None:
        self.add_named_stream()
        self.assertEqual([entry.name for entry in self.runs.iterdir()],
                         ["source.urrun"])
        self.assertEqual(self.stream.read_bytes(), b"synthetic alternate data stream")

    @unittest.expectedFailure
    def test_export_must_refuse_hidden_named_stream(self) -> None:
        # Red-first requirement, not a claim that the current exporter passes.
        # A future implementation should reject this before publishing any
        # evidence, and this expectedFailure decorator must then be removed.
        self.add_named_stream()
        destination = self.root / "should-not-publish"
        with self.assertRaisesRegex(ValueError, "(?i)alternate.*stream|named.*stream"):
            export(self.journey, destination)
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
