import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernTourContinueCppTests(unittest.TestCase):
    def test_continue_route_uses_stock_menu_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-tour-continue-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    str(ROOT / "tests" / "native" / "modern_tour_continue_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_tour_source_and_native_fixture_trigger_full_unit(self):
        workflow = (
            ROOT / ".github/workflows/tooling-unit-tests.yml"
        ).read_text(encoding="utf-8")
        # A C++-only tour patch must not silently skip the suite that
        # compiles and executes this exact production state machine.
        self.assertIn(
            '- "native/product/modern_tour_continue.hpp"', workflow)
        self.assertIn(
            '- "tests/native/modern_tour_continue_test.cpp"', workflow)
        self.assertIn('      - "tests/unit/**"', workflow)


if __name__ == "__main__":
    unittest.main()
