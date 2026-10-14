#!/usr/bin/env python3
"""Exhaustive stock 16-first/15-second rider profile product-codec census.

This compiles and runs the real C++ Modern codecs, not a synthetic encoding
or native SDL frontend. Does not claim gamepad hardware, 16 UI flows,
original-emulator parity or release QA credit.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class NativeStockPresetCensusTests(unittest.TestCase):
    def test_full_isolated_source_stock_preset_roster(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        paths = [
            ROOT / "tests/native/baldosa_native_stock_preset_census_test.cpp",
            *[PRODUCT / name for name in (
                "clean_stock_sram.cpp",
                "output_resolution_policy.cpp",
                "host_product_state.cpp",
                "host_product_store.cpp",
                "host_profile_runtime.cpp",
                "host_profile_state.cpp",
                "host_profile_store.cpp",
                "host_profile_catalog.cpp",
                "modern_racer_identity.cpp",
            )],
        ]
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "preset-census"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-pthread", "-I", str(PRODUCT),
                 *map(str, paths), "-o", str(binary)],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            run = subprocess.run([str(binary)], cwd=folder,
                                 capture_output=True, text=True, timeout=45)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: 16 first-racer and 15 independent second-racer",
                          run.stdout)
            self.assertIn("P1 selector preservation", run.stdout)

    def test_no_own_profile_format_or_guest_memory_seeding(self):
        source = (ROOT / "tests/native/baldosa_native_stock_preset_census_test.cpp"
                  ).read_text(encoding="utf-8")
        self.assertIn("for (std::size_t n = 0; n < presets.size(); ++n)", source)
        self.assertIn("for (std::size_t n = 1; n < presets.size(); ++n)", source)
        self.assertIn("source[0x0748] = identity->rider_index;", source)
        self.assertIn("create_baldosa_second_preset_for_next_boot", source)
        self.assertIn("create_baldosa_first_preset_for_next_boot", source)
        self.assertIn("require_stock_racer", source)
        self.assertNotIn("RtlWriteSram", source)
        self.assertNotIn("g_sram", source)
        self.assertNotIn("UR_BALDOSA_NATIVE_RESULT observed=1", source)


if __name__ == "__main__":
    unittest.main()
