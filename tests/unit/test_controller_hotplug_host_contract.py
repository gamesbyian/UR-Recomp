import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"


def _body(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    return source[start:source.index(end_marker, start)]


class ControllerHotplugHostContractTests(unittest.TestCase):
    def test_framework_connection_events_feed_the_seat_model(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            'extern "C" void ur_uniracers_modern_system_gamepad_source_connection(',
            'extern "C" int ur_uniracers_modern_system_gamepad_source_button(',
        )
        observe = body.index("ur::product::controller_hotplug_observe(")
        multiplayer = body.index("local_multiplayer_controller_source(")
        # Seat state is observed for every framework seat event, including
        # outside the local multiplayer join surface.
        self.assertLess(observe, multiplayer)
        self.assertIn("UR_CONTROLLER SEAT_%s", body)

    def test_disconnect_pause_uses_the_ordinary_session_command(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "void apply_controller_disconnect_pause() {",
            "#if SNESRECOMP_SDL3",
        )
        self.assertIn("controller_hotplug_take_pause(", body)
        self.assertIn("restart_surface()", body)
        self.assertIn("ur_modern_session_pause(g_session)", body)
        self.assertIn("controller_hotplug_clear_notices(", body)
        # No guest-memory, binding or seat authority is acquired here.
        for forbidden in ("g_ram[", "keybinds_set_button", "RtlTryWriteSram"):
            self.assertNotIn(forbidden, body)

    def test_disconnect_pause_runs_on_the_completed_frame_boundary(self):
        source = HOST.read_text(encoding="utf-8")
        focus = source.index("    apply_focus_pause_policy();\n    apply_controller_disconnect_pause();")
        self.assertGreater(focus, 0)

    def test_notice_and_device_line_are_presentation_only(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("controller_hotplug_notice_text(g_controller_hotplug)", source)
        self.assertIn('"PAD P1  %s"', source)

    def test_native_acceptance_covers_modern_and_authentic(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('"native/product/controller_hotplug_policy.hpp"', text)
        self.assertIn('"tests/input/modern-focus-pause.script"', text)
        self.assertIn("UR_CONTROLLER_HOTPLUG_ACCEPTANCE=1", text)
        self.assertIn("after=000 seat_connected=0 paused=1 modern=1", text)
        self.assertIn("after=000 seat_connected=0 paused=0 modern=0", text)
        self.assertIn('! grep -q "UR_CONTROLLER DISCONNECT_PAUSED" "$AUTHENTIC_LOG"', text)


if __name__ == "__main__":
    unittest.main()
