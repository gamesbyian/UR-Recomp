import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunGhostRasterCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-ghost-raster-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Wno-unused-variable",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    "-I",
                    str(ROOT / "native" / "presentation"),
                    str(ROOT / "native" / "presentation" / "racer_replacement_selector.cpp"),
                    str(ROOT / "native" / "presentation" / "completed_run_ghost_racer_selector.cpp"),
                    str(ROOT / "native" / "presentation" / "completed_run_ghost_raster.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_ghost_raster_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
