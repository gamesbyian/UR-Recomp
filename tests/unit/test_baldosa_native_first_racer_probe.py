#!/usr/bin/env python3
"""Fail-closed controller-preset creation and native restart contract.

Synthetic strings test the parser/contract, not actual gamepad hardware.
Windows exact AOT runtime proof is a separate CI step.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_first_racer_probe as probe


class NativeFirstRacerTests(unittest.TestCase):
    def test_first_run_is_controller_explicit_and_globally_last(self):
        adapter = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text()
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        painter = (ROOT / "native/product/modern_root_overlay_presenter.hpp").read_text()
        staging = (ROOT / "tools/baldosa_modern_profile_activation_spike.py").read_text()
        self.assertIn("ur_baldosa_modern_create_initial_preset(unsigned preset)", adapter)
        self.assertIn("clean_stock_sram()", adapter)
        self.assertIn("source[0x0748] = racer->rider_index;", adapter)
        self.assertLess(
            adapter.index("save_host_profile_state_file_if_current(", adapter.index("ur_baldosa_modern_create_initial_preset")),
            adapter.index("save_host_profile_catalog_file_if_current(", adapter.index("ur_baldosa_modern_create_initial_preset")))
        self.assertLess(
            adapter.index("save_host_profile_catalog_file_if_current(", adapter.index("ur_baldosa_modern_create_initial_preset")),
            adapter.index("save_host_product_state_file_if_current(", adapter.index("ur_baldosa_modern_create_initial_preset")))
        self.assertIn("create_directory(profile_root, ec)", adapter)
        self.assertNotIn("fs::remove_all(profile_root)", adapter)
        self.assertIn('"clean_stock_sram.cpp"', staging)
        self.assertIn("case SDLK_F2:", root)
        self.assertIn("case kGamepadBtn_X:", root)
        self.assertIn("g_navigation_edges.p1_gamepad(physical, pressed != 0)", root)
        self.assertIn("if (g_initial_creation_needs_restart) return false;", root)
        self.assertIn("first_racer_created=1 restart_required=1", root)
        self.assertIn("view.first_racer_creation_open", painter)
        self.assertIn("QUIT, THEN RELAUNCH", painter)

    def test_first_controller_action_requires_order_and_last_selector(self):
        correct = (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_open=1 presets=16\n"
            "UR_BALDOSA_MODERN_ROOT synthetic_first_racer_x=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_preset=1\n"
            "UR_BALDOSA_NATIVE_PROFILE CREATED profile=andrew rider=1 "
            "bytes=8192 restart_required=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1 restart_required=1\n"
        )
        probe.assert_created(correct)
        for bad in (
            correct + correct,
            correct.replace("profile=andrew", "profile=mike"),
            correct.replace("rider=1", "rider=0"),
            correct.replace("preset=1", "preset=0"),
            correct.replace("first_racer_created=1", "first_racer_rejected=1"),
            correct.replace("first_racer_open=1", "first_racer_open=0"),
            correct + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    probe.assert_created(bad)

    def test_fresh_guest_must_load_prior_exact_8k_snapshot(self):
        raw = bytes(range(256)) * 32
        pass_log = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew "
            "root=saves/profile-andrew\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=andrew "
            "bytes=8192 fnv=" + probe.fnv32(raw) + "\n"
        )
        probe.assert_fresh_named_guest(pass_log, raw)
        for bad in (
            pass_log + pass_log,
            pass_log.replace("profile=andrew", "profile=mike"),
            pass_log.replace(probe.fnv32(raw), "00000000"),
            pass_log + "UR_BALDOSA_NATIVE_PROFILE CREATED=1\n",
            pass_log + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n",
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    probe.assert_fresh_named_guest(bad, raw)


if __name__ == "__main__":
    unittest.main()
