import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernOverlayCompositionCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-overlay-composition-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "modern_overlay_composition.cpp"),
                    str(ROOT / "tests" / "native" / "modern_overlay_composition_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
