#!/usr/bin/env python3
"""Build and execute the actual native Modern visual-grammar primitives."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ModernMenuVisualGrammarTest(unittest.TestCase):
    def test_native_source_and_raster_contract(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        source = ROOT / "tests/native/modern_menu_visual_grammar_test.cpp"
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "modern-menu-visual-grammar"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(source),
                 "-o", str(executable)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(executable)], cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS: source-measured Modern menu grammar",
                          run.stdout)

    def test_native_root_consumes_one_shared_visual_grammar(self):
        host = (ROOT / "native/product/modern_root_overlay_presenter.hpp").read_text()
        self.assertIn('#include "modern_menu_visual_grammar.hpp"', host)
        self.assertIn("modern_menu_paint_checker_backdrop(", host)
        self.assertIn("modern_menu_paint_focus_band(", host)
        # Shared root uses one globally anchored BG1 checker phase across
        # widescreen/compact backgrounds; the stock guest is untouched.
        self.assertIn("rect.width, rect.height, scale, true);", host)
        # Render-only layer must not acquire independent input/routing.
        grammar = (ROOT / "native/product/modern_menu_visual_grammar.hpp").read_text()
        for forbidden in ("SDL_", "snesrecomp_", "write_sram", "std::filesystem"):
            self.assertNotIn(forbidden, grammar)


if __name__ == "__main__":
    unittest.main()
