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
        self.assertIn('#include "completed_run_browser_host.h"', patched)
        self.assertIn("ur_uniracers_modern_after_config", patched)
        self.assertIn("ur_uniracers_product_after_run_frame", patched)
        self.assertIn("ur_uniracers_product_system_key_down", patched)
        self.assertIn("ur_uniracers_product_system_gamepad_button", patched)
        self.assertIn("ur_uniracers_product_system_gamepad_control", patched)
        self.assertIn("ur_uniracers_modern_filter_player_input", patched)
        self.assertIn("ur_uniracers_modern_system_gamepad_source_button", patched)
        self.assertIn("ur_uniracers_modern_system_gamepad_source_connection", patched)
        self.assertIn("ur_uniracers_product_system_overlay", patched)
        self.assertIn("ur_uniracers_modern_after_config", patched)
        self.assertIn("ur_uniracers_modern_presentation_hz", patched)
        self.assertIn(".native_widescreen      = 1,", patched)
        self.assertIn("ur_uniracers_modern_native_widescreen_enabled", patched)
        self.assertIn("ur_uniracers_modern_prepare_frame", patched)
        self.assertIn("ur_uniracers_modern_compute_viewport", patched)
        self.assertIn("ur_uniracers_modern_begin_sim_frame", patched)
        self.assertIn("ur_uniracers_modern_draw_frame", patched)
        self.assertIn("ur_uniracers_modern_presentation_scale", patched)
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
        self.assertIn("ur_uniracers_product_after_run_frame", patched)
        self.assertIn("ur_uniracers_product_system_key_down", patched)
        self.assertIn("ur_uniracers_product_system_gamepad_button", patched)
        self.assertIn("ur_uniracers_product_system_gamepad_control", patched)
        self.assertIn("ur_uniracers_modern_system_gamepad_source_button", patched)
        self.assertIn("ur_uniracers_modern_system_gamepad_source_connection", patched)
        self.assertIn("ur_uniracers_product_system_overlay", patched)
        self.assertIn("ur_uniracers_modern_presentation_hz", patched)
        self.assertIn("ur_uniracers_modern_native_widescreen_enabled", patched)
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
            "regional_presentation_secret.cpp",
            "regional_presentation_runtime.cpp",
            "regional_presentation_input_coordinator.cpp",
        "regional_title_presenter.cpp",
            "modern_racer_identity.cpp",
            "clean_stock_sram.cpp",
            "host_profile_catalog.cpp",
            "host_profile_state.cpp",
            "host_profile_store.cpp",
            "host_profile_runtime.cpp",
            "completed_run_record.cpp",
            "completed_run_capture.cpp",
            "completed_run_comparison.cpp",
            "completed_run_presentation.cpp",
            "completed_run_store.cpp",
            "completed_run_catalog.cpp",
            "completed_run_profile_sources.cpp",
            "completed_run_browser.cpp",
            "completed_run_replay.cpp",
            "completed_run_browser_host.cpp",
            "completed_run_ghost.cpp",
            "completed_run_ghost_policy.cpp",
            "completed_run_ghost_world_sample.cpp",
            "completed_run_ghost_projection.cpp",
            "completed_run_ghost_frame.cpp",
            "completed_run_ghost_trace.cpp",
            "racer_replacement_selector.cpp",
            "racer_guest_snapshot.cpp",
            "racer_oam_placement.cpp",
            "racer_hd_presenter.cpp",
            "completed_run_ghost_racer_selector.cpp",
            "completed_run_ghost_raster.cpp",
            "modern_session_c_api.cpp",
            "modern_pause_menu.cpp",
            "modern_pause_input.cpp",
            "modern_options_menu.cpp",
            "modern_controls_rebind.cpp",
            "modern_controls_binding_authority.cpp",
            "modern_controls_presenter.cpp",
            "modern_overlay_composition.cpp",
            "presentation_density_compositor.cpp",
            "uniracers_modern_host.cpp",
            "uniracers_restart_policy.cpp",
            "uniracers_course_identity.cpp",
            "uniracers_run_data.cpp",
            "uniracers_ws_margins.c",
            "uniracers_tour_resume.cpp",
            "uniracers_challenge_generation.cpp",
            "uniracers_challenge_generation_runtime.cpp",
            "uniracers_challenge_qualification.cpp",
            "uniracers_challenge_award.cpp",
            "uniracers_challenge_completion_runtime.cpp",
            "uniracers_challenge_generation_bridge.c",
        ):
            self.assertIn(name, patched)
        self.assertIn('native/presentation', patched)
        self.assertIn("# UR_MODERN_PRODUCT_HOST", patched)
        self.assertEqual(patch_cmake_text(patched, ROOT), patched)


if __name__ == "__main__":
    unittest.main()
