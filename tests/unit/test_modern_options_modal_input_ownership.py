"""Source-bound guard for Options input ownership on failed settings writes.

A settings apply/save may fail, but the host-owned modal must still consume
Confirm and volume direction keys. This is not a physical input acceptance.
"""

from pathlib import Path
import unittest


HOST = Path(__file__).resolve().parents[2] / "native/product/uniracers_modern_host.cpp"


def _between(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


class ModernOptionsModalInputOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding="utf-8")
        keyboard = _between(
            source,
            'extern "C" int ur_uniracers_modern_system_key_down(',
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
        )
        physical_pad = _between(
            source,
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
        )
        cls.keyboard_options = _between(
            keyboard,
            "if (g_options_visible) {",
            "if (host_subview_visible() && key == SDLK_ESCAPE)",
        )
        cls.pad_options = _between(
            physical_pad,
            "if (g_options_visible) {",
            "if (host_subview_visible())",
        )
        cls.source = source

    def test_keyboard_confirm_consumed_even_if_settings_apply_fails(self):
        branch = _between(
            self.keyboard_options,
            "if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {",
            "\n        }",
        )
        self.assertIn("(void)activate_options_selection();", branch)
        self.assertIn("return 1;", branch)
        self.assertNotIn("return activate_options_selection()", branch)

    def test_physical_pad_confirm_consumed_even_if_settings_apply_fails(self):
        branch = _between(
            self.pad_options,
            "if (button == kGamepadBtn_A) {",
            "\n        }",
        )
        self.assertIn("(void)activate_options_selection();", branch)
        self.assertIn("return 1;", branch)
        self.assertNotIn("return activate_options_selection()", branch)

    def test_volume_arrows_remain_host_owned_on_failure(self):
        self.assertIn(
            "(void)step_volume_setting(key == SDLK_RIGHT ? 1 : -1);\n"
            "            return 1;",
            self.keyboard_options,
        )
        self.assertIn(
            "(void)step_volume_setting(\n"
            "                button == kGamepadBtn_DpadRight ? 1 : -1);\n"
            "            return 1;",
            self.pad_options,
        )

    def test_setting_failure_is_real_not_hypothetical(self):
        focus = _between(
            self.source,
            "bool toggle_focus_pause_setting() {",
            "bool toggle_vibration_setting() {",
        )
        self.assertIn("if (!persist_product_state(candidate))", focus)
        self.assertIn("return false;", focus)


if __name__ == "__main__":
    unittest.main()
