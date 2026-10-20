#!/usr/bin/env python3
"""Compile and exercise the actual C++ Modern menu motion and native pixels."""
from pathlib import Path
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
        self.assertIn("paint_modern_menu_selection_motion(", host)
        baldosa = BALDOSA.read_text(encoding="utf-8")
        self.assertIn('#include "modern_menu_motion.hpp"', baldosa)
        self.assertIn("modern_menu_tick60(", baldosa)
        self.assertIn("SDL_GetTicks()", baldosa)
        self.assertIn("UR_REDUCED_MOTION", baldosa)
        self.assertIn("UR_MODERN_SOURCE_HERO_EXPERIMENTAL_BUILD", baldosa)
        self.assertIn("UR_MODERN_SOURCE_HERO_EXPERIMENTAL_BUILD == 1", baldosa)
        self.assertIn("#if !__has_include(", baldosa)
        self.assertIn('#error "Opt-in original menu hero build requires', baldosa)
        self.assertIn("paint_modern_menu_selection_motion(", baldosa)
        self.assertIn("!view.quit_confirm", baldosa)
        self.assertIn("!view.two_seat_join_open", baldosa)

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
