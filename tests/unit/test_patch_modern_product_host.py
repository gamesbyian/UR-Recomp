import pathlib
import tempfile
import unittest

from tools.patch_modern_product_host import (
    patch_cmake_text,
    patch_game_rtl_text,
    patch_main_text,
)


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernProductHostPatchTests(unittest.TestCase):
    def test_generated_main_receives_only_durable_callback_bindings(self):
        source = (
            '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
            'static const SnesDesktopHostGame kGameHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '    .num_players         = 2,\n'
            '};\n'
        )
        patched = patch_main_text(source)
        self.assertIn('#include "uniracers_modern_host.h"', patched)
        self.assertIn("ur_uniracers_modern_after_run_frame", patched)
        self.assertIn("ur_uniracers_modern_system_key_down", patched)
        self.assertIn("ur_uniracers_modern_system_gamepad_button", patched)
        self.assertIn("ur_uniracers_modern_system_overlay", patched)
        self.assertIn("ur_uniracers_modern_presentation_hz", patched)
        self.assertIn(".native_widescreen      = 1,", patched)
        self.assertIn("ur_uniracers_modern_prepare_frame", patched)
        self.assertIn("ur_uniracers_modern_compute_viewport", patched)
        self.assertNotIn("UR_RESTART_PROBE", patched)
        self.assertEqual(patch_main_text(patched), patched)

    def test_existing_modern_host_is_upgraded_with_presentation_hook(self):
        source = (
            'static const SnesDesktopHostGame kGameHost = {\n'
            '    .game_info           = &kGameInfo,\n'
            '    .after_run_frame       = &ur_uniracers_modern_after_run_frame,\n'
            '    .system_key_down       = &ur_uniracers_modern_system_key_down,\n'
            '    .system_gamepad_button = &ur_uniracers_modern_system_gamepad_button,\n'
            '    .system_overlay         = &ur_uniracers_modern_system_overlay,\n'
            '};\n'
        )
        patched = patch_main_text(source)
        self.assertIn("ur_uniracers_modern_presentation_hz", patched)
        self.assertIn("ur_uniracers_modern_prepare_frame", patched)
        self.assertIn("ur_uniracers_modern_compute_viewport", patched)
        self.assertEqual(patch_main_text(patched), patched)

    def test_generated_game_rtl_wires_existing_session_reset_hook(self):
        source = (
            "const RtlGameInfo kGameInfo = {\n"
            '    .save_name_prefix = "save",\n'
            "};\n\n"
            "void GameSessionReset(void) {\n"
            "    g_resume_pc = 0;\n"
            "}\n"
        )
        patched = patch_game_rtl_text(source)
        self.assertIn("void GameSessionReset(void);", patched)
        self.assertIn(".session_reset = &GameSessionReset,", patched)
        self.assertEqual(patch_game_rtl_text(patched), patched)

    def test_generated_cmake_links_project_owned_product_sources(self):
        source = "add_executable(UniracersSNESRecomp src/main.c)\n"
        patched = patch_cmake_text(source, ROOT)
        for name in (
            "output_resolution_policy.cpp",
            "output_resolution_runtime_policy.cpp",
            "widescreen_output_composition.cpp",
            "host_product_state.cpp",
            "host_product_store.cpp",
            "modern_session_c_api.cpp",
            "modern_pause_menu.cpp",
            "modern_pause_input.cpp",
            "modern_options_menu.cpp",
            "uniracers_modern_host.cpp",
            "uniracers_restart_policy.cpp",
            "uniracers_run_data.cpp",
        ):
            self.assertIn(name, patched)
        self.assertIn("# UR_MODERN_PRODUCT_HOST", patched)
        self.assertEqual(patch_cmake_text(patched, ROOT), patched)


if __name__ == "__main__":
    unittest.main()
