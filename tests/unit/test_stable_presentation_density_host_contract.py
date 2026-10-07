import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class StablePresentationDensityHostContractTests(unittest.TestCase):
    def test_host_uses_product_setting_for_stable_density_and_exact_fallback(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")

        scale_start = source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        draw_start = source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', scale_start
        )
        scale_body = source[scale_start:draw_start]

        self.assertIn('std::getenv("UR_RACER_HD")', scale_body)
        self.assertIn(
            "g_product_state.settings.internal_render_scale", scale_body
        )
        self.assertIn("internal_render_scale_value(", scale_body)
        self.assertNotIn("racer_hd_presentation_scale()", scale_body)
        self.assertIn("world_expanded", scale_body)
        self.assertIn(
            "const bool logical_overlay_active = false;", scale_body
        )
        self.assertNotIn("regional_title", scale_body)

        draw_end = source.index(
            'extern "C" void ur_uniracers_modern_compute_viewport', draw_start
        )
        draw_body = source[draw_start:draw_end]
        self.assertIn("racer_hd_draw_frame(", draw_body)
        self.assertIn("compose_nearest_density_frame(", draw_body)
        # The regional title composes first on its own early-return path;
        # the generic fallback still follows the Racer-HD presenter.
        self.assertLess(
            draw_body.index("racer_hd_draw_frame("),
            draw_body.rindex("compose_nearest_density_frame("),
        )
        self.assertIn("presentation_scale <= 1", draw_body)

    def test_racer_presenter_remains_selection_owner(self):
        header = (
            ROOT / "native" / "presentation" / "racer_hd_presenter.hpp"
        ).read_text(encoding="utf-8")
        self.assertNotIn("racer_hd_requested_presentation_scale", header)


if __name__ == "__main__":
    unittest.main()
