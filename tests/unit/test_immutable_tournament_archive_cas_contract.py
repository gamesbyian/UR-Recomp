"""QA-02: immutable tournament archive is a create-only authority.

The native coordinator fixture proves that a different canonical schedule
cannot replace an incumbent archive. This guard ties the coordinator's
publication path to that proven store operation, not a TOCTOU exists check.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ImmutableTournamentArchiveCasContract(unittest.TestCase):
    def test_coordinator_does_not_replace_instance_archive(self):
        source = (
            ROOT / "native/product/local_tournament_session_coordinator.cpp"
        ).read_text(encoding="utf-8")
        creation = source.split(
            "LocalTournamentCoordinatorResult create_local_tournament_coordinator(", 1
        )[1].split(
            "\nLocalTournamentCoordinatorResult restore_local_tournament_coordinator(", 1
        )[0]
        self.assertIn(
            "save_local_tournament_session_definition_if_current(\n"
            "        archived_session_path(next), std::nullopt, next.definition)",
            creation,
        )
        self.assertIn(
            "archive_status == LocalTournamentSessionFileStatus::Conflict",
            creation,
        )
        self.assertIn("return error(Status::AlreadyExists", creation)
        self.assertNotIn(
            "save_local_tournament_session_definition(\n"
            "            archived_session_path(next), next.definition)",
            creation,
        )


if __name__ == "__main__":
    unittest.main()
