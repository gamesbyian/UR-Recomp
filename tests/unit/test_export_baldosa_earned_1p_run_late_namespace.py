"""ROM-free negative: staging must recheck the *whole* earned-run namespace.

Provenance: independent current-main follow-up to archived Records H27
Drive 1mBKQcLSf3SQV8TZRvP6J78N_JJhFTuTr and #2103. The original
colon-sibling case was already resolved on main before this test; this
exercise adds the previously absent *late staging* mutation boundary.
Synthetic POSIX filenames are not evidence of an NTFS ADS exploit.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import export_baldosa_earned_1p_run as exporter


class LateNamespaceMutationTests(unittest.TestCase):
    def exercise(self, added_names: tuple[str, ...], *, expected_error: str | None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            journey = root / "journey"
            runs = journey / "Brand New Player With Spaces" / "runs" / "mike"
            runs.mkdir(parents=True)
            source = runs / "source.urrun"
            source.write_bytes(b"bounded synthetic source, not earned gameplay")
            report = {
                "scope": exporter.SOURCE_SCOPE,
                "first_game_created_first_named_racer": True,
                "second_game_loaded_named_sram_and_finished_real_source_race": True,
                "third_game_reopened_exact_earned_run_read_only": True,
                "active_selector_and_catalog_preserved": True,
                "anonymous_sram_preserved": True,
                "physical_gamepad_verified": False,
                "strict_original_native_event_pass": False,
                "release_gate_credit": 0,
                "one_canonical_run_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
            (journey / "report.json").write_text(json.dumps(report), encoding="utf-8")
            destination = root / "published"
            original_dump = exporter.json.dump
            injected = []

            def add_after_copy(*args, **kwargs):
                # Called after the source read and staged-member readbacks,
                # but before the existing final report/run/namespace checks.
                self.assertFalse(injected, "manifest was unexpectedly written twice")
                injected.append(True)
                for name in added_names:
                    (runs / name).write_bytes(b"late synthetic directory entry")
                return original_dump(*args, **kwargs)

            with patch.object(exporter.json, "dump", side_effect=add_after_copy):
                if expected_error is not None:
                    with self.assertRaisesRegex(ValueError, expected_error):
                        exporter.export(journey, destination)
                else:
                    result = exporter.export(journey, destination)
                    self.assertEqual(result["source_run_filename"], "source.urrun")
            self.assertEqual(injected, [True])
            if expected_error is not None:
                self.assertFalse(destination.exists(), "invalid namespace was published")
                self.assertFalse(list(root.glob(".pending-earned-1p-*")),
                                 "abandoned staging directory")
            else:
                self.assertEqual((destination / "earned.urrun").read_bytes(),
                                 source.read_bytes())

    @unittest.skipIf(os.name == "nt", "POSIX-only invalid Win32 filename fixtures")
    def test_late_nonportable_siblings_are_refused(self):
        for name in ("shadow:stream.urrun", "AUX.txt", "bad|sidecar",
                     "trailing.", "decomposed-e\u0301.txt"):
            with self.subTest(name=repr(name)):
                self.exercise((name,), expected_error="Nonportable sibling in earned-run namespace")

    @unittest.skipIf(os.name == "nt", "POSIX-only Win32 case alias fixture")
    def test_late_win32_casefold_collision_is_refused(self):
        self.exercise(("notes.txt", "NOTES.TXT"),
                      expected_error="Win32-colliding sibling in earned-run namespace")

    def test_late_portable_unrelated_sibling_remains_allowed(self):
        self.exercise(("notes.txt",), expected_error=None)


if __name__ == "__main__":
    unittest.main()
