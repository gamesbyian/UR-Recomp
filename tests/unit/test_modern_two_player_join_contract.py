import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_two_player_join_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"


def _body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class ModernTwoPlayerJoinContractTests(unittest.TestCase):
    def test_device_line_reads_only_the_seat_projection(self):
        source = HOST.read_text(encoding="utf-8")
        line = _body(
            source,
            "std::string local_multiplayer_seat_device_line(",
            "void observe_local_multiplayer_seat_lines()",
        )
        self.assertIn("local_multiplayer_seat_presentation(", line)
        self.assertIn("local_multiplayer_seat_device_text(", line)
        self.assertIn("controller_display_name(assignment.source.stable_id - 1u)", line)
        for forbidden in ("g_ram[", "g_local_multiplayer_setup =", "keybinds_"):
            self.assertNotIn(forbidden, line)

    def test_join_overlay_draws_both_seat_device_lines(self):
        source = HOST.read_text(encoding="utf-8")
        overlay = _body(
            source,
            "if (g_local_multiplayer_join_visible && modern_mode()) {",
            "if (g_tour_action_visible && modern_mode()",
        )
        self.assertGreaterEqual(overlay.count("draw_device_line("), 3)
        self.assertIn("LocalMultiplayerSlot::Player1", overlay)
        self.assertIn("LocalMultiplayerSlot::Player2", overlay)
        self.assertIn(", 42);", overlay)
        self.assertIn(", 62);", overlay)

    def test_every_overlay_literal_fits_the_narrowest_panel(self):
        # 256-pixel frame -> 240-pixel panel -> 28 cells inside the margins.
        import re

        source = HOST.read_text(encoding="utf-8")
        overlay = _body(
            source,
            "if (g_local_multiplayer_join_visible && modern_mode()) {",
            "if (g_tour_action_visible && modern_mode()",
        )
        literals = re.findall(r'^\s+"([^"%\\]+)",', overlay, re.MULTILINE)
        literals += re.findall(r'scale,\s*"([^"%\\]+)",', overlay)
        self.assertGreaterEqual(len(literals), 5, literals)
        for text in literals:
            self.assertLessEqual(len(text), 28, text)
        self.assertIn("(panel_w_logical - 16) / 8", overlay)

    def test_acceptance_uses_real_sdl_pad_buttons(self):
        source = HOST.read_text(encoding="utf-8")
        hook = _body(
            source,
            "void run_local_multiplayer_join_acceptance() {",
            "\n}\n",
        )
        attach = _body(
            source,
            "bool attach_local_multiplayer_acceptance_pad(",
            "\n}\n",
        )
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", attach)
        self.assertIn("attach_local_multiplayer_acceptance_pad(0)", hook)
        self.assertIn("attach_local_multiplayer_acceptance_pad(1)", hook)
        self.assertIn("SDL_SetJoystickVirtualButton(pad, action.button, true)", hook)
        # Joins and confirms must arrive through the framework callbacks, not
        # by calling the host's join helpers directly.
        for shortcut in (
            "local_multiplayer_assign_source(",
            "local_multiplayer_confirm_profile(",
            "ur_uniracers_modern_system_gamepad_source_button(",
        ):
            self.assertNotIn(shortcut, hook)

    def test_disconnect_reopens_join_only_on_stock_2p_select(self):
        source = HOST.read_text(encoding="utf-8")
        callback = _body(
            source,
            'extern "C" void ur_uniracers_modern_system_gamepad_source_connection(',
            'extern "C" int ur_uniracers_modern_system_gamepad_source_button(',
        )
        self.assertIn("g_ram[0x009F] == 0x3D", callback)
        self.assertIn("g_local_multiplayer_join_visible = true;", callback)
        self.assertIn(
            'product_diagnostic("UR_LOCAL_MULTIPLAYER SOURCE_DISCONNECTED")',
            callback,
        )

    def test_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        for marker in (
            "SEAT slot=P1 device=PAD UR JOIN PAD ONE",
            "SEAT slot=P2 device=PAD UR JOIN PAD TWO",
            "UR_LOCAL_MULTIPLAYER PROFILE_DUPLICATE",
            'test "$DUP" -lt "$READY"',
            "DONE ready=1 overlay=0 p1=join.alpha p2=join.bravo",
            "UR_EXECUTION_MODE=authentic",
            "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE DETACHED pad=2 ready=0 overlay=1",
            "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE REATTACHED pad=2 ready=0 overlay=1",
            "UR_TWO_PLAYER_JOIN_DISCONNECT=blocked_while_unplugged rejoined ready",
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run_modern_two_player_join_acceptance.sh", workflow)
        self.assertIn('"native/product/local_multiplayer_*"', workflow)


if __name__ == "__main__":
    unittest.main()
