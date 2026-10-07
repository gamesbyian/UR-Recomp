import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernOverlayResizeMatrixCppTests(unittest.TestCase):
    def test_cpp_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-overlay-resize-matrix-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "widescreen_output_composition.cpp"),
                    str(ROOT / "native" / "product" / "modern_overlay_composition.cpp"),
                    str(ROOT / "tests" / "native" / "modern_overlay_resize_matrix_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
