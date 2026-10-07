import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class ProfileModalDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_profile_modal_no_longer_forces_global_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        self.assertNotIn("g_profile_menu_visible", self.source[start:end])

    def test_profile_modal_uses_shared_centered_layout_and_scale(self):
        start = self.source.index(
            "if (g_profile_menu_visible && modern_mode())"
        )
        end = self.source.index(
            "// Modern main-menu continue strip:", start
        )
        body = self.source[start:end]
        self.assertIn("centered_modern_modal_layout(", body)
        self.assertIn(
            "const int scale = modern_overlay_surface_scale(width, height);",
            body,
        )
        self.assertIn("constexpr int kProfilePanelHeight = 154;", body)
        self.assertIn("x + 8 * scale", body)
        self.assertIn("0xFFFFFFFFu, scale);", body)
        self.assertNotIn("0xFFFFFFFFu, 1);", body)


if __name__ == "__main__":
    unittest.main()
