#!/usr/bin/env python3
"""Guard source and native behavior of Baldosa Modern root physical input."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/baldosa_native_modern_root.cpp"
HEADER = ROOT / "native/product/modern_root_physical_edges.hpp"
TEST = ROOT / "tests/native/modern_root_physical_edges_test.cpp"


class BaldosaRootPhysicalEdgesTests(unittest.TestCase):
    def test_single_authority_and_real_sdl_repeat_is_tested(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('#include "modern_root_physical_edges.hpp"', source)
        self.assertIn("g_navigation_edges.keyboard(physical, pressed != 0)", source)
        self.assertIn("g_navigation_edges.p1_gamepad(physical, pressed != 0)", source)
        self.assertIn("if (player != 0) return 0;", source)
        self.assertIn("key == SDLK_DOWN && frame == 60", source)
        self.assertIn("if (SDL_PushEvent(&event) != 1) std::abort();", source)
        self.assertIn("return key == SDLK_ESCAPE && first_press &&", source)
        self.assertIn("return button == kGamepadBtn_B && first_press &&", source)
        self.assertNotIn("RtlRunFrame(", source)
        self.assertNotIn("g_ram[0x009f] =", source)

    def test_native_cpp_edge_contract(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "root-physical-edges"
            result = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(binary)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("PASS: native Modern root keyboard/P1", result.stdout)


if __name__ == "__main__":
    unittest.main()
