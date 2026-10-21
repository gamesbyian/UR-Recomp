"""Backup custody metadata cannot silently assert live Drive or current-head status."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from validate_history_custody import load, validate


class HistoricalDriveBackupReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = load()

    def edited(self, **changes):
        obj = copy.deepcopy(self.actual)
        obj.update(changes)
        return obj

    def test_historical_record_has_provenance_but_no_live_claim(self):
        value = validate(self.actual)
        self.assertEqual(value["source_commit"], self.actual["source_commit"])
        self.assertEqual(value["commit_count"], 8118)
        self.assertEqual(value["part_count"], 5)
        self.assertEqual(value["custody_type"], "historical_not_live")

    def test_corrupted_or_reordered_parts_rejected(self):
        wrong = self.edited()
        wrong["parts"][-1]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "part length sum"):
            validate(wrong)
        wrong = self.edited()
        wrong["parts"][0], wrong["parts"][1] = wrong["parts"][1], wrong["parts"][0]
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            validate(wrong)

    def test_duplicate_drive_id_and_part_hash_rejected(self):
        wrong = self.edited()
        wrong["parts"][1]["drive_id"] = wrong["parts"][0]["drive_id"]
        with self.assertRaisesRegex(ValueError, "duplicate Drive"):
            validate(wrong)
        wrong = self.edited()
        wrong["parts"][1]["sha256"] = wrong["parts"][0]["sha256"]
        with self.assertRaisesRegex(ValueError, "duplicate part digest"):
            validate(wrong)

    def test_live_or_qa_credit_misrepresentation_rejected(self):
        for key, value in (
            ("status", "currently_verified"),
            ("live_drive_state", "current"),
            ("release_qa_credit", True),
            ("scope", "whole_account"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(self.edited(**{key: value}))

    def test_missing_restore_checks_are_rejected(self):
        wrong = self.edited()
        wrong["checks"]["git_fsck_connectivity_passed"] = False
        with self.assertRaisesRegex(ValueError, "independent restoration"):
            validate(wrong)

    def test_overlarge_chunk_is_rejected(self):
        wrong = self.edited()
        wrong["parts"][0]["bytes"] = 100 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, "transfer cap"):
            validate(wrong)

    def test_source_claim_requires_exact_commit(self):
        wrong = self.edited()
        wrong["github_commit"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "differs"):
            validate(wrong)


if __name__ == "__main__":
    unittest.main()
