#!/usr/bin/env python3
"""Compile the real product-store codecs for first-racer next-boot authority."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class NativeFirstModernRacerTests(unittest.TestCase):
    def test_first_create_is_canonical_non_overwriting_and_next_boot_only(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        files = [
            ROOT / "tests/native/baldosa_native_first_profile_test.cpp",
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
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "first-racer"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra", "-Werror",
                 "-pedantic", "-pthread", "-I", str(PRODUCT),
                 *map(str, files), "-o", str(exe)],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True,
                cwd=directory, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: first Modern preset creation", run.stdout)
            self.assertIn("PASS: second named stock racer uses canonical", run.stdout)

    def test_native_root_requires_next_boot_and_source_guest_unchanged(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        activation = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text()
        presenter = (PRODUCT / "modern_root_overlay_presenter.hpp").read_text()
        self.assertIn("ur_baldosa_modern_create_first_preset", activation)
        self.assertIn("create_baldosa_first_preset_for_next_boot", activation)
        self.assertIn("g_first_racer_created = true;", root)
        self.assertIn("g_named_profile_stale = true;", root)
        self.assertIn("activation=next_process", root)
        self.assertIn("case SDLK_x:", root)
        self.assertIn("case kGamepadBtn_X:", root)
        # The original first-racer modal remains visible; P2 shares the
        # existing view only when the distinct second-racer modal is open.
        self.assertIn(
            "g_first_racer_open || g_second_racer_open || g_existing_switch_open;",
            root)
        self.assertIn("view.first_racer_is_second = g_second_racer_open;", root)
        self.assertIn("if (view.first_racer_open)", presenter)
        self.assertNotIn("RtlRunFrame(", root)
        self.assertNotIn("RtlWriteSram(", root)


if __name__ == "__main__":
    unittest.main()
