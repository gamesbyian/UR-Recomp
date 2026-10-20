#!/usr/bin/env python3
"""Compile and exercise the actual C++ Modern menu motion and native pixels."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
BALDOSA = ROOT / "tools/baldosa_native_modern_root.cpp"
MOTION = ROOT / "native/product/modern_menu_motion.hpp"
TEST = ROOT / "tests/native/modern_menu_motion_test.cpp"


class ModernMenuMotionTest(unittest.TestCase):
    def test_no_guest_clock_or_unapproved_hd_racer(self):
        source = MOTION.read_text(encoding="utf-8")
        host = HOST.read_text(encoding="utf-8")
        self.assertIn("analysis/generated/menu-visual-language.json", source)
        self.assertIn("kModernMenuMotionSelectionFrames = 12", source)
        self.assertIn("kModernMenuMotionEntranceFrames = 39", source)
        self.assertNotIn("SDL_", source)
        self.assertNotIn("racer_hd_presenter.hpp", source)
        self.assertNotIn("guest_snapshot", source)
        self.assertIn('#include "modern_menu_motion.hpp"', host)
        self.assertIn("modern_menu_tick60(", host)
        self.assertIn("SDL_GetTicks()", host)
        self.assertIn("UR_REDUCED_MOTION", host)
        self.assertIn("UR_MODERN_MENU_TEST_ADVANCE_PER_PRESENT", host)
        self.assertIn("modern_menu_capture_test_tick60(", host)
        self.assertIn("g_modern_root_motion_root_presents = 0", host)
        self.assertIn("paint_modern_menu_selection_motion(", host)
        baldosa = BALDOSA.read_text(encoding="utf-8")
        self.assertIn('#include "modern_menu_motion.hpp"', baldosa)
        self.assertIn("modern_menu_tick60(", baldosa)
        self.assertIn("SDL_GetTicks()", baldosa)
        self.assertIn("UR_REDUCED_MOTION", baldosa)
        self.assertIn("UR_MODERN_MENU_TEST_ADVANCE_PER_PRESENT", baldosa)
        self.assertIn("modern_menu_capture_test_tick60(", baldosa)
        self.assertIn("UR_MODERN_MENU_MOTION_CAPTURE ordinal=%llu tick60=%llu ", baldosa)
        for token in ("selection=%u", "spin=%d", "offset=%d",
                      "entrance=%d", "root_x=%d", "root_w=%d",
                      "surface_w=%d", "surface_h=%d", "painted=%d"):
            self.assertIn(token, baldosa)
        self.assertIn("if (provenance_log)", baldosa)
        self.assertIn("g_native_menu_motion_root_presents = 0", baldosa)
        self.assertIn("UR_MODERN_SOURCE_HERO_EXPERIMENTAL_BUILD", baldosa)
        self.assertIn("UR_MODERN_SOURCE_HERO_EXPERIMENTAL_BUILD == 1", baldosa)
        self.assertIn("#if !__has_include(", baldosa)
        self.assertIn('#error "Opt-in original menu hero build requires', baldosa)
        self.assertIn("paint_modern_menu_selection_motion(", baldosa)
        # A 342-wide owner build must not paint the moving focus relative
        # to a different rectangle than the background shell. Integration
        # may widen/recentre root_rect but must pass it to BOTH painters.
        self.assertIn("const HostOverlayRect root_rect{", baldosa)
        self.assertIn("root_rect, view);", baldosa)
        self.assertIn("root_rect, phase);", baldosa)
        self.assertNotIn("HostOverlayRect{(width - 240) / 2", baldosa)
        self.assertIn("!view.quit_confirm", baldosa)
        self.assertIn("!view.two_seat_join_open", baldosa)

    def test_source_measured_stock_motion_deltas_are_unchanged(self):
        source = json.loads(
            (ROOT / "analysis/generated/menu-visual-language.json").read_text(
                encoding="utf-8"))
        header = MOTION.read_text(encoding="utf-8")
        for name, expected in (
            ("kModernMenuMotionSourceCursorSteps",
             source["cursor"]["move_y_per_frame"]),
            ("kModernMenuMotionSourceEntranceDelta",
             source["transition_main_to_options"][
                 "enter_velocity_px_per_frame"]),
        ):
            pattern = rf"\b{name}\s*\{{\{{(.*?)\}}\}};"
            match = re.search(pattern, header, flags=re.DOTALL)
            self.assertIsNotNone(match, name)
            observed = [int(x) for x in re.findall(r"\b\d+\b",
                                                     match.group(1))]
            self.assertEqual(observed, expected)
        self.assertTrue(source["cursor"]["move_response_same_frame"])
        self.assertEqual(len(source["cursor"]["move_y_per_frame"]), 12)
        self.assertEqual(source["transition_main_to_options"]["distance_px"],
                         sum(source["transition_main_to_options"][
                             "enter_velocity_px_per_frame"]))
        self.assertEqual(
            source["transition_main_to_options"]["enter_frames"], 39)

    def test_compiled_60hz_and_native_rgba(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "modern-menu-motion-test"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(binary)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr + build.stdout)
            run = subprocess.run(
                [str(binary)], capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn(
                "PASS: Modern native menu motion 60Hz, 4:3/16:9, reduced motion",
                run.stdout,
            )


if __name__ == "__main__":
    unittest.main()
