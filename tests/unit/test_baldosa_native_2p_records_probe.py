#!/usr/bin/env python3
"""Strict log admission for a real played Baldosa 2P pair and new-game history.

These fixture strings test the observer only. They are NOT real match evidence.
"""
from pathlib import Path
import sys
import unittest
import subprocess
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_2p_records_probe as probe


def settled_log() -> str:
    return (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=native-ci-rider "
        "profile2=native-ci-second course=course:01 frames=40000 "
        "path=pair.urrun\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
        "race_host=1900 result_host=39700 riders=0,2 "
        "hundredths=2900,60000 winner=1 "
        "input_frames=37799 input_runs=6 published=1\n"
    )


def records_log() -> str:
    return (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 "
        "profile=selected validated=0 unavailable=0\n"
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 "
        "unavailable=0 selected=1\n"
        "UR_BALDOSA_MODERN_ROOT records_page=2p\n"
        "UR_BALDOSA_MODERN_ROOT records_last_2p=LAST 01 WIN 00:29.00 "
        "source=historical_paired_archive\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
    )


class NativeTwoPlayerRecordsProbe(unittest.TestCase):

    def test_native_two_player_cold_records_log_preserves_unicode_paths(self):
        # The production run_guest decoder must handle actual raw UTF-8
        # bytes from the Windows game, not cp1252-decoded mojibake.
        name = "user_2p_漢字-🚲"
        source = (
            "import sys; "
            "sys.stdout.buffer.write('2P record=" + name +
            "\\n'.encode('utf-8')); "
            "sys.stderr.buffer.write('2P archive=" + name +
            "\\n'.encode('utf-8'))"
        )
        real_run = subprocess.run
        def emit(_args, **kwargs):
            return real_run([sys.executable, "-c", source], **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(probe.subprocess, "run", side_effect=emit) as invoked:
                log = probe.run_guest(
                    root / "native.exe", root / "original.sfc",
                    root / "cold", root / name,
                    script="turbo on\\nwait 1\\nquit\\n",
                    smoke="1", timeout=15, video="dummy")
                self.assertEqual(invoked.call_args.kwargs["encoding"], "utf-8")
                self.assertEqual(invoked.call_args.kwargs["errors"], "replace")
            self.assertEqual(log.count(name), 2)
            self.assertNotIn("�", log)
            self.assertEqual(
                (root / "cold" / "log.txt").read_text(encoding="utf-8"), log)

    def test_reuses_stock_two_player_go_and_pinned_drive(self):
        from baldosa_windows_native_pause_route import (
            native_modern_race_entry_script,
        )
        s = probe.source_match_script()
        original = native_modern_race_entry_script(2)
        self.assertTrue(s.startswith(original.removesuffix("dump go\nquit\n")))
        self.assertIn("until16 0053 == 8610", s)
        self.assertIn("until 0E1F != 00", s)
        for step in probe.SOURCE_TWO_PLAYER_DRIVE:
            self.assertIn(step, s)
        self.assertEqual(s.count(f"wait {probe.AFTER_DRIVE_WAIT}"), 1)
        self.assertNotIn("until 009F", s)
        self.assertTrue(s.endswith("dump after-source-2p-drive\nquit\n"))

    def test_committed_guest_pair_requires_two_confirmed_stock_riders(self):
        observed = probe.source_match_published(settled_log())
        self.assertEqual(observed["p1_hundredths"], 2900)
        self.assertEqual(observed["p2_hundredths"], 60000)
        for invalid in (
            settled_log().replace("riders=0,2", "riders=1,0"),
            settled_log().replace("published=1", "published=0"),
            settled_log().replace("course=course:01", "course=course:02"),
            settled_log().replace("result_host=39700", "result_host=1500"),
            settled_log().replace("input_frames=37799", "input_frames=0"),
            settled_log().replace("winner=1", "winner=9"),
            settled_log().replace("join_confirmed seat=2", "join_rejected seat=2"),
            settled_log().replace("CAPTURED=1", "NOT_SAVED=1"),
            settled_log() + settled_log(),
            settled_log() + "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1\n",
        ):
            with self.subTest(invalid=invalid[-100:]):
                with self.assertRaises(ValueError):
                    probe.source_match_published(invalid)

    def test_fresh_native_records_are_one_read_only_bound_pair(self):
        probe.source_paired_records_reopened(records_log())
        for invalid in (
            records_log().replace("paired=1", "paired=0"),
            records_log().replace("selected=1", "selected=0"),
            records_log().replace("unavailable=0 selected", "unavailable=1 selected"),
            records_log().replace("records_page=2p", "records_page=1p"),
            records_log().replace("records_last_2p=", "no_latest="),
            records_log() + records_log(),
            records_log() + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
        ):
            with self.subTest(invalid=invalid[-100:]):
                with self.assertRaises(ValueError):
                    probe.source_paired_records_reopened(invalid)

    def test_fixture_uses_existing_product_stores_without_switching_p1(self):
        fixture = (ROOT / "tools/baldosa_modern_profile_native_fixture.cpp").read_text(
            encoding="utf-8")
        self.assertIn('"--add-second-keep-first"', fixture)
        self.assertIn("bool activate_second = true", fixture)
        self.assertIn("if (activate_second)", fixture)
        self.assertIn('selected=%s sram=%zu distinct=1', fixture)


if __name__ == "__main__":
    unittest.main()
