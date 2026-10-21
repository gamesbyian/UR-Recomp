"""Read-only recovery-disposition drift hints."""
import unittest
from tools.audit_recovery_handoff_drift import scan

ID = "1_RScoARFTHjfttOY87v9PKBepXmE8tK8"
SHA = "d2ab0785cdd531f6fa26534c9597d7cdda484b23"

def registry(state="blocked"):
    return {"schema": "ur-recovery-registry/1",
            "scope": "curated_not_exhaustive",
            "candidates": [{"candidate_id": "h27-knowledge-malformed-lanes",
                            "work_id": "UR-KNOWLEDGE-01", "state": state,
                            "drive_id": ID}]}

def merged(body, number=2194):
    return {"number": number, "merged_at": "2026-10-21T19:55:59Z",
            "merge_commit_sha": SHA, "body": body}

class HandoffDriftTest(unittest.TestCase):
    def test_exact_drive_id_flags_review_not_acceptance(self):
        found = scan(registry(), [merged("Source archive Drive ID " + ID)])
        self.assertEqual(len(found["hints"]), 1)
        self.assertEqual(found["hints"][0]["linked_merged_pr"], 2194)
        self.assertEqual(found["automatic_state_changes"], 0)
        self.assertFalse(found["release_gate_credit"])

    def test_no_partial_id_or_unmerged_false_positive(self):
        for body in (ID[:-1], ID + "ZZ", "file " + ID + "_extra"):
            with self.subTest(body=body):
                self.assertFalse(scan(registry(), [merged(body)])["hints"])
        pr = merged(ID)
        pr["merged_at"] = None
        self.assertFalse(scan(registry(), [pr])["hints"])

    def test_resolved_candidate_not_flagged(self):
        self.assertFalse(scan(registry("merged"), [merged(ID)])["hints"])

    def test_invalid_api_receipt_fails_closed(self):
        pr = merged(ID)
        pr["merge_commit_sha"] = "not-a-commit"
        with self.assertRaisesRegex(ValueError, "incomplete merged PR"):
            scan(registry(), [pr])

    def test_missing_census_is_not_positive(self):
        result = scan(registry(), [])
        self.assertEqual(result["merged_prs_checked"], 0)
        self.assertEqual(result["hints"], [])

if __name__ == "__main__":
    unittest.main()
