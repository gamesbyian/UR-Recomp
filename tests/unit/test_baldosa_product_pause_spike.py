#!/usr/bin/env python3
"""Guard the exact pinned Baldosa pause pump and nonshipping native smoke."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_product_pause_spike as spike


class NativePauseIntegrationTest(unittest.TestCase):
    @staticmethod
    def stage_modern_sources(root):
        modern = root / "native/product"
        modern.mkdir(parents=True)
        (root / "tools/baldosa_native_modern_root.cpp").write_text(
            "// shared root consumer")
        for name in spike.MODERN_SESSION_SOURCES:
            (modern / name).write_text("// Modern session build fixture")
        (modern / spike.NATIVE_RESULT_BRIDGE_SOURCE).write_text(
            "// genuine native result bridge build fixture")
        (modern / spike.NATIVE_RESULT_RECORDER_SOURCE).write_text(
            "// canonical run recorder build fixture")
        title = root / "native/title"
        title.mkdir(parents=True)
        for name in spike.NATIVE_TITLE_RESULT_SOURCES:
            (title / name).write_text("// title-owned result observer fixture")

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
            spike.KEY_EVENT +
            "}\n" +
            spike.PAD_EVENT +
            "}\n" +
            "static void HandleCommand(unsigned j) {\n" +
            spike.LEGACY_COMMAND +
            "}\n" +
            spike.PAUSE_GATE +
            "    if (g_paused && !g_savestate_menu_hotkey) {\n"
            "      HostSleepMs(16);\n      continue;\n    }\n"
            "  ComposeOsd(pixel_buffer, pitch, draw_w, draw_h, draw_w >= 512 ? 1 : 2);\n"
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
        self.assertIn("product_system_key", head)
        self.assertIn("product_system_gamepad", head)
        self.assertIn("snesrecomp_desktop_product_set_paused", head)
        self.assertEqual(spike.patch_host_header(head), head)

        host = spike.patch_host_source(self.host)
        self.assertEqual(host.count(spike.MARK), 5)
        self.assertIn("if (g_product_pause_owned) {", host)
        self.assertIn("PresentFrozenWithOverlay();", host)
        self.assertIn("g_game->product_pause_draw(pixel_buffer", host)
        self.assertIn("int (*product_pause_draw)(uint8_t*, size_t, int, int);", head)
        self.assertLess(host.index("g_game->product_pause_draw(pixel_buffer"),
                        host.index("ComposeOsd(pixel_buffer, pitch, draw_w, draw_h"))
        self.assertIn("++g_product_pause_presentations;", host)
        self.assertIn("unsigned snesrecomp_desktop_product_pause_presentations", head)
        self.assertLess(host.index("PresentFrozenWithOverlay();"),
                        host.index("if (g_paused && !g_savestate_menu_hotkey"))
        self.assertNotIn("RtlRunFrame(", host)
        self.assertNotIn("draw_ppu_frame(", host)
        self.assertIn("default: return;", host)
        self.assertIn("g_savestate_menu_hotkey = g_rewind_hotkey = g_open_launcher_hotkey = 0;", host)
        self.assertIn("if (g_netplay_session) return 0", host)
        self.assertIn("if (g_paused && !g_product_pause_owned) return 0", host)
        self.assertIn("if (!g_product_pause_owned) return 0", host)
        self.assertIn("if (game->product_tick) game->product_tick();", host)
        self.assertIn("g_game->product_system_key(keyCode, pressed ? 1 : 0)", host)
        self.assertIn("g_game->product_system_gamepad(gi->index, button, pressed ? 1 : 0)", host)
        self.assertLess(host.index("g_game->product_system_key(keyCode"),
                        host.index("FindCmdForSdlKey(keyCode"))
        self.assertLess(host.index("g_game->product_system_gamepad(gi->index"),
                        host.index("gi->last_cmd[button] = FindCmdForGamepadButton")
                        if "FindCmdForGamepadButton" in host else len(host))
        self.assertLess(host.index("game->product_tick"), host.index("if (g_paused && !g_savestate_menu_hotkey)"))
        self.assertEqual(spike.patch_host_source(host), host)

        game = spike.patch_game_main(self.main)
        self.assertIn("ur_baldosa_product_after_run_frame", game)
        self.assertIn("ur_baldosa_product_host_tick", game)
        self.assertIn(".product_system_key", game)
        self.assertIn(".product_pause_draw", game)
        self.assertIn(".product_system_gamepad", game)
        self.assertEqual(spike.patch_game_main(game), game)

    def test_guard_rejects_unknown_host_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "input host"):
            spike.patch_host_header(self.header.replace(spike.REQUIRED, "UNKNOWN"))
        with self.assertRaisesRegex(ValueError, "SDL event"):
            spike.patch_host_source(self.host.replace(spike.EVENT, ""))
        with self.assertRaisesRegex(ValueError, "SDL event"):
            spike.patch_host_source(self.host.replace(spike.KEY_EVENT, ""))
        with self.assertRaisesRegex(ValueError, "SDL event"):
            spike.patch_host_source(self.host.replace(spike.PAD_EVENT, ""))
        with self.assertRaisesRegex(ValueError, "native human-input"):
            spike.patch_game_main(self.main.replace(spike.REQUIRED, "UNKNOWN"))

    def test_cmake_stages_single_extra_title_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools/baldosa_native_pause_lifecycle.cpp").write_text("// smoke")
            (root / "tools/baldosa_native_product_pause_authority.cpp").write_text("// authority")
            self.stage_modern_sources(root)
            initial = "# UR_BALDOSA_PRODUCT_INPUT_SEAM\n"
            result = spike.patch_game_cmake(initial, root)
            self.assertTrue(result.startswith(initial))
            self.assertEqual(result.count(spike.MARK), 1)
            self.assertIn("baldosa_native_pause_lifecycle.cpp", result)
            self.assertIn("baldosa_native_modern_root.cpp", result)
            self.assertIn("baldosa_native_product_pause_authority.cpp", result)
            self.assertIn("modern_session_c_api.cpp", result)
            self.assertIn("modern_session_runtime.cpp", result)
            self.assertIn("baldosa_guest_result_observer.cpp", result)
            self.assertIn("completed_run_record.cpp", result)
            self.assertIn("uniracers_run_data.cpp", result)
            self.assertIn("uniracers_two_player_result.cpp", result)
            self.assertIn("uniracers_course_identity.cpp", result)
            self.assertIn("target_include_directories(UniracersSNESRecomp PRIVATE", result)
            self.assertEqual(spike.patch_game_cmake(result, root), result)
            with self.assertRaisesRegex(ValueError, "native human-input"):
                spike.patch_game_cmake("unrecognized CMake", root)

    def test_atomic_plan_rejects_mismatched_framework_before_any_file_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "baldosa"
            (root / "tools").mkdir()
            (root / "tools/baldosa_native_pause_lifecycle.cpp").write_text("// smoke")
            (root / "tools/baldosa_native_product_pause_authority.cpp").write_text("// authority")
            self.stage_modern_sources(root)
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
