"""Publication incident checks must not manufacture safe retries or source credit."""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from agent_control import BOARD, REGISTRY, extract_board, load_json
from validate_publication_incidents import INCIDENTS, check


class IncidentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = extract_board(BOARD.read_text(encoding="utf8"))
        cls.registry = load_json(REGISTRY)
        cls.original = load_json(INCIDENTS)

    def changed(self, **fields):
        data = copy.deepcopy(self.original)
        data["incidents"][0].update(fields)
        return data

    def test_retired_incident_ids_survive_board_reassignment(self):
        active = {item["work_id"] for item in self.board["work"]}
        historical = {item["work_id"] for item in self.original["incidents"]}
        self.assertTrue(historical - active)
        self.assertEqual(check(self.original, self.board, self.registry)["incidents"],
                         len(self.original["incidents"]))

    def test_current_receipts_remain_historical_holds(self):
        summary = check(self.original, self.board, self.registry)
        self.assertGreaterEqual(summary["incidents"], 2)
        self.assertEqual(summary["held"], 2)

    def test_explicit_denial_not_reclassified_actionable(self):
        for status in ("unknown", "pending_retry", "merged"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                check(self.changed(disposition=status), self.board, self.registry)

    def test_false_acceptance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot award"):
            check(self.changed(release_gate_credit=True), self.board, self.registry)

    def test_verification_requires_exact_digest_not_presence_alone(self):
        with self.assertRaisesRegex(ValueError, "requires digest"):
            check(self.changed(byte_readback="verified"), self.board, self.registry)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            check(self.changed(vault_sha256="bogus"), self.board, self.registry)

    def test_duplicate_incident_or_cross_work_owner_fails(self):
        data = copy.deepcopy(self.original)
        data["incidents"].append(copy.deepcopy(data["incidents"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate incident"):
            check(data, self.board, self.registry)
        with self.assertRaisesRegex(ValueError, "orphan"):
            check(self.changed(work_id="UR-FAKE-99"), self.board, self.registry)

    def test_retains_original_refusal_and_distinguishes_unknown(self):
        with self.assertRaisesRegex(ValueError, "original refusal"):
            check(self.changed(original_error="HTTP 500"), self.board, self.registry)
        self.assertEqual(check(self.changed(byte_readback="unknown"),
                               self.board, self.registry)["incidents"], 2)

    def test_only_an_explicit_verified_readback_may_claim_integrity(self):
        good = self.changed(byte_readback="verified", vault_sha256="a"*64)
        self.assertEqual(check(good, self.board, self.registry)["incidents"], 2)
        with self.assertRaisesRegex(ValueError, "invalid source main SHA"):
            check(self.changed(source_main_sha="bad"), self.board, self.registry)

if __name__ == "__main__":
    unittest.main()
