"""QA-02 source contract: legacy active archive restore never overwrites a rival."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HistoricalArchiveMigrationContract(unittest.TestCase):
    def test_restore_is_create_only_and_accepts_exact_concurrent_winner(self):
        source = (ROOT / "native/product/local_tournament_session_coordinator.cpp").read_text(
            encoding="utf-8"
        )
        restore = source.split(
            "LocalTournamentCoordinatorResult restore_local_tournament_coordinator(", 1
        )[1].split(
            "\nLocalTournamentCompletedHistory load_completed_local_tournament_history(", 1
        )[0]
        self.assertIn(
            "save_local_tournament_session_definition_if_current(\n"
            "            immutable_path, std::nullopt, next.definition)",
            restore,
        )
        self.assertIn(
            "migrated != LocalTournamentSessionFileStatus::Conflict",
            restore,
        )
        self.assertIn(
            "load_historical_local_tournament_session_definition(\n"
            "                immutable_path)",
            restore,
        )
        self.assertIn("concurrent archive migration changed instance plan", restore)
        self.assertNotIn(
            "save_local_tournament_session_definition(\n"
            "                immutable_path, next.definition)",
            restore,
        )


if __name__ == "__main__":
    unittest.main()
