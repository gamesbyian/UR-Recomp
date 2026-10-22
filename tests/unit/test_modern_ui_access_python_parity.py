#!/usr/bin/env python3
"""The Python diagnostics mirror three C++ formulas; prove they agree."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools import qa_modern_visual_diagnostics as d

ROOT = Path(__file__).resolve().parents[2]


class ModernUiAccessPythonParity(unittest.TestCase):
    def test_cpp_and_python_formulas_agree(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "parity"
            build = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I",
                 str(ROOT), str(ROOT / "tests/native/modern_ui_access_parity_dump.cpp"),
                 "-o", str(exe)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            lines = subprocess.run([str(exe)], capture_output=True, text=True,
                                   check=True).stdout.splitlines()
        self.assertGreater(len(lines), 20)
        seen = {"safe": 0, "scale": 0}
        for line in lines:
            f = line.split()
            if f[0] == "safe":
                w, h = int(f[1]), int(f[2])
                title = tuple(int(v) for v in f[4:8])
                action = tuple(int(v) for v in f[9:13])
                self.assertEqual(d.title_safe(w, h) or (0, 0, 0, 0), title, line)
                self.assertEqual(d.action_safe(w, h) or (0, 0, 0, 0), action, line)
            else:
                lw, lh, ow, oh = (int(v) for v in f[1:5])
                factor = int(f[6])
                vp = tuple(int(v) for v in f[8:12])
                got = d.integer_scale(lw, lh, ow, oh)
                if factor == 0:
                    self.assertIsNone(got, line)
                else:
                    self.assertEqual(got, (factor, vp[0], vp[1], vp[2], vp[3]), line)
            seen[f[0]] += 1
        self.assertGreater(seen["safe"], 5)
        self.assertGreater(seen["scale"], 15)


if __name__ == "__main__":
    unittest.main()
