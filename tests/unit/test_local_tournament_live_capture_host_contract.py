import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentLiveCaptureHostContract(unittest.TestCase):
    def test_real_two_player_capture_retains_explicit_attempt_only(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn('#include "local_tournament_session_coordinator.hpp"', host)
        self.assertIn('product_user_data_path("local-tournaments")', host)
        self.assertIn("restore_local_tournament_coordinator(", host)
        self.assertIn("multiplayer_participant_session_ready()", host)
        self.assertIn('std::getenv("UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE")', host)
        self.assertIn("arm_local_tournament_fixture(", host)
        self.assertIn("local_tournament_capture_attempt_for(", host)
        self.assertIn("commit_local_tournament_capture(", host)
        self.assertIn("cancel_local_tournament_capture(", host)

        start = host.index("bool begin_multiplayer_run_record_capture(")
        end = host.index("void observe_run_ghost_trace_sample()", start)
        begin_body = host[start:end]
        self.assertLess(
            begin_body.index("g_multiplayer_run_capture.begin_attempt("),
            begin_body.index("local_tournament_capture_attempt_for("),
        )
        self.assertIn("g_multiplayer_capture_player1->profile_id", begin_body)
        self.assertIn("g_multiplayer_capture_player2->profile_id", begin_body)
        self.assertIn("provenance.course_id", begin_body)
        self.assertIn('"UR_LOCAL_TOURNAMENT CAPTURE_TAGGED"', begin_body)
        self.assertIn("cancel_local_tournament_capture(", begin_body)
        self.assertIn('"UR_LOCAL_TOURNAMENT CAPTURE_NOT_ADMITTED"', begin_body)
        # A route that visited stock 2P setup but returned to the settled
        # frontend without reaching a valid race must retire its launch.
        self.assertIn("g_local_tournament_route_seen_two_player_select", host)
        self.assertIn('"UR_LOCAL_TOURNAMENT UNFINISHED_ROUTE_CANCELLED"', host)

        completed = host.index("void complete_multiplayer_run_record_capture()")
        last = host.index("void complete_run_record_capture()", completed)
        completion = host[completed:last]
        self.assertLess(
            completion.index("append_multiplayer_match_pair("),
            completion.index("commit_local_tournament_capture("),
        )
        self.assertLess(
            completion.index("commit_local_tournament_capture("),
            completion.index("reset_multiplayer_run_capture();",
                             completion.index("UR_MULTIPLAYER_MATCH CAPTURED")),
        )
        # The exact recorder-retained token, never a saved filename or profile
        # comparison, is passed to the production coordinator commit.
        self.assertIn("*g_multiplayer_capture_tournament_attempt, stored_path", completion)
        self.assertIn('"UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED"', completion)

    def test_native_target_links_all_authoritative_storage_owners(self):
        patched = (ROOT / "tools/patch_modern_product_host.py").read_text(
            encoding="utf-8"
        )
        for name in (
            "local_tournament_session_store.cpp",
            "local_tournament_fixture_launch_store.cpp",
            "local_tournament_result_link_store.cpp",
            "local_tournament_session_coordinator.cpp",
        ):
            self.assertIn(name, patched)

    def test_optional_live_native_gate_checks_fresh_standings(self):
        script = (ROOT /
                  "tests/native/run_modern_local_tournament_capture_acceptance.sh"
                  ).read_text(encoding="utf-8")
        self.assertIn(
            "run_modern_two_player_join_record_acceptance.sh", script
        )
        self.assertIn("UR_LOCAL_TOURNAMENT CAPTURE_TAGGED", script)
        self.assertIn("UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED", script)
        self.assertIn("local_tournament_live_capture_check.cpp", script)


if __name__ == "__main__":
    unittest.main()
