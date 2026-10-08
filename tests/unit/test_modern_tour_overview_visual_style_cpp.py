import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernTourOverviewVisualStyleCppTests(unittest.TestCase):
    def test_stock_menu_palette_and_responsive_tour_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-tour-overview-visual-style-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    str(ROOT / "tests/native/modern_tour_overview_visual_style_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
