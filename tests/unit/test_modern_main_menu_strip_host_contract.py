import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_recent_course_persistence_acceptance.sh"


class ModernMainMenuStripHostContractTests(unittest.TestCase):
    def test_strip_replaces_loose_hints_and_uses_overlay_composition(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("ur::product::build_modern_main_menu_strip(strip_input)", source)
        self.assertEqual(source.count("build_modern_main_menu_strip("), 1)
        # The two loose hints that overlapped stock OPTIONS are gone.
        self.assertNotIn('"F3 / PAD Y  NEXT EVENT: %.*s"', source)
        self.assertNotIn('"%s  RECENT: %s"', source)
        start = source.index("// Modern main-menu continue strip:")
        block = source[start:source.index("if (modern_mode() && practice_routing())", start)]
        self.assertIn("resolve_modern_overlay_composition(request)", block)
        self.assertIn("HostOverlayAnchor::BottomCenter", block)
        self.assertIn("g_ram[0x009F] == 0xD7", block)
        # Presentation only: no guest-memory assignment.
        self.assertIsNone(re.search(r"g_ram\[[^\]]+\]\s*=(?!=)", block))

    def test_pad_r_launches_recent_with_paired_release(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index('extern "C" int ur_uniracers_modern_system_gamepad_button(')
        body = source[start:source.index('extern "C" int ur_uniracers_modern_system_gamepad_control(', start)]
        release = body.index("button == kGamepadBtn_R1 &&\n             recent_course_available_for_active_profile()")
        press = body.index("if (modern_mode() && button == kGamepadBtn_R1 && !paused() &&")
        self.assertLess(release, press)
        launch = body.index("(void)launch_recent_course_practice();", press)
        self.assertLess(press, launch)

    def test_native_acceptance_presses_real_pad_r_with_tour_present(self):
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("UR_MAIN_MENU_PAD_ACCEPTANCE=r", harness)
        self.assertIn("F3/Y NEXT EVENT Monster | F6/R RECENT Bowl", harness)
        self.assertIn('! grep -q "UR_TOUR_ENTRY MENU_OPENED" "$E_LOG"', harness)


if __name__ == "__main__":
    unittest.main()
