"""Control projection must fail closed on ambiguous dispatch or recovery claims."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, REGISTRY, extract_board, load_json, summary, validate_registry


def replace_table_cell(markdown, row_id, column, value):
    """Edit one current board row without depending on historical lane prose."""
    rows = markdown.splitlines(keepends=True)
    for index, line in enumerate(rows):
        parts = line.split("|")
        if len(parts) > column and parts[1].strip() == row_id:
            parts[column] = " " + value + " "
            rows[index] = "|".join(parts)
            return "".join(rows)
    raise AssertionError("missing current board row: " + row_id)


def candidate_registry(board):
    """Stable negative fixtures, unaffected by real Vault dispositions."""
    work_id = board["work"][0]["work_id"]
    def row(identifier, status, drive_id, failure, pr=None, merge=None):
        return {
            "candidate_id": identifier, "work_id": work_id,
            "discriminator": identifier + "-discriminator",
            "state": status, "drive_id": drive_id,
            "github_pr": pr, "merge_sha": merge,
            "failure_class": failure, "release_gate_credit": False,
            "next_action": "Retain verified evidence and review the source",
        }
    return {
        "schema": "ur-recovery-registry/1",
        "scope": "curated_not_exhaustive",
        "candidates": [
            row("fixture-merged", "merged", "verified-fixture-archive-00001",
                "none", 321, "a" * 40),
            row("fixture-safety-denied", "blocked",
                "verified-fixture-archive-00002", "tool_safety_block"),
        ],
    }


class AgentBoardControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BOARD.read_text(encoding="utf-8")
        cls.board = extract_board(cls.text)

    def test_shared_pool_and_staggered_schedule(self):
        board = self.board
        self.assertEqual(board["schema"], "ur-agent-control/2")
        self.assertEqual(board["selection"], "ranked_shared_pool_top_five")
        self.assertEqual(len(board["agents"]), 5)
        self.assertGreaterEqual(len(board["work"]), 10)
        self.assertEqual(
            [a["minute"] for a in board["agents"]], [0, 12, 24, 36, 48])
        self.assertTrue(all(a["selection"] == "shared_pool_top_five"
                            and "anchors" not in a for a in board["agents"]))
        self.assertEqual(
            [job["position"] for job in board["work"]],
            list(range(1, len(board["work"]) + 1)))

    def test_fixed_lane_regression_is_rejected(self):
        bad = replace_table_cell(
            self.text, "**Agent 1**", 3,
            "**1 Windows owner + 2 storage owner**")
        with self.assertRaisesRegex(ValueError, "shared five-job pool"):
            extract_board(bad)

    def test_missing_board_entry_is_rejected(self):
        lines = self.text.splitlines(keepends=True)
        lines = [s for s in lines if not s.startswith("| 2 | UR-")]
        with self.assertRaisesRegex(ValueError, "contiguous ranked"):
            extract_board("".join(lines))

    def test_unrecognized_job_state_is_rejected(self):
        bad = replace_table_cell(self.text, "1", 3, "merged")
        with self.assertRaisesRegex(ValueError, "invalid work state"):
            extract_board(bad)

    def test_schedule_drift_is_rejected(self):
        for original, altered in (
            ("**:00**", "**:01**"),
            ("**:12**", "**:13**"),
            ("**:24**", "**:25**"),
            ("**:36**", "**:37**"),
            ("**:48**", "**:49**"),
        ):
            with self.subTest(original=original):
                bad = self.text.replace(original, altered, 1)
                with self.assertRaisesRegex(ValueError, "differs from installed schedule"):
                    extract_board(bad)

    def test_new_work_id_can_be_reprioritized(self):
        dated = "UR-VAULT-CONTRACT-20991231"
        new_board = extract_board(
            replace_table_cell(self.text, "1", 2, dated))
        self.assertEqual(new_board["work"][0]["work_id"], dated)
        self.assertEqual([a["minute"] for a in new_board["agents"]],
                         [a["minute"] for a in self.board["agents"]])

    def test_invalid_work_id_rejected(self):
        bad = replace_table_cell(
            self.text, "1", 2, "UR-VAULT-NOT-A-DATE")
        with self.assertRaisesRegex(ValueError, "invalid work ID"):
            extract_board(bad)

    def test_historical_prose_is_not_dispatch(self):
        altered = self.text + "\nHistoric: UR-OLD-99 Agent 9 anchors 1+2\n"
        self.assertEqual(extract_board(altered), self.board)

    def test_fewer_than_five_eligible_jobs_rejected(self):
        bad = self.text
        for n in range(1, len(self.board["work"]) - 3):
            row = self.board["work"][n - 1]
            if row["state"] in {"ready", "in_review"}:
                bad = replace_table_cell(bad, str(n), 3, "hold")
        with self.assertRaisesRegex(ValueError, "fewer than five selectable jobs"):
            extract_board(bad)


class RecoveryRegistryControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = extract_board(BOARD.read_text(encoding="utf-8"))
        cls.registry = load_json(REGISTRY)
        cls.fixture = candidate_registry(cls.board)
        # Real registry can legitimately shrink or change disposition.
        validate_registry(cls.fixture, cls.board)

    def test_current_registry_is_structural_not_release_credit(self):
        result = validate_registry(self.registry, self.board)
        self.assertEqual(result["candidates"], len(self.registry["candidates"]))
        self.assertTrue(all(c["release_gate_credit"] is False
                            for c in self.registry["candidates"]))

    def test_known_retired_work_id_remains_valid_historical_provenance(self):
        archived = copy.deepcopy(self.fixture)
        archived["candidates"][0]["work_id"] = "UR-QA01-01"
        self.assertEqual(validate_registry(archived, self.board)["candidates"], 2)

    def test_unknown_retired_work_id_does_not_pass_as_provenance(self):
        invalid = copy.deepcopy(self.fixture)
        invalid["candidates"][0]["work_id"] = "UR-INVENTED-01"
        with self.assertRaisesRegex(ValueError, "orphan work ID"):
            validate_registry(invalid, self.board)

    def test_retired_work_ids_cannot_admit_new_active_tasks(self):
        invalid = copy.deepcopy(self.fixture)
        first = invalid["candidates"][0]
        first.update(work_id="UR-QA01-01", state="pending_review",
                     merge_sha=None)
        with self.assertRaisesRegex(ValueError, "retired work ID"):
            validate_registry(invalid, self.board)

    def test_duplicate_canonical_candidate_is_rejected(self):
        bad = copy.deepcopy(self.fixture)
        bad["candidates"].append(copy.deepcopy(bad["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
            validate_registry(bad, self.board)

    def test_recovery_cannot_grant_release_gates(self):
        bad = copy.deepcopy(self.fixture)
        bad["candidates"][0]["release_gate_credit"] = True
        with self.assertRaisesRegex(ValueError, "cannot award a release gate"):
            validate_registry(bad, self.board)

    def test_merged_requires_pinned_merge_commit(self):
        bad = copy.deepcopy(self.fixture)
        bad["candidates"][0]["merge_sha"] = None
        with self.assertRaisesRegex(ValueError, "exact commit SHA"):
            validate_registry(bad, self.board)

    def test_denied_operation_cannot_be_recast_as_pending_retry(self):
        bad = copy.deepcopy(self.fixture)
        denied = next(c for c in bad["candidates"]
                      if c["failure_class"] == "tool_safety_block")
        denied["state"] = "pending_review"
        with self.assertRaisesRegex(ValueError, "not an actionable retry"):
            validate_registry(bad, self.board)

    def test_same_work_discriminator_cannot_have_two_active_candidates(self):
        bad = copy.deepcopy(self.fixture)
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

    def test_negative_fixtures_survive_real_disposition_turnover(self):
        # The live registry may legitimately drop merged history or have no
        # currently blocked refusals after the integrator closes them.
        changed = copy.deepcopy(self.registry)
        changed["candidates"] = []
        self.assertEqual(validate_registry(changed, self.board)["candidates"], 0)
        denied = copy.deepcopy(self.fixture)
        refused = next(x for x in denied["candidates"]
                       if x["failure_class"] == "tool_safety_block")
        refused["state"] = "pending_review"
        with self.assertRaisesRegex(ValueError, "not an actionable retry"):
            validate_registry(denied, self.board)

    def test_dashboard_discloses_offline_and_incomplete_scope(self):
        markdown = summary(self.board, self.registry)
        self.assertIn("offline snapshot", markdown)
        self.assertIn("not a live Drive or GitHub API scan", markdown)
        self.assertIn("No blocked write may be retried", markdown)


if __name__ == "__main__":
    unittest.main()
