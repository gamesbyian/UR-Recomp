import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class UniracersRunDataCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "uniracers-run-data-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "title" / "uniracers_run_data.cpp"),
                    str(ROOT / "tests" / "native" / "uniracers_run_data_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
