"""Regression tests for the read-only vault queue-to-review consumer."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import vault_integration_review as q


A = "a" * 64
B = "b" * 64
DRIVE = "1fog_2M1xOs7gi9fJ8N8jSKGbVnJQkqoJ"
FOLDERS = {
    "incoming": "https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX",
    "evidence": "https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2",
}


def save(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


class ReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / "registry.json"
        self.ledger = self.root / "ledger.json"
        self.github = self.root / "github.json"
        save(self.registry, {"schema": q.REGISTRY, "candidates": []})
        save(self.ledger, {"schema": q.LEDGER, "items": []})
        save(self.github, {"prs": []})
        for scope in FOLDERS:
            (self.root / scope).mkdir()
            self.make_artifact(scope)

    def make_artifact(self, scope, *, with_lead=False):
        root = self.root / scope
        items = {}
        reviews = []
        if with_lead:
            items[DRIVE] = {
                "sha256": A, "path": "recovery.zip", "bytes": 200,
                "audited_at": "2026-10-24T00:00:00+00:00",
                "unmatched_or_unexamined": 1,
                "review_leads": [{"member": "src/recovered.py", "sha256": B,
                                  "bytes": 90, "status": "unmatched_needs_review",
                                  "kind": "source_or_test"}],
            }
            reviews = [{"id": DRIVE, **items[DRIVE]}]
        save(root / "checkpoint.json", {"schema": q.CHECKPOINT, "items": items})
        save(root / "queue.json", {"schema": q.QUEUE, "needs_engineering_review": reviews,
                                    "retry_cooldown": []})
        save(root / "report.json", {"schema": "ur-vault-recurring-intake/1",
                                     "folder": FOLDERS[scope], "scanned_at": "2026-10-24",
                                     "processed": [], "errors": [],
                                     "remaining_due": 0})

    def run_review(self):
        return q.assemble(self.root / "incoming", self.root / "evidence",
                          self.registry, self.ledger, self.github)

    def seed(self):
        self.make_artifact("incoming", with_lead=True)
        return q.member_key("incoming", DRIVE, A, "src/recovered.py", B)

    def test_stable_identity_and_no_auto_publishing(self):
        key = self.seed()
        one, two = self.run_review(), self.run_review()
        self.assertEqual(one, two)
        self.assertEqual(one["records"][0]["candidate_id"], key)
        self.assertEqual(one["records"][0]["state"], "needs_semantic_review")
        self.assertFalse(one["automatic_publication_authorized"])
        self.assertEqual(one["source_bytes_published"], 0)

    def test_archive_level_merge_is_not_member_level_merge(self):
        self.seed()
        save(self.registry, {"schema": q.REGISTRY,
                             "candidates": [{"drive_id": DRIVE, "candidate_id": "older",
                                             "state": "merged", "github_pr": 2458}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "needs_semantic_review")

    def test_historical_hold_preserved(self):
        self.seed()
        save(self.registry, {"schema": q.REGISTRY,
                             "candidates": [{"drive_id": DRIVE, "state": "blocked"}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "held")

    def test_engineering_requires_provenance_and_authorization(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER,
                           "items": [{"candidate_id": key, "state": "engineering",
                                      "reason": "reviewed gap", "source_path": "tools/new.py"}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "unresolved")
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "engineering", "reason": "reviewed gap",
             "source_path": "tools/new.py", "publication_authorized": True,
             "provenance_verified": True}]})
        row = self.run_review()["records"][0]
        self.assertEqual((row["state"], row["owner"]), ("queued_engineering", "Agent 2"))

    def test_approved_member_produces_only_manual_bounded_stage_handoff(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "engineering",
             "source_path": "tools/new.py", "reason": "verified missing source",
             "provenance_verified": True, "publication_authorized": True}]})
        result = self.run_review()
        handoff = result["staging_handoff"]
        self.assertEqual(len(handoff), 1)
        self.assertEqual(handoff[0]["drive_file_id"], DRIVE)
        self.assertEqual(handoff[0]["archive_sha256"], A)
        self.assertEqual(handoff[0]["expected_archive_sha256"], A)
        self.assertEqual(handoff[0]["member_sha256"], B)
        self.assertFalse(handoff[0]["dispatch_automatically"])
        self.assertFalse(handoff[0]["entire_archive_review_required"])
        self.assertTrue(handoff[0]["source_member_review_required"])
        self.assertFalse(handoff[0]["staging_may_include_other_unmatched_source_members"])
        self.assertEqual(handoff[0]["stage_member"], "src/recovered.py")
        self.assertEqual(handoff[0]["stage_member_sha256"], B)
        self.assertNotEqual(handoff[0]["confirm_source_review"], True)

    def test_missing_source_after_checkpoint_prevents_engineering_stage(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "engineering",
             "source_path": "tools/new.py", "reason": "verified missing source",
             "provenance_verified": True, "publication_authorized": True}]})
        report = q.load(self.root / "incoming" / "report.json")
        report["absent_from_current_listing"] = [DRIVE]
        save(self.root / "incoming" / "report.json", report)
        result = self.run_review()
        self.assertEqual(result["records"][0]["state"], "unavailable_source_hold")
        self.assertEqual(result["staging_handoff"], [])
        self.assertIn("absent_from_current_public_listing",
                      [item["type"] for item in result["exceptions"]])

    def test_merged_requires_live_matching_sha_and_tests(self):
        key = self.seed()
        entry = {"candidate_id": key, "state": "merged", "pr": 2459,
                 "merge_commit": "f" * 40, "tests": ["unit"],
                 "source_path": "tools/new.py",
                 "archive_sha256": A, "member_sha256": B,
                 "evidence": "https://github.com/gamesbyian/UR-Recomp/issues/2088"}
        save(self.ledger, {"schema": q.LEDGER, "items": [entry]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merge_unverified")
        save(self.github, {"prs": [{"number": 2459, "state": "MERGED",
                                   "merged_at": "2026-10-24",
                                   "merge_commit_sha": "f" * 40}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merged")
        save(self.github, {"prs": [{"number": 2459, "state": "MERGED",
                                   "merged_at": "2026-10-24",
                                   "merge_commit_sha": "0" * 40}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merge_unverified")

    def test_open_pr_claim_not_auto_merged_and_collision_detected(self):
        key = self.seed()
        save(self.github, {"prs": [{"number": 999, "state": "OPEN",
                                   "body": "vault-member-sha256:" + B}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "open_pr_unverified")
        save(self.github, {"prs": [
            {"number": n, "state": "OPEN", "body": key} for n in (998, 999)]})
        self.assertEqual(self.run_review()["records"][0]["state"], "duplicate_pr_collision")

    def test_partial_run_carries_prior_members_and_errors(self):
        self.seed()
        root = self.root / "incoming"
        report = q.load(root / "report.json")
        report["errors"] = [{"id": "1oversizeArchive000000", "error": "expanded ZIP budget exceeded"}]
        save(root / "report.json", report)
        result = self.run_review()
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["exceptions"][0]["type"], "inspection_failure")

    def test_missing_artifact_and_mixed_queue_fail_closed(self):
        self.seed()
        (self.root / "evidence" / "report.json").unlink()
        with self.assertRaises((OSError, ValueError)):
            self.run_review()
        self.make_artifact("evidence")
        root = self.root / "incoming"
        queue = q.load(root / "queue.json")
        queue["needs_engineering_review"][0]["sha256"] = B
        save(root / "queue.json", queue)
        with self.assertRaises(ValueError):
            self.run_review()

    def test_ledger_identity_conflict_cannot_credit_merged_or_superseded(self):
        key = self.seed()
        base = {"candidate_id": key, "state": "superseded",
                "source_path": "tools/covered.py", "tests": "tests/unit/test_covered.py",
                "evidence": "#2088", "reason": "Already present",
                "drive_id": "1SomeOtherDriveArchiveID"}
        save(self.ledger, {"schema": q.LEDGER, "items": [base]})
        self.assertEqual(self.run_review()["records"][0]["state"], "identity_conflict")
        base["drive_id"] = DRIVE
        base["scope"] = "evidence"
        save(self.ledger, {"schema": q.LEDGER, "items": [base]})
        self.assertEqual(self.run_review()["records"][0]["state"], "identity_conflict")
        base["scope"] = "incoming"
        base["archive_sha256"] = B
        save(self.ledger, {"schema": q.LEDGER, "items": [base]})
        self.assertEqual(self.run_review()["records"][0]["state"], "identity_conflict")
        base["archive_sha256"] = A
        base["member_sha256"] = A
        save(self.ledger, {"schema": q.LEDGER, "items": [base]})
        self.assertEqual(self.run_review()["records"][0]["state"], "identity_conflict")
        base["member_sha256"] = B
        self.assertEqual(q.classify(
            {"candidate_id": key, "scope": "incoming", "drive_id": DRIVE,
             "archive_sha256": A, "member_sha256": B, "member": "src/recovered.py"},
            base, [], {})[0], "superseded")

    def test_merged_provenance_requires_exact_original_hashes_and_evidence(self):
        key = self.seed()
        record = {"candidate_id": key, "state": "merged", "pr": 2459,
                  "merge_commit": "f" * 40, "tests": ["unit"],
                  "source_path": "tools/new.py"}
        save(self.github, {"prs": [{"number": 2459, "state": "MERGED",
                                   "merged_at": "2026-10-24",
                                   "merge_commit_sha": "f" * 40}]})
        save(self.ledger, {"schema": q.LEDGER, "items": [record]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merge_unverified")
        record["archive_sha256"] = A
        record["member_sha256"] = B
        save(self.ledger, {"schema": q.LEDGER, "items": [record]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merge_unverified")
        record["evidence"] = "#2088 source receipt"
        save(self.ledger, {"schema": q.LEDGER, "items": [record]})
        self.assertEqual(self.run_review()["records"][0]["state"], "merged")

    def test_supersession_requires_concrete_evidence(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "superseded", "reason": "same behavior"}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "unresolved")
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "superseded", "reason": "same behavior",
             "source_path": "tools/current.py", "evidence": "#2459",
             "tests": ["tests/unit/test_current.py"]}]})
        self.assertEqual(self.run_review()["records"][0]["state"], "superseded")

    def test_ledger_dispositions_not_lost_when_archive_unavailable(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "held", "reason": "authoritative hold"}]})
        self.make_artifact("incoming")
        result = self.run_review()
        self.assertEqual(result["dispositions_not_in_current_artifacts"], [key])

    def test_reject_duplicate_member_dispositions(self):
        key = self.seed()
        save(self.ledger, {"schema": q.LEDGER, "items": [
            {"candidate_id": key, "state": "held"},
            {"candidate_id": key, "state": "held"}]})
        with self.assertRaises(ValueError):
            self.run_review()


if __name__ == "__main__":
    unittest.main()
