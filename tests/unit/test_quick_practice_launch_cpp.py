import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class QuickPracticeLaunchCppTests(unittest.TestCase):
    def test_windows_host_observes_menu_during_release_gap(self):
        root = (ROOT / "tools" / "baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        gap = root.split("    if (g_practice_input_gap > 0) {", 1)[1].split(
            "    const QuickPracticeLaunchObservation observation{", 1)[0]
        self.assertIn("quick_practice_launch_observe_source_menu(", gap)
        self.assertIn("g_ram[0x009f]", gap)
        self.assertLess(gap.index("quick_practice_launch_observe_source_menu("),
                        gap.index("--g_practice_input_gap;"))
        # Requiring the pure state-machine helper in the real Windows root
        # prevents a model-only fix that misses transitions inside the gap.

    def test_arbitrary_course_launch_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "quick-practice-launch-test"
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
                    str(ROOT / "tests/native/quick_practice_launch_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
