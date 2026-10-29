import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernTourActionMenuCppTests(unittest.TestCase):
    def test_tour_action_changes_request_the_compiled_suite(self):
        # A green PR must compile this header's adverse selection cases,
        # not rely only on the expensive unrelated native guest workflow.
        workflow = (ROOT / ".github" / "workflows" /
                    "tooling-unit-tests.yml").read_text(encoding="utf-8")
        for path in (
            "native/product/modern_tour_action_menu.hpp",
            "tests/native/modern_tour_action_menu_test.cpp",
        ):
            self.assertIn(f'- "{path}"', workflow)

    def test_tour_action_menu(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-tour-action-menu-test"
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
                    str(ROOT / "tests" / "native" /
                        "modern_tour_action_menu_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
