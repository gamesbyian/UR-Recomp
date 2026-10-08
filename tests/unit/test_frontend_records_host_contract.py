import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODERN = (ROOT / "native/product/uniracers_modern_host.cpp").read_text()
BROWSER = (ROOT / "native/product/completed_run_browser_host.cpp").read_text()
WORKFLOW = (ROOT / ".github/workflows/completed-run-replay-acceptance.yml").read_text()


class FrontendRecordsHostContract(unittest.TestCase):
    def test_modern_host_owns_input_and_holds_frames_while_open(self):
        self.assertIn("g_frontend_records_open ||", MODERN)
        self.assertIn("g_frontend_records_open || onboarding_surface_active();", MODERN)
        admissible = MODERN.split(
            'extern "C" int ur_uniracers_modern_frontend_records_admissible(void) {', 1)[1]
        admissible = admissible.split("\n}\n", 1)[0]
        self.assertIn("ur_uniracers_modern_settled_main_menu()", admissible)
        self.assertIn("!host_owns_human_player_input()", admissible)

    def test_frontend_records_is_unpaused_and_read_only(self):
        self.assertIn("bool open_frontend_records()", BROWSER)
        self.assertIn("frontend ? snesrecomp_desktop_is_paused() != 0", BROWSER)
        # Local Runs (and therefore replay) is never reachable from here.
        self.assertEqual(BROWSER.count("!g_records_frontend &&"), 2)
        self.assertIn("ur_uniracers_modern_set_frontend_records_open(0);", BROWSER)
        self.assertIn("FRONTEND_STALE_CONTEXT", BROWSER)

    def test_entry_points_and_native_acceptance(self):
        self.assertIn('"B BACK  F8/PAD X RECORDS"', MODERN)
        self.assertEqual(MODERN.count("ur_uniracers_product_open_frontend_records()"), 2)
        self.assertIn("UR_RECORDS_BROWSER_ACCEPTANCE=main-menu", WORKFLOW)
        self.assertIn("local_runs_refused=1 closed=1 admissible_after=1", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
