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
        self.assertEqual(source.count("render_modern_native_pause_destination("), 1)
        self.assertIn("fill_options_view(view, option_text);", source)
        self.assertIn("g_pause_options_open = true;", source)
        self.assertIn("if (drawn)", source)
        self.assertIn("auto shell_view = view;", source)
        self.assertIn("root_rect, shell_view);", source)
        for flag in ("options_open", "read_only_records_open",
                     "practice_picker_open", "practice_launch_pending",
                     "two_seat_join_open", "first_racer_open",
                     "unbound_two_player_warning_open"):
            self.assertIn(f"shell_view.{flag} = false;", source)
        self.assertIn("g_options.open) fill_options_view(view, option_text);", source)
        self.assertIn("view.records_detail = g_records_detail;", source)
        self.assertIn("view.two_seat_join_open = g_two_seat_join.open();", source)
        self.assertIn("view.practice_course_name = preview.course_name;", source)
        self.assertIn("view.first_racer_preset_name = presets[chosen].name;", source)
        self.assertIn("(width != 256 && width != 342)", source)
        self.assertIn("width == 342 ? 320 : 240", source)
        self.assertIn("modern_native_frontend_compact_drawable(", source)
        self.assertIn("*logical_width = 256;", source)
        self.assertIn("*logical_width = 342;", source)
        self.assertIn("root_rect, shell_view);", source)
        self.assertIn("root_rect, view);", source)
        # Native diagnostic receipts are emitted only *after* successful
        # painting from the authoritative view, with the actual root/raster.
        self.assertIn("modern_native_destination_stage(view)", source)
        self.assertIn("g_last_native_destination_stage != stage", source)
        self.assertIn("UR_BALDOSA_MODERN_DESTINATION stage=%s", source)
        self.assertIn("raster=%dx%d root=%d,%d,%d,%d", source)
        self.assertIn("source=modern_product_view", source)
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
            if build.returncode != 0:
                print("FAIL: native destination build (bounded):",
                      (build.stdout + build.stderr)[-3000:], flush=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(executable)], capture_output=True, text=True)
            # CI's parallel unit runner redirects full tracebacks into retained
            # shard artifacts. Also surface a bounded exact failing assertion
            # in the job log so the first defect is actionable without polling
            # or downloading every shard.
            if run.returncode != 0:
                print("FAIL: native destination runtime (bounded):",
                      (run.stdout + run.stderr)[-3000:], flush=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS: Modern native destination views", run.stdout)


if __name__ == "__main__":
    unittest.main()
