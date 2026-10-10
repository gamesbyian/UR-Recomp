#!/usr/bin/env python3
"""Real C++ coverage of native read-only Records via the shipping codec."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BaldosaNativeRecordsTests(unittest.TestCase):
    def test_canonical_store_and_selected_profile_archive(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler available")
        product = ROOT / "native/product"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "records-reader"
            cmd = [
                compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-I", str(ROOT),
                "-I", str(product),
                str(ROOT / "tests/native/baldosa_native_records_summary_test.cpp"),
                str(product / "baldosa_native_records_summary.cpp"),
                str(product / "completed_run_store.cpp"),
                str(product / "completed_run_record.cpp"),
                "-o", str(target),
            ]
            built = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(built.returncode, 0,
                             built.stdout + built.stderr)
            checked = subprocess.run(
                [str(target)], text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0,
                             checked.stdout + checked.stderr)
            self.assertIn("PASS: native Records reads only canonical",
                          checked.stdout)

    def test_native_root_never_publishes_or_replays_from_records(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        self.assertIn("inspect_baldosa_native_records_archive", root)
        self.assertIn("g_records_open", root)
        self.assertIn("UR_BALDOSA_MODERN_ROOT records_opened=1", root)
        self.assertNotIn("append_completed_run_record(", root)
        self.assertNotIn("RtlRunFrame(", root)
        self.assertNotRegex(root, r"g_ram\[0x009f\]\s*=(?!=)")
        stage = (ROOT / "tools/baldosa_modern_profile_activation_spike.py"
                 ).read_text(encoding="utf-8")
        for name in ("completed_run_store.cpp", "completed_run_record.cpp",
                     "baldosa_native_records_summary.cpp"):
            self.assertIn(name, stage)


if __name__ == "__main__":
    unittest.main()
