#!/usr/bin/env python3
"""2P match receipt retry is source-observed and never creates a guest result."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class BaldosaNativeTwoPlayerMatchRetryTests(unittest.TestCase):
    def test_source_and_profiles_do_not_drift_during_bounded_retry(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "native-two-player-retry"
            result = subprocess.run([
                compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-I", str(ROOT / "native/product"),
                "-I", str(ROOT / "native/title"),
                str(ROOT / "tests/native/baldosa_native_match_publish_retry_test.cpp"),
                "-o", str(binary),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            outcome = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(outcome.returncode, 0,
                             outcome.stderr + outcome.stdout)
            self.assertIn("PASS: 2P source-result", outcome.stdout)

    def test_native_bridge_only_retries_real_source_bound_match(self):
        source = (ROOT / "tools/baldosa_native_pause_lifecycle.cpp").read_text(
            encoding="utf-8")
        self.assertIn("g_pending_two_player_match.ready_for_retry(", source)
        self.assertIn("ur_baldosa_modern_root_source_bound_2p_profiles(", source)
        self.assertIn("observe_ordinary_two_player_race_result(", source)
        self.assertIn("g_pending_two_player_match.defer_failed_publication(",
                      source)
        self.assertIn("g_pending_two_player_match.reset();", source)
        self.assertIn("ur_baldosa_modern_publish_settled_two_player_match(",
                      source)
        self.assertIn("SAVE_ABANDONED=1", source)
        self.assertIn("SAVE_RETRY status=%s", source)
        self.assertIn("ur_baldosa_modern_root_set_run_save_feedback(", source)
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        self.assertIn("stock_result_still_visible", root)
        self.assertIn("g_handed_off_players == 2u", root)
        self.assertIn("ur::title::kOrdinaryTwoPlayerRaceResultMenu", root)
        self.assertIn("render_baldosa_native_run_save_feedback(", root)
        self.assertNotIn("append_multiplayer_match_pair(", source)
        self.assertNotIn("RtlWriteSram(", source)

if __name__ == "__main__":
    unittest.main()
