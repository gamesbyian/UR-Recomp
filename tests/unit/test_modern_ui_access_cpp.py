#!/usr/bin/env python3
"""Build and execute the actual native Modern visual-grammar primitives."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ModernUiAccessTest(unittest.TestCase):
    def test_native_source_and_raster_contract(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        source = ROOT / "tests/native/modern_ui_access_test.cpp"
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "modern-ui-access"
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
            self.assertIn("PASS: Modern UI accessibility primitives",
                          run.stdout)

    def test_header_is_presentation_only(self):
        header = (ROOT / "native/product/modern_ui_access.hpp").read_text()
        for forbidden in ("SDL_", "snesrecomp_", "write_sram", "std::filesystem"):
            self.assertNotIn(forbidden, header)


if __name__ == "__main__":
    unittest.main()
