"""Synthetic retention/provenance checks; no GitHub network needed."""
import copy
import unittest
from tools.artifact_retention_preflight import inspect

SOURCE = "a" * 40
DIFFERENT = "b" * 40
DIGEST = "c" * 64
RUN = {"id": 42, "name": "Windows build", "status": "completed",
       "conclusion": "success", "head_sha": SOURCE}
ROW = {"id": 77, "name": "windows-native-smoke", "size_in_bytes": 900,
       "digest": "sha256:" + DIGEST,
       "created_at": "2026-10-26T01:00:00Z",
       "expires_at": "2026-11-02T01:00:00Z", "expired": False,
       "workflow_run": {"id": 42, "head_sha": SOURCE}}


def listing():
    return {"total_count": 1, "artifacts": [copy.deepcopy(ROW)]}


class ArtifactAvailabilityTests(unittest.TestCase):
    def test_realistic_source_bound_metadata_unchecked_bytes(self):
        result = inspect(RUN, listing(), expected_sha=SOURCE,
                         now="2026-10-27T01:00:00Z")
        self.assertEqual(result["artifacts"][0]["availability"],
                         "metadata_ready_for_independent_byte_audit")
        self.assertTrue(result["artifact_census_complete"])
        self.assertFalse(result["artifacts"][0]["authoritative_release_evidence"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_missing_expected_source_is_unknown_not_success(self):
        result = inspect(RUN, listing(), now="2026-10-27T01:00:00Z")
        self.assertIsNone(result["source_matches_expected"])
        self.assertEqual(result["artifacts"][0]["availability"], "source_unqualified")

    def test_source_mismatch_and_nonpassing_run(self):
        self.assertEqual(inspect(RUN, listing(), expected_sha=DIFFERENT,
                         now="2026-10-27T01:00:00Z")["artifacts"][0]["availability"],
                         "source_unqualified")
        producer = {**RUN, "conclusion": "failure"}
        self.assertEqual(inspect(producer, listing(), expected_sha=SOURCE,
                         now="2026-10-27T01:00:00Z")["artifacts"][0]["availability"],
                         "producer_not_successful")

    def test_expired_and_soon_expiring(self):
        imminent = inspect(RUN, listing(), expected_sha=SOURCE,
                           now="2026-11-01T01:30:00Z")
        self.assertEqual(imminent["artifacts"][0]["availability"],
                         "expiry_urgent_review")
        out = inspect(RUN, listing(), expected_sha=SOURCE,
                      now="2026-11-03T01:30:00Z")
        self.assertEqual(out["artifacts"][0]["availability"],
                         "expired_or_unavailable")

    def test_missing_digest_and_partial_page(self):
        x = listing()
        x["artifacts"][0]["digest"] = None
        x["total_count"] = 25
        res = inspect(RUN, x, expected_sha=SOURCE,
                      now="2026-10-27T01:00:00Z")
        self.assertFalse(res["artifact_census_complete"])
        self.assertEqual(res["artifacts"][0]["availability"],
                         "digest_or_bytes_missing")

    def test_cross_source_or_run_mismatch_rejected(self):
        for key, changed in (("id", 999), ("head_sha", DIFFERENT)):
            x = listing()
            x["artifacts"][0]["workflow_run"][key] = changed
            with self.assertRaisesRegex(ValueError, "different run/source"):
                inspect(RUN, x, expected_sha=SOURCE,
                        now="2026-10-27T01:00:00Z")

    def test_invalid_digest_timestamps_and_duplicate_id(self):
        x = listing()
        x["artifacts"][0]["digest"] = "sha256:" + "BAD"
        with self.assertRaisesRegex(ValueError, "digest"):
            inspect(RUN, x, expected_sha=SOURCE)
        x = listing()
        x["artifacts"][0]["expires_at"] = "2026-10-01T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "expiry predates"):
            inspect(RUN, x, expected_sha=SOURCE)
        x = listing()
        x["artifacts"].append(copy.deepcopy(x["artifacts"][0]))
        x["total_count"] = 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect(RUN, x, expected_sha=SOURCE)

    def test_run_metadata_not_release_authority(self):
        x = inspect(RUN, listing(), expected_sha=SOURCE,
                    now="2026-10-27T01:00:00Z")
        self.assertTrue(any("not a bytes check" in v for v in x["limits"]))
        self.assertIsNone(inspect(RUN, listing(),
                          now="2026-10-27T01:00:00Z")["source_matches_expected"])


if __name__ == "__main__":
    unittest.main()
