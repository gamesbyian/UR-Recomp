"""QA-02: a live fixture owns a crash-released, nonblocking OS handle.

Native two-process acceptance exercises actual file-handle contention and
process death. This guard prevents a future refactor from limiting protection
to the short checkpoint publication window or forgetting lease release.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class FixtureLiveLeaseContract(unittest.TestCase):
    def test_nonblocking_is_distinct_from_existing_short_lock(self):
        header = (ROOT / "native/product/local_tournament_launch_path_lock.hpp"
                  ).read_text(encoding="utf-8")
        self.assertIn("bool nonblocking = false", header)
        self.assertIn("LOCKFILE_FAIL_IMMEDIATELY", header)
        self.assertIn("LOCK_NB", header)
        self.assertIn("bool busy() const noexcept", header)
        self.assertIn("GetLastError() == ERROR_LOCK_VIOLATION", header)

    def test_live_lease_spans_guest_attempt_and_actual_fixture_commit(self):
        header = (ROOT / "native/product/local_tournament_session_coordinator.hpp"
                  ).read_text(encoding="utf-8")
        cpp = (ROOT / "native/product/local_tournament_session_coordinator.cpp"
               ).read_text(encoding="utf-8")
        self.assertIn("std::shared_ptr<TournamentLaunchPathLock> live_fixture_lock", header)
        self.assertIn("Busy, // another still-running game", header)
        arm = cpp.split("LocalTournamentCoordinatorStatus arm_local_tournament_fixture(", 1)[1].split(
            "\nstd::optional<std::string> local_tournament_capture_attempt_for(", 1)[0]
        arm_lock = arm.index("pending_path(session) + \".live\", true")
        current = arm.index("load_historical_local_tournament_session_definition(")
        receipts = arm.index("restore_saved_local_tournament_fixtures(")
        save = arm.index("save_local_tournament_launch_file(")
        retain = arm.index("session.live_fixture_lock = std::move(live_lock)")
        self.assertLess(arm_lock, current)
        self.assertLess(current, receipts)
        self.assertLess(receipts, save)
        self.assertLess(save, retain)
        self.assertIn("live_lock->busy() ? Status::Busy", arm)
        commit = cpp.split("LocalTournamentCoordinatorStatus commit_local_tournament_capture(", 1)[1].split(
            "\nLocalTournamentCoordinatorStatus cancel_local_tournament_capture(", 1)[0]
        self.assertLess(commit.index("commit_saved_local_tournament_fixture("),
                        commit.index("session.live_fixture_lock.reset()"))
        self.assertLess(commit.index("retire_local_tournament_launch_file("),
                        commit.index("session.live_fixture_lock.reset()"))
        cancel = cpp.split("LocalTournamentCoordinatorStatus cancel_local_tournament_capture(", 1)[1].split(
            "\nbool local_tournament_coordinator_complete(", 1)[0]
        self.assertLess(cancel.index("retire_local_tournament_launch_file("),
                        cancel.index("session.live_fixture_lock.reset()"))


if __name__ == "__main__":
    unittest.main()
