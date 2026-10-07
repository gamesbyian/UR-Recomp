import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class PauseModalDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_pause_family_no_longer_forces_global_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.source[start:end]
        self.assertNotIn("host_subview_visible()", body)
        self.assertNotIn("paused() ||", body)
        self.assertNotIn("g_profile_menu_visible", body)
        self.assertNotIn("UR_UNIRACERS_RESTART_RESULTS", body)

    def test_pause_family_uses_shared_composition_and_density(self):
        start = self.source.index(
            'extern "C" void ur_uniracers_modern_system_overlay('
        )
        body = self.source[start:]
        self.assertIn("centered_modern_modal_layout(", body)
        self.assertIn(
            "const int modal_scale = modern_overlay_surface_scale(width, height);",
            body,
        )
        for surface in (
            "options_layout",
            "controls_layout",
            "quit_layout",
            "run_layout",
        ):
            self.assertIn(surface, body)
        self.assertIn("0xFFFFFFFFu, modal_scale);", body)
        self.assertIn("22 * modal_scale", body)
        self.assertIn("row_y += 13 * modal_scale;", body)

    def test_no_modal_guard_forces_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.source[start:end]
        # Every modal and the regional title now compose at the configured
        # density, so none of them may pin presentation to 1x.
        for guard in (
            "regional_title",
            "g_local_multiplayer_join_visible",
            "g_tour_action_visible",
            "onboarding_surface_active()",
            "g_profile_menu_visible",
        ):
            self.assertNotIn(guard, body)
        self.assertIn("const bool logical_overlay_active = false;", body)


if __name__ == "__main__":
    unittest.main()
