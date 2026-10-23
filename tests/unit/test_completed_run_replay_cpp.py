import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunReplayCppTests(unittest.TestCase):
    def test_windows_utf8_path_boundary_is_explicit(self):
        source = (ROOT / "native" / "product" /
                  "completed_run_replay.cpp").read_text(encoding="utf-8")
        self.assertIn('"local_tournament_utf8_path.hpp"', source)
        self.assertIn("host_native_path_from_utf8(user_data_root)", source)
        self.assertIn("host_native_path_from_utf8(directory_)", source)
        self.assertIn("host_native_path_from_utf8(path)", source)
        self.assertIn("directory_ = staging.u8string();", source)
        self.assertIn('input_path_ = (staging / "selected-run.input").u8string();', source)

    def test_staging_and_return_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-replay-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_replay.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_replay_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run(
                [str(exe), str(pathlib.Path(tmp) / "selected.input")],
                cwd=ROOT,
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
