#!/usr/bin/env python3
"""Compile the established title readers under Baldosa's new result bridge."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"
TITLE = ROOT / "native/title"


class BaldosaGuestResultObserverTests(unittest.TestCase):
    def test_native_observer_compiles_real_title_readers(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("No available C++17 compiler")
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "guest-observer"
            sources = [
                ROOT / "tests/native/baldosa_guest_result_observer_test.cpp",
                PRODUCT / "baldosa_guest_result_observer.cpp",
                TITLE / "uniracers_run_data.cpp",
                TITLE / "uniracers_two_player_result.cpp",
            ]
            compile_run = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(PRODUCT),
                 "-I", str(TITLE), *map(str, sources), "-o", str(exe)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                compile_run.returncode, 0,
                compile_run.stdout + compile_run.stderr)
            executed = subprocess.run(
                [str(exe)], capture_output=True, text=True)
            self.assertEqual(executed.returncode, 0,
                             executed.stdout + executed.stderr)
            self.assertIn(
                "PASS: source-backed Baldosa native result bridge",
                executed.stdout)

    def test_real_host_result_ownership_and_no_publisher(self):
        source = (ROOT / "tools/baldosa_native_pause_lifecycle.cpp").read_text()
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        observer = (PRODUCT / "baldosa_guest_result_observer.cpp").read_text()
        staging = (ROOT / "tools/baldosa_product_pause_spike.py").read_text()
        self.assertIn("g_native_result_observer.observe(", source)
        self.assertIn("ur_baldosa_modern_root_guest_players()", source)
        self.assertIn("published=0", source)
        self.assertIn("g_handed_off_players = static_cast<unsigned>(players);", root)
        self.assertIn("g_handed_off_players = 0;", root)
        self.assertIn("observe_ordinary_two_player_race_result(", observer)
        self.assertIn("ur_uniracers_line_snapshot_ticks60(", observer)
        self.assertNotIn("save_completed_run", observer)
        self.assertNotIn("RtlRunFrame", observer)
        self.assertIn("uniracers_two_player_result.cpp", staging)
        self.assertIn("uniracers_run_data.cpp", staging)


if __name__ == "__main__":
    unittest.main()
