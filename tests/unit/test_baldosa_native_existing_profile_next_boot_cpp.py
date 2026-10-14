#!/usr/bin/env python3
"""Existing-profile NEXT-BOOT selector: full production C++ codec integration.

Pure headless product acceptance only. This does NOT mean that the Baldosa
native root exposes a user-facing selector, changes live cartridge SRAM, or
has passed physical gamepad/release QA.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class NativeNextBootProfileSwitchTests(unittest.TestCase):
    def test_validated_two_profile_next_boot_selection_never_touches_raw_sram(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        paths = [
            ROOT / "tests/native/baldosa_native_existing_profile_next_boot_test.cpp",
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
            exe = Path(directory) / "existing-next-boot"
            cmd = [
                compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-pthread", "-I", str(PRODUCT),
                *map(str, paths), "-o", str(exe)
            ]
            built = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            finished = subprocess.run(
                [str(exe)], cwd=directory,
                capture_output=True, text=True, timeout=40)
            self.assertEqual(
                finished.returncode, 0, finished.stderr + finished.stdout)
            self.assertIn("PASS: next-boot named P1 selection", finished.stdout)

    def test_only_selector_published_and_live_guest_has_no_call(self):
        header = (PRODUCT / "baldosa_native_existing_profile_next_boot.hpp"
                  ).read_text(encoding="utf-8")
        for expected in (
            "TournamentLaunchPathLock selector_lock",
            "TournamentLaunchPathLock catalog_lock",
            "TournamentLaunchPathLock first_lock",
            "TournamentLaunchPathLock second_lock",
            "catalog_entry_matches_profile_state",
            "stock_sram_format_signature_present",
            "baldosa_sram_file_matches_exact",
            "save_host_product_state_file(selector.string(), next)",
            "next.active_profile_id = std::string(requested_profile)",
            "expected_active_profile == requested_profile",
            "next_profile_id",
        ):
            self.assertIn(expected, header)
        self.assertNotIn("save_host_product_state_file_if_current(", header)
        self.assertNotIn("RtlWriteSram", header)
        self.assertNotIn("RtlSetSaveRoot", header)
        self.assertNotIn("g_sram", header)
        self.assertNotIn("fs::remove_all", header)
        native_root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        self.assertNotIn(
            "select_baldosa_existing_profile_for_next_boot(", native_root)
        self.assertIn("next process", header.lower())


if __name__ == "__main__":
    unittest.main()
