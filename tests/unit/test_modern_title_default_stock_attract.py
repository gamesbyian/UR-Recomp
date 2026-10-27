#!/usr/bin/env python3
"""Source contract for default stock attract and hidden-guest P2 isolation.

These checks protect the product wiring. Actual idle/wake and guest-input
behavior must also be observed on the same compiled Windows executable.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DefaultStockAttractSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8"
        )

    def test_default_idle_uses_observed_stock_transition_without_opt_in(self):
        source = self.source
        region = source.split(
            "// The original guest's *observed* MAIN D7 -> TITLE 84 transition,", 1
        )[1].split(
            "if (g_visible && ur::product::modern_title_active(g_title))", 1
        )[0]
        self.assertIn("g_original_attract_seen_main = true;", region)
        self.assertIn("source_menu == 0x84u", region)
        self.assertIn("g_original_attract_visible = true;", region)
        self.assertIn("g_visible = false;", region)
        self.assertNotIn("UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW", region)
        self.assertNotIn("std::getenv", region)
        self.assertIn("g_stock_target == -1", region)

    def test_p2_is_consumed_during_title_and_root_except_real_join(self):
        region = self.source.split(
            'extern "C" int ur_baldosa_modern_root_gamepad(', 1
        )[1].split(
            'extern "C" int ur_baldosa_modern_root_window_base_width(', 1
        )[0]
        self.assertIn("if (g_original_attract_visible && player == 1)", region)
        self.assertIn("button == g_original_attract_p2_release_button", region)
        isolation = (
            "if (player == 1 && g_visible && !g_two_seat_join.open())\n"
            "        return 1;"
        )
        self.assertIn(isolation, region)
        self.assertLess(region.index(isolation),
                        region.index("if (player == 1 && g_visible && g_two_seat_join.open())"))
        self.assertIn(
            "default: return 1; // host-owned join; no hidden guest P2 input",
            region,
        )
        self.assertIn("if (player == 1 && !g_visible && button == kGamepadBtn_B)",
                      region)

    def test_native_p2_wake_fixture_probes_different_followup_button(self):
        region = self.source.split(
            '// CI-only mode 22: unjoined P2 can wake true original demo', 1
        )[1].split(
            '// CI-only mode 20:', 1
        )[0]
        self.assertIn("frame == 1642", region)
        self.assertIn("SDL_SetJoystickVirtualButton(", region)
        self.assertIn("p2_pad, SDL_GAMEPAD_BUTTON_EAST, true", region)
        self.assertIn("p2_pad, SDL_GAMEPAD_BUTTON_EAST, false", region)
        self.assertIn("!p1_pad || !p2_pad", region)
        self.assertIn("p2_sdl_event_submitted=1", region)
        self.assertIn("p2_sdl_release_submitted=1", region)
        self.assertIn("p2_sdl_callback_received=1", self.source)
        self.assertIn("p2_other_button_isolated=1", region)


if __name__ == "__main__":
    unittest.main()
