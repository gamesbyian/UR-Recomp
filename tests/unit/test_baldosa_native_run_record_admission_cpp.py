#!/usr/bin/env python3
"""Native result must pass original Records codec admission without writing."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"
TITLE = ROOT / "native/title"


class BaldosaNativeRunRecordAdmissionTests(unittest.TestCase):
    def test_result_to_canonical_codec_is_fail_closed(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "record-admission"
            sources = [
                ROOT / "tests/native/baldosa_native_run_record_admission_test.cpp",
                PRODUCT / "baldosa_native_run_record_admission.cpp",
                PRODUCT / "completed_run_record.cpp",
                PRODUCT / "completed_run_store.cpp",
            ]
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(PRODUCT),
                 "-I", str(TITLE), *map(str, sources), "-o", str(binary)],
                text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0,
                             build.stdout + build.stderr)
            run = subprocess.run(
                [str(binary)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn(
                "PASS: source-settled Baldosa results admit only canonical",
                run.stdout)

    def test_no_publication_and_distinct_backend_replay_identity(self):
        source = (
            PRODUCT / "baldosa_native_run_record_admission.cpp"
        ).read_text(encoding="utf-8")
        header = (
            PRODUCT / "baldosa_native_run_record_admission.hpp"
        ).read_text(encoding="utf-8")
        self.assertIn("validate_completed_run_record(record)", source)
        self.assertIn("observed.captured_input_frames", source)
        self.assertIn("ordinary_two_player_carrier_elapsed_ticks60", source)
        self.assertIn("authority.multiplayer_participants_bound", source)
        self.assertIn("selected_named_profile_verified", source)
        self.assertIn("baldosa-10b864b9d14a7b7416dd909eb7b054c88faef101",
                      header)
        self.assertNotIn("save_completed_run_record_file", source)
        self.assertNotIn("append_completed_run_record", source)
        self.assertNotIn("RtlWriteSram", source)


if __name__ == "__main__":
    unittest.main()
