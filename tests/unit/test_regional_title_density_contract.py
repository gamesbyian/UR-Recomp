import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
PRESENTER = ROOT / "native" / "product" / "regional_title_presenter.cpp"


class RegionalTitleDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.host = HOST.read_text(encoding="utf-8")
        self.presenter = PRESENTER.read_text(encoding="utf-8")

    def test_regional_title_no_longer_forces_one_x(self):
        start = self.host.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.host.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.host[start:end]
        self.assertNotIn("RegionalPresentation::Europe", body)
        self.assertIn("world_expanded", body)

    def test_host_precomposes_canonical_frame_and_restores_on_failure(self):
        start = self.host.index(
            'extern "C" int ur_uniracers_modern_draw_frame'
        )
        end = self.host.index(
            'extern "C" void ur_uniracers_modern_compute_viewport', start
        )
        body = self.host[start:end]
        self.assertGreaterEqual(
            body.count("compose_nearest_density_frame("),
            2,
        )
        self.assertIn("presentation_scale", body)
        self.assertIn(
            "RegionalTitlePresentationResult::FailedClosed",
            body,
        )

    def test_presenter_scales_logical_crop_and_verifies_scaled_digest(self):
        self.assertIn("x * presentation_scale + sx", self.presenter)
        self.assertIn("(kOriginY + y) * presentation_scale + sy", self.presenter)
        self.assertIn(
            "regional_title_visible_crop_digest(\n"
            "            pixels, pitch, width, height, presentation_scale)",
            self.presenter,
        )


if __name__ == "__main__":
    unittest.main()
