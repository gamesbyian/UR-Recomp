import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = (ROOT / "native/product/uniracers_modern_host.cpp").read_text()
WORKFLOW = (ROOT / ".github/workflows/multiplayer-match-capture-acceptance.yml").read_text()
SCRIPT = (ROOT / "tests/native/run_modern_local_tournament_panel_acceptance.sh").read_text()


def function_body(name: str) -> str:
    match = re.search(r"\n[^\n]*\b" + re.escape(name) + r"\([^)]*\)\s*\{", HOST)
    if not match:
        raise AssertionError(f"missing {name}")
    depth = 0
    for index in range(match.end() - 1, len(HOST)):
        if HOST[index] == "{":
            depth += 1
        elif HOST[index] == "}":
            depth -= 1
            if depth == 0:
                return HOST[match.end():index]
    raise AssertionError(f"unterminated {name}")


class LocalTournamentPanelHostContract(unittest.TestCase):
    def test_panel_owns_human_input_and_is_bound_to_confirmed_2p_select(self):
        self.assertIn("g_local_tournament_panel_visible ||",
                      function_body("host_owns_human_player_input"))
        context = function_body("local_tournament_panel_context_valid")
        self.assertIn("g_ram[0x009F] == 0x3D) return true", context)
        self.assertIn("multiplayer_participant_session_ready()", context)
        self.assertIn("g_local_multiplayer_join_visible ||", context)

    def test_production_ids_are_os_minted_never_fixed(self):
        for name in ("create_local_tournament_from_panel",
                     "arm_local_tournament_from_panel"):
            body = function_body(name)
            self.assertIn("mint_local_tournament_token()", body)
            self.assertNotRegex(body, r'"[0-9a-f]{32}"')

    def test_unfinished_event_is_never_replaced_from_the_panel(self):
        body = function_body("create_local_tournament_from_panel")
        self.assertIn("!local_tournament_session_complete()", body)
        self.assertIn("EVENT IN PROGRESS", body)

    def test_arm_requires_the_seated_pair_and_no_pending_attempt(self):
        body = function_body("arm_local_tournament_from_panel")
        self.assertIn("session.launch.pending", body)
        self.assertIn("local_tournament_fixture_playable_by", body)
        self.assertIn("arm_local_tournament_fixture", body)

    def test_native_acceptance_drives_the_production_key_handler(self):
        body = function_body("run_local_tournament_panel_acceptance")
        self.assertIn("ur_uniracers_modern_system_key_down(", body)
        self.assertNotIn("arm_local_tournament_fixture", body)
        self.assertNotIn("create_local_tournament_coordinator", body)
        self.assertIn("UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=create", SCRIPT)
        self.assertIn("minted", SCRIPT)
        self.assertIn("run_modern_local_tournament_panel_acceptance.sh", WORKFLOW)
        self.assertIn("run_modern_local_tournament_legs_acceptance.sh", WORKFLOW)

    def test_results_screen_admits_the_seated_pair_after_capture(self):
        context = function_body("local_tournament_panel_context_valid")
        self.assertIn("kOrdinaryTwoPlayerRaceResultMenu", context)
        self.assertIn("!g_multiplayer_run_capture.capturing()", context)


if __name__ == "__main__":
    unittest.main()
