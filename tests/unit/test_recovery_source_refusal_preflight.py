"""Source-bound negative admissions, no publication permission is issued."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from recovery_source_refusal_preflight import check, git_blob


SOURCE = "6ccc44d0b671740e52f3bf86ff63a38dd2d039e4"
ARCHIVE = "1d1ikPoEZBEilf55HaM1i6ZY3u1exbQVO"


class RefusalPreflight(unittest.TestCase):
    def candidate(self, **overrides):
        return {**{"source_blob_sha": SOURCE,
                   "target_path": "tools/verify_cross_resolution.py",
                   "source_archive_drive_id": ARCHIVE}, **overrides}

    def incident(self, **overrides):
        return {**{"incident_id": "agent5-20261022-856px-refusal",
                   "failure_class": "explicit-safety-refusal",
                   "raw_error": "This tool call was blocked by OpenAI's safety checks.",
                   "source_member_git_blob_sha": SOURCE,
                   "attempted_target": "analysis/recovery/agent5/verify_cross_resolution.py",
                   "source_zip_drive_id": ARCHIVE}, **overrides}

    def test_identical_bytes_are_held_even_when_target_renamed(self):
        receipt = check(self.candidate(), [self.incident()])
        self.assertEqual(receipt["decision"], "HOLD_KNOWN_REFUSAL")
        self.assertIn("identical refused source bytes", receipt["exact_refusal_matches"][0]["reasons"])
        self.assertFalse(receipt["automatic_publication_authorized"])

    def test_same_target_is_held_even_if_proposed_bytes_differ(self):
        i = self.incident(source_member_git_blob_sha="a"*40,
                          attempted_target="tools/verify_cross_resolution.py")
        receipt = check(self.candidate(), [i])
        self.assertEqual(receipt["decision"], "HOLD_KNOWN_REFUSAL")
        self.assertIn("identical refused target path", receipt["exact_refusal_matches"][0]["reasons"])

    def test_original_operation_content_is_hashed_as_git_blob(self):
        text = "# original source\nprint('preserve')\n"
        i = {"incident_id": "original-operation", "classification": "EXPLICIT_TOOL_SAFETY_REFUSAL",
             "original_operation": {"path": "other/path.py", "content": text}}
        receipt = check(self.candidate(source_blob_sha=git_blob(text)), [i])
        self.assertEqual(receipt["decision"], "HOLD_KNOWN_REFUSAL")

    def test_shared_composite_archive_prompts_review_not_exact_refusal(self):
        i = self.incident(source_member_git_blob_sha="b"*40, attempted_target="elsewhere.py")
        receipt = check(self.candidate(), [i])
        self.assertEqual(receipt["decision"], "REVIEW_SHARED_ARCHIVE")
        self.assertFalse(receipt["automatic_publication_authorized"])

    def test_unrelated_technical_failure_is_not_mislabeled_as_refusal(self):
        i = self.incident(failure_class="transport_error", raw_error="HTTP 503",
                          source_member_git_blob_sha="b"*40, attempted_target="other.py")
        receipt = check(self.candidate(), [i])
        self.assertEqual(receipt["decision"], "NO_MATCH_NONEXHAUSTIVE")
        self.assertFalse(receipt["automatic_publication_authorized"])
        self.assertTrue(receipt["manual_source_and_incident_review_required"])

    def test_incomplete_or_duplicate_denial_requires_review(self):
        for records in ([None], [self.incident(), self.incident()],
                        [{"incident_id": "missing-target", "classification": "explicit_safety_denial"}]):
            with self.subTest(records=records):
                result = check(self.candidate(source_blob_sha="a"*40,
                                              source_archive_drive_id=None), records)
                self.assertEqual(result["decision"], "REVIEW_INCOMPLETE_RECORDS")

    def test_invalid_candidate_fails_closed(self):
        for v in (self.candidate(source_blob_sha="bad"),
                  self.candidate(target_path="../tools/x"),
                  self.candidate(source_archive_drive_id="short")):
            with self.subTest(candidate=v), self.assertRaises(ValueError):
                check(v, [])


if __name__ == "__main__":
    unittest.main()
