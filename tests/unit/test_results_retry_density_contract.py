import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class ResultsRetryDensityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_results_retry_no_longer_forces_one_x(self):
        start = self.source.index(
            'extern "C" int ur_uniracers_modern_presentation_scale(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_draw_frame', start
        )
        body = self.source[start:end]
        self.assertNotIn("UR_UNIRACERS_RESTART_RESULTS", body)
        self.assertIn(
            "const bool logical_overlay_active = false;",
            body,
        )

    def test_results_action_menu_uses_modal_density(self):
        start = self.source.index(
            "const auto selected =\n"
            "            ur::product::selected_modern_results_action("
        )
        end = self.source.index("\n    }\n}\n", start)
        body = self.source[start:end]
        self.assertIn('"RETRY / REMATCH  R/X"', body)
        self.assertIn("x + 8 * modal_scale", body)
        self.assertIn("row_y += 15 * modal_scale", body)
        self.assertIn("0xFFFFFFFFu, modal_scale", body)


if __name__ == "__main__":
    unittest.main()
