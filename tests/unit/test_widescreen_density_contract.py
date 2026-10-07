import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
SCALE_POLICY = ROOT / "native" / "product" / "internal_render_scale_policy.hpp"


class WidescreenDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.host = HOST.read_text(encoding="utf-8")
        self.policy = SCALE_POLICY.read_text(encoding="utf-8")

    def test_world_expansion_no_longer_clamps_internal_render_scale(self):
        self.assertIn("(void)world_expanded;", self.policy)
        self.assertNotIn(
            "!modern_mode || world_expanded || logical_overlay_active",
            self.policy,
        )

    def test_host_keeps_logical_widescreen_geometry_separate_from_density(self):
        prepare_start = self.host.index(
            'extern "C" void ur_uniracers_modern_prepare_frame'
        )
        scale_start = self.host.index(
            'extern "C" int ur_uniracers_modern_presentation_scale',
            prepare_start,
        )
        prepare = self.host[prepare_start:scale_start]
        self.assertIn("*frame_width = plan.logical_view_width;", prepare)
        self.assertIn("*frame_height = plan.logical_view_height;", prepare)
        self.assertIn("ur_ws_margins_prepare_frame(", prepare)

    def test_generic_density_fallback_accepts_widened_field(self):
        draw_start = self.host.index(
            'extern "C" int ur_uniracers_modern_draw_frame'
        )
        draw_end = self.host.index(
            'extern "C" void ur_uniracers_modern_compute_viewport',
            draw_start,
        )
        body = self.host[draw_start:draw_end]
        self.assertIn("racer_hd_draw_frame(", body)
        self.assertIn("compose_nearest_density_frame(", body)
        self.assertIn("frame_width,", body)
        self.assertIn("frame_height,", body)
        self.assertIn("presentation_scale", body)


if __name__ == "__main__":
    unittest.main()
