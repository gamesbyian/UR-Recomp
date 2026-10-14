#!/usr/bin/env python3
"""Actual existing Modern profile/CAS/store codecs admit native 2P pairs."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"

class BaldosaNativeTwoPlayerPublicationTests(unittest.TestCase):
    def test_profile_authority_and_canonical_pair_publication(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        sources = [
            ROOT / "tests/native/baldosa_modern_profile_activation_test.cpp",
            ROOT / "tools/baldosa_modern_profile_activation.cpp",
            *[PRODUCT / filename for filename in (
                "output_resolution_policy.cpp",
                "clean_stock_sram.cpp", // activation now supports new first-racer boot
                "host_product_state.cpp",
                "host_product_store.cpp",
                "host_profile_runtime.cpp",
                "host_profile_state.cpp",
                "host_profile_store.cpp",
                "host_profile_catalog.cpp",
                "modern_racer_identity.cpp",
                "completed_run_record.cpp",
                "completed_run_store.cpp",
                "baldosa_native_run_record_admission.cpp",
                "local_multiplayer_match_binding.cpp",
                "multiplayer_match_record.cpp",
                "multiplayer_match_catalog.cpp",
            )],
        ]
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "native-two-player-append"
            command = [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                       "-Werror", "-pedantic", "-pthread",
                       "-I", str(PRODUCT),
                       "-I", str(ROOT / "native/title"),
                       *map(str, sources), "-o", str(binary)]
            built = subprocess.run(command, capture_output=True, text=True,
                                   timeout=120)
            self.assertEqual(built.returncode, 0,
                             built.stderr + built.stdout)
            executed = subprocess.run(
                [str(binary)], capture_output=True, text=True,
                timeout=35, cwd=directory)
            self.assertEqual(executed.returncode, 0,
                             executed.stderr + executed.stdout)
            self.assertIn("PASS: native Modern pre-SRAM profile root",
                          executed.stdout)
            self.assertIn("PASS: fresh-process native Modern 1P and paired 2P Records readback",
                          executed.stdout)

    def test_guest_observer_publishes_only_after_explicit_join(self):
        bridge = (ROOT / "tools/baldosa_native_pause_lifecycle.cpp").read_text(
            encoding="utf-8")
        writer = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text(
            encoding="utf-8")
        self.assertIn("ur_baldosa_modern_root_source_bound_2p_profiles(",
                      bridge)
        self.assertIn("ur_baldosa_modern_publish_settled_two_player_match(",
                      bridge)
        self.assertIn("bind_local_multiplayer_match_context(", writer)
        self.assertIn("baldosa_sram_checkpoint_preflight_under_lock(", writer)
        self.assertIn("append_multiplayer_match_pair(", writer)
        # The shared native preflight now checks both typed and raw P1/P2
        # data paths before OS locks, and again under the same locks.
        self.assertIn("baldosa_native_selected_profile_paths_are_real(", writer)
        self.assertIn("g_native_user_root, selected_root.save_root", writer)
        self.assertIn("g_native_user_root, first.save_root", writer)
        self.assertIn("g_native_user_root, second.save_root", writer)
        guard = (PRODUCT / "baldosa_native_profile_path_guard.hpp").read_text(
            encoding="utf-8")
        self.assertIn('baldosa_native_real_directory(user_root / "saves")',
                      guard)
        self.assertIn('baldosa_native_real_directory(profile)', guard)
        self.assertIn('baldosa_native_real_file(profile / "host-profile.txt")',
                      guard)
        self.assertIn('baldosa_native_real_file(profile / "save.srm")',
                      guard)
        self.assertIn("g_last_published_two_player_event = event;", writer)
        self.assertNotIn("RtlWriteSram();", writer)


if __name__ == "__main__":
    unittest.main()
