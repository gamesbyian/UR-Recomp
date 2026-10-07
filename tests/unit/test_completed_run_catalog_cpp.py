import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunCatalogCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-catalog-test"
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
                    str(ROOT / "native" / "product" / "completed_run_comparison.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_presentation.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_catalog.cpp"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_catalog_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
