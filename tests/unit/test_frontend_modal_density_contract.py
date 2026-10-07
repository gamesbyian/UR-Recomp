import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class FrontendModalDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_migrated_frontend_modals_no_longer_force_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.source[start:end]
        self.assertNotIn("g_local_multiplayer_join_visible", body)
        self.assertNotIn("g_tour_action_visible", body)

    def test_local_multiplayer_modal_scales_through_shared_layout(self):
        start = self.source.index(
            "if (g_local_multiplayer_join_visible && modern_mode())"
        )
        end = self.source.index(
            "if (g_tour_action_visible && modern_mode()", start
        )
        body = self.source[start:end]
        self.assertIn("centered_modern_modal_layout(", body)
        self.assertIn("kLocalMultiplayerPanelHeight = 142", body)
        self.assertIn("0xFFFFFFFFu, scale);", body)
        self.assertNotIn("0xFFFFFFFFu, 1);", body)

    def test_tour_action_modal_scales_rows_and_confirm_state(self):
        start = self.source.index(
            "if (g_tour_action_visible && modern_mode()"
        )
        end = self.source.index(
            "if (g_profile_menu_visible && modern_mode())", start
        )
        body = self.source[start:end]
        self.assertIn("centered_modern_modal_layout(", body)
        self.assertIn("kTourActionPanelHeight = 142", body)
        self.assertIn(
            "y + (66 + static_cast<int>(i) * 18) * scale",
            body,
        )
        self.assertIn("0xFFFFFFFFu, scale);", body)
        self.assertNotIn("0xFFFFFFFFu, 1);", body)


if __name__ == "__main__":
    unittest.main()
