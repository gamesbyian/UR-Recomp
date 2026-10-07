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
        self.assertIn(
            "draw_device_line(ur::product::LocalMultiplayerSlot::Player1, 42);",
            overlay,
        )
        self.assertIn(
            "draw_device_line(ur::product::LocalMultiplayerSlot::Player2, 62);",
            overlay,
        )

    def test_acceptance_uses_real_sdl_pad_buttons(self):
        source = HOST.read_text(encoding="utf-8")
        hook = _body(
            source,
            "void run_local_multiplayer_join_acceptance() {",
            "\n}\n",
        )
        self.assertIn("attach_local_multiplayer_acceptance_pad(", hook)
        self.assertIn("detach_local_multiplayer_acceptance_pad(pad_index)", hook)
        self.assertIn("SDL_SetJoystickVirtualButton(pad, action.button, true)", hook)
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", source)
        # Joins and confirms must arrive through the framework callbacks, not
        # by calling the host's join helpers directly.
        for shortcut in (
            "local_multiplayer_assign_source(",
            "local_multiplayer_confirm_profile(",
            "ur_uniracers_modern_system_gamepad_source_button(",
        ):
            self.assertNotIn(shortcut, hook)

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
            "JOIN_MODE=disconnect run_native disconnect",
            "SEAT slot=P2 device=CONTROLLER DISCONNECTED",
            "DETACHED pad=2 ready=0 overlay=1",
            'test "$REJOIN" -lt "$DREADY"',
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run_modern_two_player_join_acceptance.sh", workflow)
        self.assertIn('"native/product/local_multiplayer_*"', workflow)


if __name__ == "__main__":
    unittest.main()
