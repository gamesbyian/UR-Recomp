import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class StockPracticeTourUnlockTests(unittest.TestCase):
    def test_stock_unlock_tiers_and_hidden_hunter(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "stock-practice-tour-unlock-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native/title"),
                    "-I", str(ROOT / "native/product"),
                    str(ROOT / "tests/native/uniracers_practice_tour_unlock_test.cpp"),
                    "-o", str(exe)
                ],
                cwd=ROOT, check=True
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
