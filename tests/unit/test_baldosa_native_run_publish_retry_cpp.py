#!/usr/bin/env python3
"""The existing native result handoff retries only a live stock result receipt."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BaldosaNativePublishRetryTests(unittest.TestCase):
    def test_bounded_1p_retry_and_session_revocation(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "baldosa-run-retry"
            built = subprocess.run([
                compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                "-Werror", "-pedantic",
                "-I", str(ROOT / "native/product"),
                "-I", str(ROOT / "native/title"),
                str(ROOT / "tests/native/baldosa_native_run_publish_retry_test.cpp"),
                "-o", str(binary),
            ], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: Baldosa native run receipt retry", run.stdout)

    def test_live_native_result_hook_uses_existing_canonical_publisher(self):
        source = (ROOT / "tools/baldosa_native_pause_lifecycle.cpp").read_text(
            encoding="utf-8")
        self.assertIn("g_pending_one_player_run.ready_for_retry(", source)
        self.assertIn("ur_baldosa_modern_publish_settled_one_player_run(retry)", source)
        self.assertIn("g_pending_one_player_run.defer_failed_publication(", source)
        self.assertIn("g_pending_one_player_run.reset();", source)
        self.assertNotIn("append_completed_run_record(", source)
        self.assertNotIn("RtlWriteSram(", source)


if __name__ == "__main__":
    unittest.main()
