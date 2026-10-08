import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
HARNESS = ROOT / "tests/native/run_modern_frontend_options_acceptance.sh"


class ModernFrontendOptionsHostContractTests(unittest.TestCase):
    def test_frontend_admission_is_settled_modern_only(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("bool open_frontend_options()")
        end = source.index("bool request_desktop_quit()", start)
        body = source[start:end]
        for forbidden in (
            "!modern_mode()", "paused()", "g_ram[0x009F] != 0xD7",
            "g_ram[0x0313] == 0x01", "g_practice_active",
            "g_progress_overview_visible", "g_practice_picker.visible",
            "tour_continue_routing()", "g_exit_frontend_waiting_for_main",
            "g_exit_frontend_waiting_for_usable",
        ):
            self.assertIn(forbidden, body)
        self.assertIn("ur_modern_options_menu_reset(&g_options_menu)", body)
        self.assertIn("g_options_visible = true", body)
        self.assertNotIn("ur_modern_session_pause(", body)
        self.assertNotIn("ur_modern_session_exit_to_frontend(", body)

    def test_input_consumption_and_existing_settings_authority(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("key == SDLK_F10", source)
        self.assertIn("pressed && control == 4 && open_frontend_options()", source)
        self.assertIn("if (g_frontend_options_active && g_options_visible)", source)
        self.assertIn("return -1;", source)
        self.assertIn("case 6: (void)activate_options_selection();", source)
        self.assertIn("g_frontend_options_active = false", source)
        self.assertIn("g_suppress_human_input_once = true", source)
        self.assertIn("host_owns_human_player_input()", source)
        self.assertIn("g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01", source)

    def test_same_renderer_serves_frontend_and_pause(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("if (is_paused || frontend_options)", source)
        self.assertIn("if (!frontend_options) {", source)
        self.assertIn('"UR_FRONTEND_OPTIONS PRESENT scale=%d', source)
        self.assertIn("if (frontend_options && !g_frontend_options_draw_reported", source)
        self.assertEqual(source.count('"OPTIONS", 0xFFFFFFFFu, modal_scale'), 1)
        self.assertIn('"F10/PAD SELECT OPTIONS"', source)

    def test_native_frontend_and_authentic_gate(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        body = HARNESS.read_text(encoding="utf-8")
        self.assertIn("run_case modern", body)
        self.assertIn("run_case authentic", body)
        self.assertIn("UR_FRONTEND_OPTIONS PRESENT", body)
        self.assertIn("UR_VOLUME SELECTED percent=", body)
        flow = (ROOT / ".github/workflows/modern-onboarding-practice-acceptance.yml").read_text(encoding="utf-8")
        self.assertIn("run_case frontend-options run_modern_frontend_options_acceptance.sh", flow)


if __name__ == "__main__":
    unittest.main()
