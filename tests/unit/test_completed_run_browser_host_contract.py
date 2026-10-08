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
        self.assertIn('"RECORDS / MULTIPLAYER"', source)
        self.assertIn('"NO STORED MATCH HISTORY"', source)
        self.assertIn('"INVALID / UNBOUND PAIRS IGNORED"', source)
        self.assertIn("refresh_multiplayer_match_browser()", source)
        self.assertIn("inspect_multiplayer_match_artifacts(directory)", source)
        self.assertIn("g_multiplayer_match_health.unavailable_pairs()", source)
        self.assertIn("g_multiplayer_match_browser.move(delta)", source)
        self.assertIn("g_multiplayer_match_browser.open_selected()", source)
        self.assertIn("g_multiplayer_match_browser.back()", source)
        self.assertIn("g_multiplayer_match_browser.visible_rows(", source)
        self.assertIn(
            "g_multiplayer_match_browser.selected_detail_presentation()", source
        )
        self.assertIn("MultiplayerMatchBrowserView::Detail", source)
        self.assertNotIn('"HISTORY AUTHORITY NOT YET AVAILABLE"', source)
        self.assertNotIn('"LIVE 2P RESULTS ARE NOT PERSISTED"', source)
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


    def test_restart_rearms_capture_after_unrecorded_replay(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")
        begin = source.index("void rearm_run_capture_after_retry() {")
        end = source.index("ur::product::ModernControlsBindingAuthority", begin)
        retry = source[begin:end]
        self.assertIn("if (!g_run_capture.capturing()) {", retry)
        self.assertIn(
            "if (!g_multiplayer_run_capture.capturing()) {", retry
        )
        self.assertIn("g_run_capture_previous_active = false;", retry)
        self.assertLess(
            retry.index("g_run_capture_previous_active = false;"),
            retry.index("g_run_capture.abort_attempt();"),
        )

    def test_multiplayer_summary_aggregates_only_listed_pairs(self):
        source = (
            ROOT / "native" / "product" / "completed_run_browser_host.cpp"
        ).read_text(encoding="utf-8")
        start = source.index("bool refresh_multiplayer_match_browser()")
        body = source[start:source.index("\n}\n", start)]
        summary = body.index(
            "ur::product::summarize_multiplayer_matches(matches)")
        handoff = body.index(
            "g_multiplayer_match_browser.set_matches(std::move(matches));")
        self.assertLess(summary, handoff)
        self.assertIn("g_multiplayer_match_summary = {};", body)
        self.assertIn("MULTIPLAYER_SUMMARY matches=%zu", body)
        self.assertIn(
            "multiplayer_head_to_head_for_match(\n"
            "                              g_multiplayer_match_summary, *selected)",
            source,
        )


if __name__ == "__main__":
    unittest.main()
