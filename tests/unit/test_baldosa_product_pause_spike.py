#!/usr/bin/env python3
"""Guard the exact pinned Baldosa pause pump and nonshipping native smoke."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_product_pause_spike as spike


class NativePauseIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.header = (
            "/* UR_BALDOSA_PRODUCT_INPUT_SEAM */\n"
            + spike.HEADER
            + spike.PUBLIC
        )
        self.host = (
            "/* UR_BALDOSA_PRODUCT_INPUT_SEAM */\n"
            "static bool g_netplay_session;\n"
            + spike.GLOBAL +
            spike.EVENT +
            "static void HandleCommand(unsigned j) {\n" +
            spike.LEGACY_COMMAND +
            "}\n" +
            spike.PAUSE_GATE +
            "    if (g_paused && !g_savestate_menu_hotkey) {\n"
            "      HostSleepMs(16);\n      continue;\n    }\n"
        )
        self.main = (
            "/* UR_BALDOSA_PRODUCT_INPUT_SEAM */\n"
            + spike.HOST + spike.STAT
        )

    def test_real_host_offline_pause_and_pump_wiring(self):
        head = spike.patch_host_header(self.header)
        self.assertEqual(head.count(spike.MARK), 1)
        self.assertIn("filter_human_frame_inputs", head)
        self.assertIn("void (*product_tick)(void);", head)
        self.assertIn("snesrecomp_desktop_product_set_paused", head)
        self.assertEqual(spike.patch_host_header(head), head)

        host = spike.patch_host_source(self.host)
        self.assertEqual(host.count(spike.MARK), 4)
        self.assertIn("if (g_product_pause_owned) {", host)
        self.assertIn("default: return;", host)
        self.assertIn("g_savestate_menu_hotkey = g_rewind_hotkey = g_open_launcher_hotkey = 0;", host)
        self.assertIn("if (g_netplay_session) return 0", host)
        self.assertIn("if (g_paused && !g_product_pause_owned) return 0", host)
        self.assertIn("if (!g_product_pause_owned) return 0", host)
        self.assertIn("if (game->product_tick) game->product_tick();", host)
        self.assertLess(host.index("game->product_tick"), host.index("if (g_paused && !g_savestate_menu_hotkey)"))
        self.assertEqual(spike.patch_host_source(host), host)

        game = spike.patch_game_main(self.main)
        self.assertIn("ur_baldosa_product_after_run_frame", game)
        self.assertIn("ur_baldosa_product_host_tick", game)
        self.assertEqual(spike.patch_game_main(game), game)

    def test_guard_rejects_unknown_host_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "input host"):
            spike.patch_host_header(self.header.replace(spike.REQUIRED, "UNKNOWN"))
        with self.assertRaisesRegex(ValueError, "SDL event"):
            spike.patch_host_source(self.host.replace(spike.EVENT, ""))
        with self.assertRaisesRegex(ValueError, "native human-input"):
            spike.patch_game_main(self.main.replace(spike.REQUIRED, "UNKNOWN"))

    def test_cmake_stages_single_extra_title_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools/baldosa_native_pause_lifecycle.cpp").write_text("// smoke")
            initial = "# UR_BALDOSA_PRODUCT_INPUT_SEAM\n"
            result = spike.patch_game_cmake(initial, root)
            self.assertTrue(result.startswith(initial))
            self.assertEqual(result.count(spike.MARK), 1)
            self.assertIn("baldosa_native_pause_lifecycle.cpp", result)
            self.assertEqual(spike.patch_game_cmake(result, root), result)
            with self.assertRaisesRegex(ValueError, "native human-input"):
                spike.patch_game_cmake("unrecognized CMake", root)

    def test_atomic_plan_rejects_mismatched_framework_before_any_file_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "baldosa"
            (root / "tools").mkdir()
            (root / "tools/baldosa_native_pause_lifecycle.cpp").write_text("// smoke")
            (game / "src").mkdir(parents=True)
            (game / "snesrecomp/runner/src/desktop").mkdir(parents=True)
            (game / "src/main.c").write_text(self.main)
            (game / "CMakeLists.txt").write_text("# UR_BALDOSA_PRODUCT_INPUT_SEAM\n")
            (game / "snesrecomp/runner/src/desktop/host_main.h").write_text(self.header)
            (game / "snesrecomp/runner/src/desktop/host_main.c").write_text("BROKEN")
            with self.assertRaises(ValueError):
                spike.plan(game, root)
            self.assertEqual((game / "src/main.c").read_text(), self.main)


if __name__ == "__main__":
    unittest.main()
