import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunBrowserHostContractTests(unittest.TestCase):
    def test_records_detail_target_keyboard_and_gamepad_parity(self):
        source = (
            ROOT / "native" / "product" / "completed_run_browser_host.cpp"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "records_browser_navigation(UR_MODERN_HOST_NAV_LEFT)", source
        )
        self.assertIn(
            "records_browser_navigation(UR_MODERN_HOST_NAV_RIGHT)", source
        )
        self.assertIn("key == SDLK_LEFT", source)
        self.assertIn("key == SDLK_RIGHT", source)
        self.assertIn("button == kGamepadBtn_DpadLeft", source)
        self.assertIn("button == kGamepadBtn_DpadRight", source)

        self.assertIn(
            "ur_modern_host_navigation_adjustment_delta(action)", source
        )
        self.assertIn("adjust_detail_target(adjustment)", source)


if __name__ == "__main__":
    unittest.main()
