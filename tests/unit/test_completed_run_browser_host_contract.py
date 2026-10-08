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


    def test_replay_can_cancel_without_injecting_guest_input(self):
        source = (ROOT / "native" / "product" /
                  "completed_run_browser_host.cpp").read_text(encoding="utf-8")
        helper = source.split("void cancel_active_replay_to_browser()", 1)[1].split(
            "void adjust_records_root_section(", 1)[0]
        for token in (
            "g_replay_flow.cancel();",
            "snesrecomp_desktop_load_relative_input_file(nullptr)",
            "ur_uniracers_modern_after_run_frame(nullptr)",
            "snesrecomp_desktop_is_paused()",
            "refresh_browser()",
            "g_browser_visible = opened;",
        ):
            self.assertIn(token, helper)
        keyboard = source.split("int ur_uniracers_product_system_key_down(", 1)[1].split(
            "int ur_uniracers_product_system_gamepad_button(", 1)[0]
        raw = source.split("int ur_uniracers_product_system_gamepad_button(", 1)[1].split(
            "int ur_uniracers_product_system_gamepad_control(", 1)[0]
        mapped = source.split("int ur_uniracers_product_system_gamepad_control(", 1)[1].split(
            "void ur_uniracers_product_system_overlay(", 1)[0]
        self.assertIn("key == SDLK_ESCAPE && !repeat", keyboard)
        self.assertIn("pressed && button == kGamepadBtn_B", raw)
        self.assertIn("pressed && control == 7", mapped)
        self.assertIn('"ESC / B  CANCEL REPLAY"', source)
        for event_path in (keyboard, raw, mapped):
            self.assertIn("cancel_active_replay_to_browser();", event_path)

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
