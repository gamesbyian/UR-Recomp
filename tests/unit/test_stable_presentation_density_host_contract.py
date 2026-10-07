import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class StablePresentationDensityHostContractTests(unittest.TestCase):
    def test_host_uses_stable_requested_density_and_fallback_compositor(self):
        source = (ROOT / "native" / "product" / "uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        scale_start = source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        draw_start = source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', scale_start
        )
        scale_body = source[scale_start:draw_start]
        draw_end = source.index(
            'extern "C" void ur_uniracers_modern_compute_viewport', draw_start
        )
        draw_body = source[draw_start:draw_end]

        self.assertIn("racer_hd_requested_presentation_scale()", scale_body)
        self.assertNotIn("racer_hd_presentation_scale()", scale_body)
        self.assertIn("world_expanded", scale_body)
        self.assertIn("logical_overlay_active", scale_body)
        self.assertIn("regional_title", scale_body)

        self.assertIn("racer_hd_draw_frame(", draw_body)
        self.assertIn("compose_nearest_density_frame(", draw_body)
        self.assertLess(
            draw_body.index("racer_hd_draw_frame("),
            draw_body.index("compose_nearest_density_frame("),
        )
        self.assertIn("presentation_scale <= 1", draw_body)

    def test_racer_presenter_distinguishes_requested_from_active_scale(self):
        source = (
            ROOT / "native" / "presentation" / "racer_hd_presenter.cpp"
        ).read_text(encoding="utf-8")

        requested = source.index("int racer_hd_requested_presentation_scale()")
        active = source.index("int racer_hd_presentation_scale()")
        requested_body = source[requested:active]
        active_body = source[active:source.index("void racer_hd_begin_sim_frame", active)]

        self.assertIn("env_enabled() ? g_internal_render_scale : 1", requested_body)
        self.assertNotIn("g_frame_active", requested_body)
        self.assertIn("g_frame_active", active_body)


if __name__ == "__main__":
    unittest.main()
