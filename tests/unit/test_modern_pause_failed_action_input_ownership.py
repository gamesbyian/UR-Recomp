"""Pause and Quit confirmations remain host-owned on action failure.

These source-bound contracts do not substitute for actual Windows fault
injection, controller/audio acceptance, or a physical-device journey.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


def section(source: str, begin: str, end: str) -> str:
    start = source.index(begin)
    return source[start:source.index(end, start)]


class PauseFailedActionOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding="utf-8")
        cls.keyboard = section(
            source,
            'extern "C" int ur_uniracers_modern_system_key_down(',
            'extern "C" int ur_uniracers_modern_controls_active(',
        )
        cls.pad = section(
            source,
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
        )
        cls.source = source

    def test_keyboard_quit_confirm_consumed_on_sdl_failure(self):
        body = section(self.keyboard, "if (g_quit_confirm_visible &&",
                       "\n    if (g_options_visible)")
        self.assertIn("(void)request_desktop_quit();", body)
        self.assertIn("return 1;", body)
        self.assertNotIn("return request_desktop_quit() ? 1 : 0;", body)

    def test_physical_pad_quit_confirm_consumed_on_sdl_failure(self):
        body = section(self.pad,
                       "if (g_quit_confirm_visible && button == kGamepadBtn_A)",
                       "\n    if (g_options_visible)")
        self.assertIn("(void)request_desktop_quit();", body)
        self.assertIn("return 1;", body)
        self.assertNotIn("return request_desktop_quit() ? 1 : 0;", body)

    def test_keyboard_pause_confirm_consumed_on_failed_action(self):
        body = section(self.keyboard,
                       "if (paused() && (key == SDLK_RETURN || key == SDLK_KP_ENTER))",
                       "\n    if (modern_mode() && key == SDLK_r")
        self.assertIn("const bool handled = activate_pause_selection();", body)
        self.assertIn("if (restarting && !handled)", body)
        self.assertIn("g_restart_return_release = {};", body)
        self.assertIn("return 1;", body)
        self.assertNotIn("return handled ? 1 : 0;", body)

    def test_physical_pad_pause_confirm_consumed_on_failed_action(self):
        body = section(self.pad, "if (!paused()) return 0;",
                       "\n    if (button == kGamepadBtn_B)")
        self.assertIn("(void)activate_pause_selection();", body)
        self.assertIn("return 1;", body)
        self.assertNotIn("return activate_pause_selection() ? 1 : 0;", body)

    def test_failure_paths_remain_real(self):
        focus = section(self.source, "bool toggle_focus_pause_setting() {",
                        "bool toggle_vibration_setting() {")
        self.assertIn("if (!persist_product_state(candidate))", focus)
        self.assertIn("return false;", focus)
        quit_request = section(self.source, "bool request_desktop_quit() {",
                               "void maybe_run_exit_frontend_acceptance() {")
        self.assertIn("if (SDL_PushEvent(&event) != 1)", quit_request)
        self.assertIn("return false;", quit_request)


if __name__ == "__main__":
    unittest.main()
