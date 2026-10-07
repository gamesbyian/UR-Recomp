import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class PauseRecordsIntegrationContractTests(unittest.TestCase):
    def test_pause_menu_records_destination_is_wired_to_existing_browser(self):
        modern = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")
        browser = (
            ROOT / "native" / "product" / "completed_run_browser_host.cpp"
        ).read_text(encoding="utf-8")
        header = (
            ROOT / "native" / "product" / "completed_run_browser_host.h"
        ).read_text(encoding="utf-8")

        self.assertIn("UR_MODERN_PAUSE_RECORDS", modern)
        self.assertIn('"> RECORDS"', modern)
        self.assertIn("ur_uniracers_product_open_records()", modern)
        self.assertIn("UR_PAUSE_RECORDS OPENED", modern)
        self.assertIn("restart ? 144 : 129", modern)
        self.assertIn("const int records_y = run_data_y + 15", modern)
        self.assertIn("const int exit_y = records_y + 15", modern)

        self.assertIn("ur_uniracers_product_open_records(void)", header)
        self.assertIn("open_records_browser_impl(false)", browser)
        self.assertIn("UR_RECORDS_BROWSER OPENED_FROM_PAUSE_MENU", browser)
        self.assertGreaterEqual(
            browser.count('std::getenv("UR_PAUSE_RECORDS_ACCEPTANCE")'),
            2,
        )


if __name__ == "__main__":
    unittest.main()
