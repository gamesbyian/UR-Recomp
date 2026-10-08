import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
HARNESS = ROOT / "tests/native/run_modern_frontend_controls_acceptance.sh"


class ModernFrontendControlsHostContractTests(unittest.TestCase):
    def test_only_settled_modern_frontend_opens_controls(self):
        source = HOST.read_text(encoding="utf-8")
        open_body = source.split("bool open_frontend_controls() {", 1)[1].split(
            "bool request_desktop_quit()", 1
        )[0]
        self.assertIn("if (!open_frontend_options()) return false;", open_body)
        self.assertIn("g_options_visible = false;", open_body)
        self.assertIn("g_controls_rebind = {};", open_body)
        self.assertIn("g_controls_visible = true;", open_body)
        self.assertIn('UR_FRONTEND_CONTROLS OPENED', open_body)
        self.assertIn("key == SDLK_F9 && !paused()", source)
        self.assertIn("control == 8", source)

    def test_same_rebind_authority_and_return_to_frontend_options(self):
        source = HOST.read_text(encoding="utf-8")
        handler = source.split(
            "bool handle_controls_action(ur::product::ModernControlsAction action)", 1
        )[1].split("bool handle_controls_key(", 1)[0]
        self.assertIn("modern_controls_handle_action(", handler)
        self.assertIn("g_options_visible = true;", handler)
        self.assertIn("UR_FRONTEND_CONTROLS RETURNED_OPTIONS", handler)
        self.assertIn("UR_PAUSE_CONTROLS CLOSED", handler)
        self.assertIn("keybinds_set_button(", source)
        self.assertIn("keybinds_save();", source)
        self.assertIn("if (g_frontend_options_active && g_options_visible)", source)
        self.assertIn("if (is_paused || frontend_options)", source)
        self.assertIn("g_controls_visible) && !is_paused", source)

    def test_panel_renders_without_guest_menu_navigation(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("UR_FRONTEND_CONTROLS PRESENT scale=%d", source)
        self.assertIn('" CONTROLS / B BACK"', source)
        self.assertIn('"F9 CTRL F10/" + live_gamepad_binding_label(4) + " OPT"', source)
        self.assertIn("host_owns_human_player_input()", source)
        self.assertIn("modern_host_input_filter(", source)

    def test_native_gate_performs_real_binding_and_authentic_isolation(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        script = HARNESS.read_text(encoding="utf-8")
        for expected in (
            "run_case modern", "run_case authentic",
            "UR_FRONTEND_CONTROLS PRESENT scale=",
            "UR_CONTROLS command=2 binding=0", "UR_CONTROLS BINDINGS a=G",
            "UR_FRONTEND_CONTROLS RETURNED_OPTIONS",
            "UR_FRONTEND_OPTIONS CLOSED",
        ):
            self.assertIn(expected, script)
        workflow = (
            ROOT / ".github/workflows/modern-onboarding-practice-acceptance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "run_case frontend-controls run_modern_frontend_controls_acceptance.sh frontend-controls",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
