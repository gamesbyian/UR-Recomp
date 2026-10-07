import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunStoreCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-store-test"
            store = pathlib.Path(tmp) / "runs"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_capture.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_store_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe), str(store)], cwd=ROOT, check=True)
            # Three valid artifacts plus deliberately malformed and corrupt
            # artifacts are retained on disk; load_valid_run_records() filters
            # authority, not evidence.
            self.assertEqual(len(list(store.glob("*.urrun"))), 5)


if __name__ == "__main__":
    unittest.main()
