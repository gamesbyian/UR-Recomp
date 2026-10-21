"""Pixel-level regression for overlapping root/child Modern drawing.

This intentionally crude ROM-free block-font fixture checks only the source
painter's rectangle ordering at 256 and 342 logical widths, not SDL final
output, hardware or artistic acceptance.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "tests/native/modern_native_destination_layering_test.cpp"
HOST = ROOT / "tools/baldosa_native_modern_root.cpp"


class ModernNativeDestinationLayeringTest(unittest.TestCase):
    def test_real_native_draw_hook_keeps_shell_and_child_order(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("auto shell_view = view;", source)
        self.assertIn("root_rect, shell_view);", source)
        self.assertIn("root_rect, view);", source)
        self.assertLess(source.index("root_rect, shell_view);"),
                        source.index("root_rect, view);"))
        for flag in ("options_open", "read_only_records_open",
                     "two_seat_join_open", "first_racer_open",
                     "practice_picker_open", "practice_launch_pending",
                     "unbound_two_player_warning_open"):
            self.assertIn(f"shell_view.{flag} = false;", source)

    def test_real_source_painters_leave_no_root_ink_through_child(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as d:
            binary = Path(d) / "layering"
            command = [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                       "-Werror", "-pedantic", "-I", str(ROOT),
                       str(CPP), "-o", str(binary)]
            build = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0,
                             build.stdout + build.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0,
                             run.stdout + run.stderr)
            # Ten substantive child states at both real native geometries.
            # Count actual per-state raster passes, never the final PASS line.
            self.assertEqual(sum(line.startswith("occlusion ")
                                 for line in run.stdout.splitlines()), 20)
            for state in ("options-help", "practice-entering", "records-2p",
                          "two-seat-join", "profile-switch"):
                self.assertIn(f"occlusion {state} 256x224", run.stdout)
                self.assertIn(f"occlusion {state} 342x224", run.stdout)
            self.assertIn("PASS: destination occlusion", run.stdout)


if __name__ == "__main__":
    unittest.main()
