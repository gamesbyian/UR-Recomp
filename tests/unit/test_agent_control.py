"""Control projection must fail closed on ambiguous dispatch or recovery claims."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, REGISTRY, extract_board, load_json, summary, validate_registry


class AgentBoardControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BOARD.read_text(encoding="utf-8")
        cls.board = extract_board(cls.text)

    def test_live_board_exactly_five_agents_ten_unique_lines(self):
        board = self.board
        self.assertEqual(len(board["agents"]), 5)
        self.assertEqual(len(board["work"]), 10)
        self.assertEqual(
            sorted(n for a in board["agents"] for n in a["anchors"]),
            list(range(1, 11)),
        )
        self.assertEqual(
            board["agents"][3]["work_ids"],
            ["UR-WINQA-01", "UR-INTEGRATION-01"],
        )

    def test_duplicate_anchor_is_rejected(self):
        bad = self.text.replace(
            "**1 CPU first-divergence + 8 decentralized P2P**",
            "**1 CPU first-divergence + 1 decentralized P2P**",
            1,
        )
        self.assertNotEqual(bad, self.text)
        with self.assertRaisesRegex(ValueError, "duplicate or invalid agent anchors"):
            extract_board(bad)

    def test_missing_shard_fails_closed(self):
        bad = self.text.replace(
            "1c: only then narrow causality probe", "1d: only then narrow causality probe", 1
        )
        self.assertNotEqual(bad, self.text)
        with self.assertRaisesRegex(ValueError, "expected a/b/c shards"):
            extract_board(bad)

    def test_board_start_minutes_match_the_five_installed_schedules(self):
        expected = {1: 0, 2: 12, 3: 24, 4: 36, 5: 48}
        self.assertEqual(
            {row["number"]: row["minute"] for row in self.board["agents"]},
            expected,
        )
        for original, altered in (
            ("**:00**", "**:01**"),
            ("**:12**", "**:13**"),
            ("**:24**", "**:25**"),
            ("**:36**", "**:37**"),
            ("**:48**", "**:49**"),
        ):
            with self.subTest(original=original):
                bad = self.text.replace(original, altered, 1)
                self.assertNotEqual(bad, self.text)
                with self.assertRaisesRegex(ValueError, "differs from installed schedule"):
                    extract_board(bad)

    def test_board_never_scrapes_old_prose_as_dispatch(self):
        altered = self.text + "\nHistorical reference: UR-OBSOLETE-99 and Agent 9\n"
        self.assertEqual(extract_board(altered), self.board)


class RecoveryRegistryControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = extract_board(BOARD.read_text(encoding="utf-8"))
        cls.registry = load_json(REGISTRY)

    def test_current_registry_is_structural_not_release_credit(self):
        result = validate_registry(self.registry, self.board)
        self.assertGreaterEqual(result["candidates"], 5)
        self.assertTrue(all(c["release_gate_credit"] is False
                            for c in self.registry["candidates"]))

    def test_duplicate_canonical_candidate_is_rejected(self):
        bad = copy.deepcopy(self.registry)
        bad["candidates"].append(copy.deepcopy(bad["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
            validate_registry(bad, self.board)

    def test_recovery_cannot_grant_release_gates(self):
        bad = copy.deepcopy(self.registry)
        bad["candidates"][0]["release_gate_credit"] = True
        with self.assertRaisesRegex(ValueError, "cannot award a release gate"):
            validate_registry(bad, self.board)

    def test_merged_requires_pinned_merge_commit(self):
        bad = copy.deepcopy(self.registry)
        bad["candidates"][0]["merge_sha"] = None
        with self.assertRaisesRegex(ValueError, "exact commit SHA"):
            validate_registry(bad, self.board)

    def test_denied_operation_cannot_be_recast_as_pending_retry(self):
        bad = copy.deepcopy(self.registry)
        denied = next(c for c in bad["candidates"]
                      if c["failure_class"] == "tool_safety_block")
        denied["state"] = "pending_review"
        with self.assertRaisesRegex(ValueError, "not an actionable retry"):
            validate_registry(bad, self.board)

    def test_same_work_discriminator_cannot_have_two_active_candidates(self):
        bad = copy.deepcopy(self.registry)
        first = copy.deepcopy(bad["candidates"][0])
        first.update(candidate_id="fresh-active-candidate",
                     state="pending_review", merge_sha=None,
                     drive_id="new-archive-record-000001")
        other = copy.deepcopy(first)
        other.update(candidate_id="other-active-candidate",
                     drive_id="new-archive-record-000002")
        bad["candidates"].extend([first, other])
        with self.assertRaisesRegex(ValueError, "duplicate active candidate"):
            validate_registry(bad, self.board)

    def test_dashboard_discloses_offline_and_incomplete_scope(self):
        markdown = summary(self.board, self.registry)
        self.assertIn("offline snapshot", markdown)
        self.assertIn("not a live Drive or GitHub API scan", markdown)
        self.assertIn("No blocked write may be retried", markdown)


if __name__ == "__main__":
    unittest.main()
