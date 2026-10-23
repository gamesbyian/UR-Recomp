#!/usr/bin/env python3
"""Guard source and native behavior of Baldosa Modern root physical input."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/baldosa_native_modern_root.cpp"
HEADER = ROOT / "native/product/modern_root_physical_edges.hpp"
TEST = ROOT / "tests/native/modern_root_physical_edges_test.cpp"


class BaldosaRootPhysicalEdgesTests(unittest.TestCase):
    def test_single_authority_and_real_sdl_repeat_is_tested(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('#include "modern_root_physical_edges.hpp"', source)
        self.assertIn("g_navigation_edges.keyboard(physical, pressed != 0)", source)
        self.assertIn("g_navigation_edges.p1_gamepad(physical, pressed != 0)", source)
        self.assertIn("if (player != 0) return 0;", source)
        self.assertIn("key == SDLK_DOWN && frame == 60", source)
        self.assertIn("if (SDL_PushEvent(&event) != 1) std::abort();", source)
        self.assertIn("return key == SDLK_ESCAPE && first_press &&", source)
        self.assertIn("return button == kGamepadBtn_B && first_press &&", source)
        self.assertNotIn("RtlRunFrame(", source)
        self.assertNotRegex(source, r"g_ram\\[0x009f\\]\\s*=(?!=)")

    def test_orphan_p2_stock_reentry_is_guarded_and_edge_triggered(self):
        source = SOURCE.read_text(encoding="utf-8")
        # This is the actual source handler, not a mock policy function.
        # The P2 exception must precede the ordinary P1-only navigation gate.
        orphan = source.index(
            "if (player == 1 && !g_visible && button == kGamepadBtn_B)")
        p1_only = source.index("if (player != 0) return 0;", orphan)
        branch = source[orphan:p1_only]
        self.assertIn("g_p2_join_edges.p1_gamepad(4, pressed != 0)", branch)
        self.assertIn("!fresh_press", branch)
        self.assertIn("snesrecomp_desktop_product_seat_source(0) != -1", branch)
        self.assertIn("snesrecomp_desktop_product_seat_source(1) == -1", branch)
        self.assertIn("reopen_on_observed_stock_main()", branch)
        # The shared authority still rejects active races, unobserved
        # handoffs, pending stock transitions and an unsettled stock menu.
        authority = source[source.index("bool reopen_on_observed_stock_main()"):]
        authority = authority[:authority.index("void select_records_page(")]
        for guard in (
            "!configured()", "g_visible", "!g_stock_handed_off",
            "g_stock_target != -1", "g_ram[0x009f] != 0xd7u",
            "g_ram[0x0313] == 0x01u",
        ):
            self.assertIn(guard, authority)

    def test_native_cpp_edge_contract(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "root-physical-edges"
            result = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(binary)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("PASS: native Modern root keyboard/P1", result.stdout)


if __name__ == "__main__":
    unittest.main()
