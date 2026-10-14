#!/usr/bin/env python3
"""Pure contract tests for one real Win32 source-event product probe.

These synthetic log strings ONLY test admission, never constitute an event.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_1p_records_probe as probe


class NativeOnePlayerRecordsProbeTests(unittest.TestCase):
    def test_source_route_reuses_existing_guest_stock_entry(self):
        from baldosa_windows_native_pause_route import (
            native_modern_race_entry_script,
        )
        parent = native_modern_race_entry_script(1)
        script = probe.source_finish_script()
        self.assertTrue(script.startswith(parent.removesuffix("dump go\nquit\n")))
        self.assertIn("until16 0053 == 8610", script)
        self.assertIn("until 0E1F != 00", script)
        self.assertNotIn("until 009F == 99 12000", script)
        self.assertEqual(script.count("press right 1200"), 1)
        self.assertTrue(script.endswith("dump after-source-drive\nquit\n"))

    def test_real_result_requires_one_committed_guest_provenance(self):
        complete = (
            "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
            "profile=native-ci-rider course=course:01 "
            "input_frames=1300 inputs=2 path=one.urrun\n"
            "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
            "race_host=500 result_host=2000 finish_ticks60=740 "
            "input_frames=1500 input_runs=2 published=1\n"
        )
        probe.source_result_published(complete)
        for broken in (
            complete.replace("published=1", "published=0"),
            complete.replace("finish_ticks60=740", "finish_ticks60=0"),
            complete.replace("course=course:01", "course=course:02"),
            complete.replace("race_host=500", "race_host=2500"),
            complete + complete,
            complete + "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1\n",
            complete.replace("UR_BALDOSA_NATIVE_RUN CAPTURED=1", "MISSING"),
        ):
            with self.subTest(broken=broken[-140:]):
                with self.assertRaises(ValueError):
                    probe.source_result_published(broken)

    def test_fresh_game_records_must_be_read_only_and_exact(self):
        complete = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
            "root=saves/profile-native-ci-rider\n"
            "UR_BALDOSA_MODERN_ROOT records_opened=1 "
            "profile=selected validated=1 unavailable=0\n"
        )
        probe.native_records_reopened(complete)
        for broken in (
            complete.replace("validated=1", "validated=0"),
            complete.replace("unavailable=0", "unavailable=1"),
            complete + complete,
            complete + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        ):
            with self.subTest(broken=broken):
                with self.assertRaises(ValueError):
                    probe.native_records_reopened(broken)


if __name__ == "__main__":
    unittest.main()
