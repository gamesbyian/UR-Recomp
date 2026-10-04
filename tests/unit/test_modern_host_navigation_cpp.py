import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class ModernHostNavigationCppTests(unittest.TestCase):
    def test_semantic_action_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-host-navigation-test"
            subprocess.run([
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-I", str(ROOT / "native" / "product"),
                str(ROOT / "tests" / "native" / "modern_host_navigation_test.cpp"),
                "-o", str(exe),
            ], cwd=ROOT, check=True)
            subprocess.run([str(exe)], cwd=ROOT, check=True)

if __name__ == "__main__":
    unittest.main()
