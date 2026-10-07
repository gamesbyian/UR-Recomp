import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernRootMenuCppTests(unittest.TestCase):
    def test_root_navigation_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-root-menu-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native/product"),
                    str(ROOT / "tests/native/modern_root_menu_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
