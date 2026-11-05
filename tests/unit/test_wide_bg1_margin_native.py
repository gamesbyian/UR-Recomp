"""Compile and run the real standalone BG1 course/mismatch C regression."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class WidescreenBg1NativeTests(unittest.TestCase):
    def test_course_and_first_mismatch_suppression(self):
        compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
        if not compiler:
            self.skipTest("C compiler unavailable; native regression not executed")
        with tempfile.TemporaryDirectory(prefix="ur-ws-bg1-") as temp:
            executable = Path(temp) / "ws_bg1_test"
            command = [
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-DUR_WS_MARGINS_NO_RUNTIME", "-I", str(ROOT / "native/title"),
                str(ROOT / "native/title/uniracers_ws_margins.c"),
                str(ROOT / "tests/native/uniracers_ws_margins_test.c"),
                "-o", str(executable),
            ]
            build = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


    def test_actual_runtime_first_mismatch_and_split_suppression(self):
        compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
        if not compiler:
            self.skipTest("C compiler unavailable; runtime margin regression not executed")
        with tempfile.TemporaryDirectory(prefix="ur-ws-runtime-") as temp:
            binary = Path(temp) / "ws_runtime_test"
            build = subprocess.run([
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-I", str(ROOT / "tests/native/ws_margin_stubs"),
                "-I", str(ROOT / "native/title"),
                str(ROOT / "native/title/uniracers_ws_margins.c"),
                str(ROOT / "tests/native/uniracers_ws_margins_runtime_test.c"),
                "-o", str(binary),
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
