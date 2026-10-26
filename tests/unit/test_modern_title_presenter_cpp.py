#!/usr/bin/env python3
"""Compile the production Modern title painter and verify native geometry/input."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests/native/modern_title_presenter_test.cpp"
TITLE = ROOT / "native/product/modern_title_presenter.hpp"
HOST = ROOT / "tools/baldosa_native_modern_root.cpp"
ADAPTER = ROOT / "tools/baldosa_modern_profile_activation_spike.py"


class NativeModernTitleTest(unittest.TestCase):
    def test_real_cpp_renderer_state_and_bounds(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++17 toolchain unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "modern-title-native"
            command = [
                compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-I", str(ROOT),
                str(TEST), "-o", str(binary),
            ]
            proc = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            proc = subprocess.run([str(binary)], text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_host_owns_mode_and_source_native_raster(self):
        source = HOST.read_text(encoding="utf-8")
        presenter = TITLE.read_text(encoding="utf-8")
        adapter = ADAPTER.read_text(encoding="utf-8")
        self.assertIn('std::strcmp(mode, "authentic") == 0', source)
        self.assertIn("modern_title_boot(", source)
        self.assertIn('std::strcmp(fixture, "24") != 0', source)
        self.assertIn('std::strcmp(fixture, "25") != 0', source)
        self.assertIn('std::strcmp(fixture, "26") != 0', source)
        self.assertIn('std::strcmp(fixture, "27") != 0', source)
        self.assertIn('std::strcmp(opt, "27") == 0', source)
        self.assertIn('std::strcmp(fixture, "28") != 0', source)
        self.assertIn("mode > 28", source)
        # Controller 15-19 must not be admitted as title-only smoke modes.
        for mode in range(15, 20):
            self.assertNotIn(f'std::strcmp(fixture, "{mode}") != 0', source)
        self.assertIn("native_p1_held_filtered=1", source)
        self.assertIn("native_p1_held_isolated=1", source)
        self.assertIn('std::strcmp(opt, "25") == 0', source)
        self.assertIn("native_keyboard_enter=1", source)
        self.assertIn('std::strcmp(opt, "26") == 0', source)
        self.assertIn("kGamepadBtn_Start, 1", source)
        self.assertIn("kGamepadBtn_Start, 0", source)
        self.assertIn("native_p1_start_button=1", source)
        self.assertIn("modern_title_confirm(g_title)", source)
        self.assertIn("modern_title_advance(g_title)", source)
        self.assertIn("g_navigation_edges.p1_gamepad(physical, pressed != 0)", source)
        self.assertIn("modern_title_active(g_title)", source)
        self.assertIn("ur_baldosa_modern_root_prepare_frame(", source)
        self.assertIn("modern_title_logical_width(", source)
        self.assertIn("ur_baldosa_modern_root_window_base_width(int)", source)
        self.assertIn("return configured() ? 428 : 320;", source)
        self.assertIn('UR_BALDOSA_MODERN_TITLE_CAPTURE_DIR', source)
        self.assertIn("rgba_fnv1a64=", source)
        self.assertIn("render_modern_title(", source)
        self.assertIn("ModernRootOverlayPainter", presenter)
        self.assertIn("kModernStockMenuPalette", presenter)
        self.assertNotIn("g_ram[", presenter)
        self.assertNotIn("SDL_", presenter)
        self.assertIn(".native_widescreen   = 1", adapter)
        self.assertIn(".window_base_width  = &ur_baldosa_modern_root_window_base_width", adapter)
        self.assertIn(".prepare_frame       = &ur_baldosa_modern_root_prepare_frame", adapter)
        self.assertIn(".compute_viewport    = &ur_baldosa_modern_root_viewport", adapter)
        self.assertIn("SnesDisplayViewport* out", adapter)
        self.assertIn("iw != 342 || ih != 224", adapter)
        self.assertIn('std::strcmp(opt, "24") == 0', source)
        self.assertIn("native_p1_start=1", source)


    def test_unknown_original_attract_wake_release_is_host_owned(self):
        # Source contract for the native input boundary. Full guest/SDL
        # execution and physical input remain distinct evidence classes.
        source = HOST.read_text(encoding="utf-8")
        keyboard = source.split(
            'extern "C" int ur_baldosa_modern_root_key(', 1
        )[1].split('extern "C" int ur_baldosa_modern_root_gamepad(', 1)[0]
        pad = source.split(
            'extern "C" int ur_baldosa_modern_root_gamepad(', 1
        )[1].split('extern "C" int ur_baldosa_modern_root_window_base_width(', 1)[0]
        self.assertIn("g_original_attract_unknown_key_releases.count(key)", keyboard)
        self.assertIn("if (!pressed) g_original_attract_unknown_key_releases.erase(key)", keyboard)
        self.assertIn("g_original_attract_unknown_key_releases.insert(key)", keyboard)
        self.assertLess(
            keyboard.index("g_original_attract_unknown_key_releases.count(key)"),
            keyboard.index("switch (key)"),
        )
        self.assertIn("g_original_attract_unknown_pad_releases.count(button)", pad)
        self.assertIn("if (!pressed) g_original_attract_unknown_pad_releases.erase(button)", pad)
        self.assertIn("g_original_attract_unknown_pad_releases.insert(button)", pad)
        self.assertLess(
            pad.index("g_original_attract_unknown_pad_releases.count(button)"),
            pad.index("switch (button)", pad.index("if (player != 0) return 0;")),
        )
        self.assertIn(
            "if (g_original_attract_visible) {\n"
            "            if (pressed) {\n"
            "                g_original_attract_unknown_pad_releases.insert(button);",
            pad,
        )
        self.assertIn("g_original_attract_unknown_key_releases.clear();", source)
        self.assertIn("g_original_attract_unknown_pad_releases.clear();", source)


if __name__ == "__main__":
    unittest.main()
