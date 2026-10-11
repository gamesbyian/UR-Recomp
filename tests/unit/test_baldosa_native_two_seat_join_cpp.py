#!/usr/bin/env python3
"""Native two-controller join cannot infer identity from device seat alone."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"

class BaldosaNativeTwoSeatJoinTests(unittest.TestCase):
    def test_explicit_seat_confirmations_with_catalog_authority(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        sources = (
            ROOT / "tests/native/baldosa_native_two_seat_join_test.cpp",
            PRODUCT / "host_profile_runtime.cpp",
            PRODUCT / "host_profile_state.cpp",
            PRODUCT / "host_product_state.cpp",
            PRODUCT / "output_resolution_policy.cpp",
            PRODUCT / "modern_racer_identity.cpp",
        )
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "two-seat-join"
            built = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(PRODUCT),
                 *map(str, sources), "-o", str(binary)],
                capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            tested = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0,
                             tested.stderr + tested.stdout)
            self.assertIn("PASS: native two-seat join", tested.stdout)

    def test_native_root_consents_and_revokes_on_source_lifecycle(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        self.assertIn("g_two_seat_join.begin(std::move(ready), active)", source)
        self.assertIn("ready.erase(std::remove_if(", source)
        self.assertIn("profile_id != active", source)
        self.assertIn("ur_baldosa_modern_profile_can_join_opponent(", source)
        profile_adapter = (
            ROOT / "tools/baldosa_modern_profile_activation.cpp"
        ).read_text(encoding="utf-8")
        self.assertIn("catalog_entry_matches_profile_state(", profile_adapter)
        self.assertIn("baldosa_sram_file_matches_exact(", profile_adapter)
        painter = (PRODUCT / "modern_root_overlay_presenter.hpp").read_text(
            encoding="utf-8")
        self.assertIn("view.two_seat_join_open", painter)
        self.assertIn("TWO PLAYER PROFILES", painter)
        self.assertIn("player == 1 && g_visible && g_two_seat_join.open()",
                      source)
        self.assertIn("join_confirm(1)", source)
        self.assertIn("join_confirm(0)", source)
        self.assertIn("ur_baldosa_modern_root_source_bound_2p_profiles(",
                      source)
        self.assertIn("g_stock_handed_off", source)
        self.assertIn("g_two_seat_join.cancel();", source)
        self.assertIn("request_stock_route(2);", source)
        self.assertNotIn("g_ram[0x017d] =", source.lower())
        self.assertNotIn("save_multiplayer_match_record(", source)


if __name__ == "__main__":
    unittest.main()
