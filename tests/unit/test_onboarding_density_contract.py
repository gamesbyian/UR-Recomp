import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class OnboardingDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_onboarding_no_longer_forces_global_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.source[start:end]
        self.assertNotIn("onboarding_surface_active()", body)
        self.assertIn("const bool logical_overlay_active = false;", body)
        self.assertNotIn("regional_title", body)
        self.assertNotIn("UR_UNIRACERS_RESTART_RESULTS", body)

    def test_onboarding_panel_uses_shared_layout_and_scale(self):
        start = self.source.index(
            "if (onboarding_surface_active())",
            self.source.index(
                'extern "C" void ur_uniracers_modern_system_overlay'
            ),
        )
        end = self.source.index("if (modern_mode() &&", start)
        body = self.source[start:end]
        self.assertIn("centered_modern_modal_layout(", body)
        self.assertIn("kOnboardingPanelHeight = 189", body)
        self.assertIn(
            "const int scale = modern_overlay_surface_scale(width, height);",
            body,
        )
        self.assertIn("0xFFFFFFFFu, scale);", body)
        self.assertNotIn("0xFFFFFFFFu, 1);", body)


if __name__ == "__main__":
    unittest.main()
