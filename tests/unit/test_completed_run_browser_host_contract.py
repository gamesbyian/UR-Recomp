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
        self.assertIn("adjust_detail_split_offset(delta)", source)
        self.assertIn("detail_split_offset()", source)
        self.assertIn("CUR / TGT / DELTA", source)

        self.assertNotIn('"LEFT / RIGHT  CHANGE TARGET"', source)
        self.assertIn('"SPLITS < %s >  CURRENT / TARGET / DELTA"', source)
        self.assertIn("shown >= 3", source)

        self.assertIn('"RECORDS / RACERS-PROFILES"', source)
        self.assertIn("RecordsRootSection::Profiles", source)
        self.assertIn("RecordsRootSection::MultiplayerTournament", source)
        self.assertIn("adjust_records_root_section(adjustment)", source)
        self.assertIn('"RECORDS / MULTIPLAYER-TOURNAMENT"', source)
        self.assertIn('"NO STORED MATCH HISTORY"', source)
        self.assertIn('"HISTORY AUTHORITY NOT YET AVAILABLE"', source)
        self.assertIn("UR_RECORDS_BROWSER PROFILE_OPEN", source)
        self.assertIn("load_run_records_profile_sources(root)", source)
        self.assertIn("total_unavailable_artifacts", source)
        self.assertIn('"%zu RACERS / %zu RUNS / %zu UNAVAILABLE"', source)
        self.assertIn("profile_unavailable=%zu", source)
        self.assertIn(
            "return records_viewing_active_profile() && selected && target",
            source,
        )

        self.assertIn("void draw_results_records_hint(", source)
        self.assertIn("records_results_surface()", source)
        self.assertIn('"F8 / Y      RECORDS"', source)


if __name__ == "__main__":
    unittest.main()
