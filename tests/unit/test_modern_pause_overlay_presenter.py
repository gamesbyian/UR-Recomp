#!/usr/bin/env python3
"""The native paused menu wires OPTIONS to the shared Options modal."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class NativePausedOptionsPresenterTest(unittest.TestCase):
    def test_presenter_links_and_renders(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "pause-presenter"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
                 "-pedantic", "-I", str(ROOT), "-I", str(PRODUCT),
                 str(ROOT / "tests/native/modern_pause_overlay_presenter_test.cpp"),
                 str(PRODUCT / "modern_pause_menu.cpp"), "-o", str(exe)],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("wires OPTIONS", run.stdout)

    def test_pause_lifecycle_routes_only_owned_edges_and_stays_frozen(self):
        source = (ROOT / "tools/baldosa_native_pause_lifecycle.cpp").read_text()
        for token in (
                "ur_baldosa_modern_root_pause_options_open()",
                "pause_options_edge(",
                "g_pause_options_keys[6]",
                "g_pause_options_pad[7]",
                "no Restart while the Options panel is open",
                "ur_baldosa_modern_root_pause_options_draw(",
                "UR_BALDOSA_PAUSE_OPTIONS_SMOKE"):
            self.assertIn(token, source)
        # The panel never steps the guest: it only draws on the frozen raster
        # and routes edges; no guest-memory or controller-word write appears.
        block = source.split("bool pause_options_edge(", 1)[1].split(
            "void reset_native_pause_menu_on_open", 1)[0]
        for forbidden in ("g_ram", "g_sram", "RtlRunFrame", "SetPadButton"):
            self.assertNotIn(forbidden, block)


if __name__ == "__main__":
    unittest.main()
