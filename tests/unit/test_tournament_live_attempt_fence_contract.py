"""QA-02: fixture receipt commit requires still-current durable launch attempt."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TournamentLiveAttemptFenceContract(unittest.TestCase):
    def test_checkpoint_mutex_and_exact_disk_attempt_surround_receipt(self):
        source = (
            ROOT / "native/product/local_tournament_session_coordinator.cpp"
        ).read_text(encoding="utf-8")
        action = source.split(
            "LocalTournamentCoordinatorStatus commit_local_tournament_capture(", 1
        )[1].split(
            "\nLocalTournamentCoordinatorStatus cancel_local_tournament_capture(", 1
        )[0]
        lock = action.index("TournamentLaunchPathLock lock(checkpoint)")
        read = action.index("load_local_tournament_launch_file(")
        compare = action.index(
            "encode_local_tournament_pending_fixture(*on_disk.pending)"
        )
        receipt = action.index("commit_saved_local_tournament_fixture(")
        close_scope = action.index("\n    }\n    // The durable receipt")
        retirement = action.index("retire_local_tournament_launch_file(")
        self.assertLess(lock, read)
        self.assertLess(read, compare)
        self.assertLess(compare, receipt)
        self.assertLess(receipt, close_scope)
        self.assertLess(close_scope, retirement)
        self.assertIn("return Status::EvidenceRejected;", action)
        self.assertIn("return Status::StorageFailed;", action)


if __name__ == "__main__":
    unittest.main()
