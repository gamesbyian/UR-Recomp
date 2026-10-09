"""QA-02 C16: a storage fault after a saved 2P pair must not auto-cancel.

Native production-store process acceptance covers actual receipt outage,
same-attempt retry and fresh history. This source guard binds the recovered
status to the existing Modern host's real completed-capture and panel path.
"""
from pathlib import Path
import unittest

HOST = (Path(__file__).resolve().parents[2] /
        "native/product/uniracers_modern_host.cpp")


class ReceiptStorageRetryHostContract(unittest.TestCase):
    def test_real_pair_is_retained_only_for_same_process_live_attempt(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("g_local_tournament_receipt_retry", source)
        capture = source.split("void complete_multiplayer_run_record_capture()", 1)[1].split(
            "\nvoid complete_run_record_capture()", 1
        )[0]
        self.assertLess(
            capture.index("append_multiplayer_match_pair("),
            capture.index("commit_local_tournament_capture("),
        )
        self.assertIn("*g_multiplayer_capture_tournament_attempt, stored_path", capture)
        saved = capture.split(
            "credited == ur::product::LocalTournamentCoordinatorStatus::StorageFailed", 1
        )[1].split("\n        } else {", 1)[0]
        self.assertIn("g_local_tournament_receipt_retry = LocalTournamentReceiptRetry{", saved)
        self.assertIn("g_local_tournament_session->definition.instance_id", saved)
        self.assertIn("*g_multiplayer_capture_tournament_attempt", saved)
        self.assertNotIn("cancel_local_tournament_capture(", saved)
        self.assertIn("UR_LOCAL_TOURNAMENT RECEIPT_SAVE_PENDING", saved)
        self.assertIn("g_multiplayer_capture_tournament_attempt.reset();", capture)
        panel = source.split("bool open_local_tournament_panel() {", 1)[1].split(
            "\nvoid create_local_tournament_from_panel(", 1
        )[0]
        self.assertIn("g_local_tournament_receipt_retry", panel)
        self.assertIn("g_local_tournament_receipt_retry->attempt_id", panel)
        self.assertIn("g_local_tournament_receipt_retry->tournament_id", panel)
        self.assertIn("g_local_tournament_session->definition.instance_id", panel)
        self.assertIn("g_local_tournament_receipt_retry->saved_run_path", panel)
        self.assertIn("RECEIPT_RETRY_COMMITTED", panel)
        self.assertIn("RECEIPT_RETRY_STORAGE", panel)
        self.assertNotIn("append_multiplayer_match_pair(", panel)
        # A completed result must not be cancelled when moving from 2P
        # Results to the next stock screen before the explicit retry.
        abandoned = source.split(
            '"UR_LOCAL_TOURNAMENT UNFINISHED_ROUTE_CANCELLED"', 1
        )[0].rsplit("g_local_tournament_route_seen_two_player_select", 1)[-1]
        self.assertIn("g_local_tournament_receipt_retry", abandoned)


if __name__ == "__main__":
    unittest.main()
