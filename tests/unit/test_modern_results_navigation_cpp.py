import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernResultsNavigationCppTests(unittest.TestCase):
    def _compile_and_run(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-results-navigation-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "tests" / "native" / source),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_results_navigation_model(self):
        self._compile_and_run("modern_results_navigation_test.cpp")

    def test_results_stale_direction(self):
        self._compile_and_run("modern_results_stale_direction_test.cpp")


if __name__ == "__main__":
    unittest.main()
