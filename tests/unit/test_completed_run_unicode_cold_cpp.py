"""ROM-free production Records -> replay Unicode cold-process regression.

Tests exactly two separate compiled native processes. Unicode subpaths are
constructed inside C++, so narrow Windows argv cannot accidentally substitute
an ACP pathname. The complete GUI, physical controller and DATA-05 criterion
remain separate acceptance requirements.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunUnicodeColdCppTests(unittest.TestCase):
    def test_unicode_archive_to_replay_across_cold_process(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="ur-data05-cold-") as temporary:
            base = pathlib.Path(temporary)
            exe = base / ("unicode-run-replay.exe" if sys.platform == "win32"
                          else "unicode-run-replay")
            cmd = [
                compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-pthread", "-I",
                str(ROOT / "native" / "product"),
                *[str(ROOT / "native" / "product" / name) for name in (
                    "completed_run_record.cpp",
                    "completed_run_capture.cpp",
                    "completed_run_store.cpp",
                    "completed_run_replay.cpp",
                )],
                str(ROOT / "tests" / "native" /
                    "completed_run_unicode_cold_test.cpp"),
                "-o", str(exe),
            ]
            subprocess.run(cmd, cwd=ROOT, check=True, timeout=120)
            root = base / "cold-root"
            for mode, marker in (
                ("write", "DATA05_UNICODE_COLD_WRITE=passed"),
                ("cold-read", "DATA05_UNICODE_COLD_READ=passed"),
            ):
                with self.subTest(mode=mode):
                    completed = subprocess.run(
                        [str(exe), str(root), mode], cwd=ROOT, check=True,
                        capture_output=True, text=True, timeout=30)
                    self.assertIn(marker, completed.stdout)
            # One immutable .urrun must survive replay staging/cleanup.
            runs = list((root / "player-漢字-資料-🚲" /
                         "runs" / "mike").glob("*.urrun"))
            self.assertEqual(len(runs), 1)
            self.assertGreater(runs[0].stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
