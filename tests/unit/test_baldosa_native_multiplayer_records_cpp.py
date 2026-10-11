#!/usr/bin/env python3
"""Compile canonical 2P match/Records codecs for native read-only product UI."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class BaldosaNativeMultiplayerRecordsTests(unittest.TestCase):
    def test_source_bound_pairs_and_profile_scoped_history(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler")
        sources = [
            ROOT / "tests/native/baldosa_native_multiplayer_records_summary_test.cpp",
            PRODUCT / "baldosa_native_multiplayer_records_summary.cpp",
            PRODUCT / "multiplayer_match_catalog.cpp",
            PRODUCT / "multiplayer_match_summary.cpp",
            PRODUCT / "multiplayer_match_record.cpp",
            PRODUCT / "local_multiplayer_match_binding.cpp",
            PRODUCT / "completed_run_record.cpp",
            PRODUCT / "completed_run_store.cpp",
            PRODUCT / "host_profile_runtime.cpp",
            PRODUCT / "host_product_state.cpp",
            PRODUCT / "output_resolution_policy.cpp",
            PRODUCT / "modern_racer_identity.cpp",
        ]
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "2p-records"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(PRODUCT),
                 "-I", str(ROOT / "native/title"),
                 *map(str, sources), "-o", str(binary)],
                text=True, capture_output=True,
            )
            self.assertEqual(built.returncode, 0,
                             built.stdout + built.stderr)
            checked = subprocess.run(
                [str(binary)], text=True, capture_output=True,
            )
            self.assertEqual(checked.returncode, 0,
                             checked.stdout + checked.stderr)
            self.assertIn("PASS: Baldosa native Records reads only paired",
                          checked.stdout)

    def test_native_root_reuses_existing_catalog_and_painter(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        stage = (ROOT / "tools/baldosa_modern_profile_activation_spike.py"
                 ).read_text(encoding="utf-8")
        self.assertIn(
            "inspect_baldosa_native_two_player_records_archive(", source)
        self.assertIn("select_records_page(!g_records_two_player)", source)
        self.assertIn("g_records_two_player, true", source)
        self.assertNotIn("save_multiplayer_match_record", source)
        for name in ("baldosa_native_multiplayer_records_summary.cpp",
                     "multiplayer_match_catalog.cpp",
                     "multiplayer_match_summary.cpp",
                     "multiplayer_match_record.cpp",
                     "local_multiplayer_match_binding.cpp"):
            self.assertIn(name, stage)


if __name__ == "__main__":
    unittest.main()
