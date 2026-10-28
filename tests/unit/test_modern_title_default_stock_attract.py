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

    def test_wake_disarms_previous_main_before_source_title_exit(self):
        # Real Start exits a racing demo through stock TITLE 84 before MAIN.
        # Reusing the old D7 observation would immediately reveal that
        # transient TITLE as a new attract on a just-woken Modern title.
        wake = self.source.split("void wake_original_stock_attract() {", 1)[1].split(
            'extern "C" int ur_baldosa_modern_root_key(', 1
        )[0]
        self.assertIn("g_original_attract_seen_main = false;", wake)
        self.assertLess(
            wake.index("g_original_attract_seen_main = false;"),
            wake.index("g_original_attract_visible = false;"))
        rearm = self.source.split(
            "// The original guest's *observed* MAIN D7 -> TITLE 84 transition,", 1
        )[1].split(
            "if (g_visible && ur::product::modern_title_active(g_title))", 1
        )[0]
        self.assertIn("if (!guest_in_race && source_menu == 0xd7u)", rearm)
        self.assertIn("g_original_attract_seen_main = true;", rearm)
        self.assertIn("if (g_original_attract_seen_main && !guest_in_race &&", rearm)

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

    def test_real_p1_start_is_the_only_guest_demo_exit_bridge(self):
        bridge = (ROOT / "tools/baldosa_native_product_execution.cpp").read_text(
            encoding="utf-8")
        handler = self.source.split(
            'extern "C" int ur_baldosa_modern_root_gamepad(', 1
        )[1].split(
            'extern "C" int ur_baldosa_modern_root_window_base_width(', 1
        )[0]
        self.assertIn("button == kGamepadBtn_Start && !pressed", handler)
        self.assertIn("button == kGamepadBtn_Start && g_ram[0x0313u] == 1u",
                      handler)
        self.assertIn("if (genuine_p1_start_in_demo)", handler)
        self.assertIn("ur_baldosa_product_attract_p1_start_event(1);", handler)
        self.assertIn("ur_baldosa_product_attract_p1_start_event(0);", handler)
        self.assertIn("host_owned && g_attract_p1_physical_start_held", bridge)
        self.assertIn("g_attract_source_demo_observed ? 0x0008u : 0u", bridge)
        self.assertIn("ur_baldosa_product_attract_source_demo_observed(g_ram[0x0313u] == 1u)", self.source)
        self.assertIn("if (!g_attract_source_demo_observed)", bridge)
        self.assertIn("g_attract_p1_physical_start_held = false;", bridge)
        self.assertIn("filtered | static_cast<std::uint32_t>(g_pending_stock_menu_mask) |",
                      bridge)
        self.assertIn("live_demo_start;", bridge)
        self.assertIn("quick_practice_runner_mask_is_discrete_menu_input(mask)",
                      bridge)
        # Original real-start bridge does not widen the scripted Accept
        # vocabulary or treat P2 as P1. No automatic criterion promotion.
        self.assertNotIn("quick_practice_runner_mask_is_discrete_menu_input(mask) ||",
                         bridge)
        self.assertLess(handler.index("if (player != 0) return 0;"),
                        handler.index("if (genuine_p1_start_in_demo)"))

    def test_rapid_exit_fixture_requires_source_d7_and_fresh_confirm(self):
        section = self.source.split('// CI-only mode 35:', 1)[1].split(
            '// CI-only mode 28:', 1)[0]
        self.assertIn("mode < 1 || mode > 36", self.source)
        self.assertIn('std::strcmp(fixture, "35") != 0', self.source)
        self.assertIn('frame == 1600', section)
        self.assertIn('kGamepadBtn_Start, 1', section)
        self.assertIn('kGamepadBtn_Start, 0', section)
        self.assertIn('original_stock_attract_source_ready()', section)
        self.assertIn('kQuickPracticeMenuSettleObservations', section)
        self.assertIn('frame == 1940', section)
        self.assertIn('frame == 1960', section)
        self.assertIn('kGamepadBtn_A, 1', section)
        self.assertIn('rapid_start_root_ready=1', section)
        self.assertNotIn('g_ram[0x009fu] =', section)


    def test_separate_start_after_a_wake_exits_original_demo_without_host_confirm(self):
        handler = self.source.split(
            'extern "C" int ur_baldosa_modern_root_gamepad(', 1
        )[1].split(
            'extern "C" int ur_baldosa_modern_root_window_base_width(', 1
        )[0]
        region = handler.split("if (g_visible && g_original_attract_woken &&", 1)[1].split(
            "if (!g_visible)", 1
        )[0]
        for required in (
            "ur::product::modern_title_active(g_title)",
            "button == kGamepadBtn_Start && first_press",
            "g_ram[0x0313u] == 1u && g_stock_target == -1",
            "ur_baldosa_product_attract_p1_start_event(1);",
            "post_wake_real_start_to_demo=1",
        ):
            self.assertIn(required, region)
        self.assertNotIn("confirm_modern_native_title()", region)
        self.assertLess(handler.index("if (player != 0) return 0;"),
                        handler.index("if (g_visible && g_original_attract_woken &&"))
        fixture = self.source.split("// CI-only mode 36:", 1)[1].split(
            "// CI-only mode 35:", 1
        )[0]
        for required in (
            'std::strcmp(opt, "36") == 0',
            "frame == 1600", "kGamepadBtn_A, 1",
            "frame == 1602", "kGamepadBtn_A, 0",
            "frame == 1604", "kGamepadBtn_Start, 1",
            "frame == 1608", "kGamepadBtn_Start, 0",
            "frame == 1940", "original_stock_attract_source_ready()",
            "kQuickPracticeMenuSettleObservations",
            "frame == 1960", "frame == 1990",
            "post_wake_start_root_ready=1",
        ):
            self.assertIn(required, fixture)
        self.assertNotIn("g_ram[0x009fu] =", fixture)
        driver = (ROOT / "tools/qa_modern_visual_win32_capture_driver.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"stock-attract-post-wake-start-exit": ("36", 2000,', driver)

if __name__ == "__main__":
    unittest.main()
