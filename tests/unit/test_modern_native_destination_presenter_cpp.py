#!/usr/bin/env python3
"""Compile and execute the real native Modern destination painter contract."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "tools/baldosa_native_modern_root.cpp"
PRESENTER = ROOT / "native/product/modern_native_destination_presenter.hpp"
TEST = ROOT / "tests/native/modern_native_destination_presenter_test.cpp"


class ModernNativeDestinationPresenterTest(unittest.TestCase):
    def test_native_integration_has_single_narrow_presentation_hook(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn('#include "modern_native_destination_presenter.hpp"', source)
        self.assertEqual(source.count("render_modern_native_destination("), 1)
        self.assertIn("if (drawn)", source)
        self.assertIn("g_options.open) fill_options_view(view, option_text);", source)
        self.assertIn("view.records_detail = g_records_detail;", source)
        self.assertIn("view.two_seat_join_open = g_two_seat_join.open();", source)
        self.assertIn("view.practice_course_name = preview.course_name;", source)
        self.assertIn("view.first_racer_preset_name = presets[chosen].name;", source)
        self.assertIn("width != 256 || height != 224", source)
        self.assertNotIn("SDL_", PRESENTER.read_text(encoding="utf-8"))

    def test_cpp_native_destination_views_compile_and_render(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "modern-native-destinations"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(executable)],
                capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(executable)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS: Modern native destination views", run.stdout)


if __name__ == "__main__":
    unittest.main()
