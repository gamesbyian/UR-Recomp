import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunReplayCppTests(unittest.TestCase):
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
