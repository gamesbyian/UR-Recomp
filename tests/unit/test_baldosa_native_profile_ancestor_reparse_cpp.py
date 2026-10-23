"""Build and run real profile ancestor path preflight regression."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BaldosaNativeProfileAncestorCppTests(unittest.TestCase):
    def test_redirected_ancestor_is_rejected(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "profile-ancestor"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT / "native/product"),
                 str(ROOT / "tests/native/baldosa_native_profile_ancestor_reparse_test.cpp"),
                 "-o", str(binary)],
                cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stderr + build.stdout)
            run = subprocess.run([str(binary)], cwd=ROOT, capture_output=True,
                                 text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: redirected ancestor rejected", run.stdout)


if __name__ == "__main__":
    unittest.main()
