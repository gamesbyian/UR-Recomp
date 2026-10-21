#!/usr/bin/env python3
"""Compile first-party, source-atlas drawing against actual native C++17 pixels.

No copyrighted binaries, PNG fixture fabrication masquerading as game images,
or SDL mocks. Tests the same header that Modern painters can consume.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native/product/modern_menu_source_atlas.hpp"
SOURCE = ROOT / "tests/native/modern_menu_source_atlas_test.cpp"
GRAMMAR = ROOT / "native/product/modern_menu_visual_grammar.hpp"


class ModernMenuSourceAtlasNativeTest(unittest.TestCase):
    def test_native_source_atlas_exact_pixel_contract(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "modern-menu-source-atlas"
            build = subprocess.run([
                compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-I", str(ROOT), str(SOURCE),
                "-o", str(exe),
            ], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], cwd=ROOT,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS: original menu source raster cells",
                          run.stdout)

    def test_source_grammar_reexports_atlas_without_art_or_execution_authority(self):
        grammar = GRAMMAR.read_text(encoding="utf-8")
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('#include "modern_menu_source_atlas.hpp"', grammar)
        for prohibited in ("SDL_", "Rtl", "snesrecomp_", "filesystem",
                           "write_sram", "fopen(", "decode_png("):
            self.assertNotIn(prohibited, source)
        self.assertIn("ModernMenuSourceSheet::Cursor", source)
        self.assertIn("ModernMenuSourceSheet::Backdrop", source)


if __name__ == "__main__":
    unittest.main()
