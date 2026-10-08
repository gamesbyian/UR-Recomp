import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class StockTourProgressOverviewCppTests(unittest.TestCase):
    def test_stock_progression_overview_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "stock-tour-progress-overview"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-pedantic", "-I", str(ROOT / "native/title"),
                 str(ROOT / "tests/native/uniracers_tour_progress_overview_test.cpp"),
                 "-o", str(exe)],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
