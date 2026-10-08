import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernPracticeVisualStyleCppTests(unittest.TestCase):
    def test_measured_stock_visual_hierarchy_and_responsive_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-practice-style-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    str(ROOT / "tests/native/modern_practice_visual_style_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
