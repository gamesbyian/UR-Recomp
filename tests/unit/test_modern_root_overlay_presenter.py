#!/usr/bin/env python3
"""The existing Modern root's actual presenter is now reusable by Baldosa."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
PRESENTER = ROOT / "native/product/modern_root_overlay_presenter.hpp"
TEST = ROOT / "tests/native/modern_root_overlay_presenter_test.cpp"


class ModernRootOverlaySharedPresenterTest(unittest.TestCase):
    def test_shipping_host_calls_the_same_renderer(self):
        host = HOST.read_text(encoding="utf-8")
        presenter = PRESENTER.read_text(encoding="utf-8")
        self.assertIn('#include "modern_root_overlay_presenter.hpp"', host)
        self.assertIn("ur::product::render_modern_root_overlay(", host)
        self.assertIn("&snes_ovl_fill_rect, &snes_ovl_stroke_rect, &snes_ovl_draw_text", host)
        self.assertEqual(host.count('"UR_MODERN_ROOT PRESENT"'), 1)
        self.assertNotIn("constexpr const char* kDetails[]", host)
        self.assertEqual(presenter.count("TOUR AND CONTINUE"), 1)
        self.assertEqual(presenter.count("CHOOSE A COURSE"), 1)
        self.assertEqual(presenter.count("LOCAL TWO PLAYER"), 1)
        self.assertEqual(presenter.count("RUNS AND BEST TIMES"), 1)
        self.assertEqual(presenter.count("DISPLAY AND CONTROLS"), 1)
        # Preserve the independent #2125 first-racer shortcut contract
        # while adding the shared-root child screens' new language guards.
        self.assertIn('"X CREATE RACER"', presenter)
        self.assertNotIn("X CREATE STOCK RACER", presenter)
        # Both original shared-root renderer and separately owned native
        # child must present user-facing copy, not internal guest terminology.
        for phrase in ("ENTERING ORIGINAL COURSE", "WAIT FOR SOURCE GO",
                       "READ ONLY - NO REPLAY", "SECOND STOCK RACER",
                       "FIRST STOCK RACER", "NO LIVE RACER CHANGE",
                       "PLAY STOCK 2P ANYWAY?", "NO MATCH HISTORY SAVED"):
            self.assertNotIn('"' + phrase + '"', presenter)
        self.assertNotIn("SDL_", presenter)
        self.assertNotIn("Rtl", presenter)
        self.assertNotIn("snesrecomp_desktop_", presenter)

    def test_actual_cpp_links_and_renders_original_and_wide(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "root-presenter-native"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(executable)],
                capture_output=True, text=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(executable)], capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS: one shared Modern root artwork presenter", run.stdout)


if __name__ == "__main__":
    unittest.main()
