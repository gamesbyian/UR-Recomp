import pathlib
import tempfile
import unittest

from tools.patch_modern_product_host import patch_cmake_text, patch_main_text


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
        self.assertNotIn("UR_RESTART_PROBE", patched)
        self.assertEqual(patch_main_text(patched), patched)

    def test_generated_cmake_links_project_owned_product_sources(self):
        source = "add_executable(UniracersSNESRecomp src/main.c)\n"
        patched = patch_cmake_text(source, ROOT)
        for name in (
            "host_product_state.cpp",
            "host_product_store.cpp",
            "modern_session_c_api.cpp",
            "modern_pause_menu.cpp",
            "modern_pause_input.cpp",
            "uniracers_modern_host.cpp",
            "uniracers_restart_policy.cpp",
            "uniracers_run_data.cpp",
        ):
            self.assertIn(name, patched)
        self.assertIn("# UR_MODERN_PRODUCT_HOST", patched)
        self.assertEqual(patch_cmake_text(patched, ROOT), patched)


if __name__ == "__main__":
    unittest.main()
