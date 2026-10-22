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

    def test_live_board_exactly_five_agents_ten_unique_lines(self):
        board = self.board
        self.assertEqual(len(board["agents"]), 5)
        self.assertEqual(len(board["work"]), 10)
        self.assertEqual(
            sorted(n for a in board["agents"] for n in a["anchors"]),
            list(range(1, 11)),
        )
        # The board owns assignment changes; no test freezes Agent 4's
        # historical pair or prevents an authorized reshuffle.
        for agent in board["agents"]:
            self.assertEqual(
                agent["work_ids"],
                [board["work"][number - 1]["work_id"] for number in agent["anchors"]],
            )

    def test_duplicate_anchor_is_rejected(self):
        first = self.board["agents"][0]["anchors"][0]
        bad = replace_table_cell(
            self.text, "**Agent 1**", 3,
            f"**{first} first anchor + {first} duplicated anchor**",
        )
        self.assertNotEqual(bad, self.text)
        with self.assertRaisesRegex(ValueError, "duplicate or invalid agent anchors"):
            extract_board(bad)

    def test_missing_shard_fails_closed(self):
        line = self.board["work"][0]
        number = line["position"]
        bad = replace_table_cell(
            self.text, str(number), 4,
            f"{number}a: {line['shards']['a']}; {number}b: {line['shards']['b']}",
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

    def test_dated_work_ids_parse_without_changing_agent_schedule(self):
        self.assertEqual(
            self.board["work"][0]["work_id"], "UR-VAULT-EXTRACT-20261022")
        self.assertEqual(
            self.board["work"][-1]["work_id"], "UR-VAULT-REGRESS-20261022")
        self.assertEqual(
            [agent["minute"] for agent in self.board["agents"]],
            [0, 12, 24, 36, 48])

    def test_invalid_dated_work_id_is_not_silently_assigned(self):
        broken = replace_table_cell(
            self.text, "1", 2, "UR-VAULT-EXTRACT-NOT-A-DATE")
        with self.assertRaisesRegex(ValueError, "ten unique active work lines"):
            extract_board(broken)

    def test_board_never_scrapes_old_prose_as_dispatch(self):
        altered = self.text + "\nHistorical reference: UR-OBSOLETE-99 and Agent 9\n"
        self.assertEqual(extract_board(altered), self.board)


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
