import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunRecordReadBoundsTests(unittest.TestCase):
    def test_fresh_process_bounds_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            executable = directory / "run-record-bounds"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native/product"),
                    str(ROOT / "native/product/completed_run_record.cpp"),
                    str(ROOT / "tests/native/completed_run_record_read_bounds_test.cpp"),
                    "-o", str(executable),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(executable), str(directory)], check=True)


if __name__ == "__main__":
    unittest.main()
