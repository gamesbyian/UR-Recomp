"""ROM-free native profile-path admission, including a redirected user root."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NativeProfilePathGuardTests(unittest.TestCase):
    def test_direct_root_and_redirected_root(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "profile-path-guard"
            cmd = [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                   "-Werror", "-pedantic", "-I", str(ROOT / "native/product"),
                   str(ROOT / "tests/native/baldosa_native_profile_path_guard_test.cpp"),
                   "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            finished = subprocess.run([str(exe)], capture_output=True, text=True,
                                      timeout=20)
            self.assertEqual(finished.returncode, 0,
                             finished.stdout + finished.stderr)
            self.assertIn("PASS: direct named-profile root", finished.stdout)


if __name__ == "__main__":
    unittest.main()
