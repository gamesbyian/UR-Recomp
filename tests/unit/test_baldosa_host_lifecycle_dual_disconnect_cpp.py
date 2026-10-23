"""Compile and run the native two-seat disconnect lifecycle regression."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BaldosaDualDisconnectCppTests(unittest.TestCase):
    def test_native_simultaneous_seat_departures(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "dual-disconnect"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT / "native/product"),
                 str(ROOT / "tests/native/baldosa_host_lifecycle_dual_disconnect_test.cpp"),
                 "-o", str(binary)],
                cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stderr + build.stdout)
            run = subprocess.run([str(binary)], cwd=ROOT, capture_output=True,
                                 text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: dual-disconnect source mask", run.stdout)


if __name__ == "__main__":
    unittest.main()
