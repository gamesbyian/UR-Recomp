"""Audit of immutable three-source inventories and application decisions."""
from __future__ import annotations
from copy import deepcopy
import unittest

from tools.audit_three_project_apparatus import (
    BALD, MAL, UR, MATRIX, read, validate, PINS
)


class ThreeProjectApparatusAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bald, cls.mal, cls.ur, cls.matrix = (
            read(BALD), read(MAL), read(UR), read(MATRIX)
        )

    def test_repository_snapshots_and_all_references_validate(self):
        self.assertEqual(validate(self.bald, self.mal, self.ur, self.matrix), [])
        self.assertEqual(len(self.mal["entries"]), 1062)
        self.assertEqual(self.mal["blob_entries"], 1006)
        self.assertEqual(len(self.ur["entries"]), 2680)
        self.assertGreaterEqual(len(self.matrix["entries"]), 30)
        self.assertEqual(self.matrix["pins"], PINS)

    def test_unrecognized_source_claim_rejected(self):
        matrix = deepcopy(self.matrix)
        matrix["entries"][0]["ur"].append("tools/not_a_real_tool.py")
        errors = validate(self.bald, self.mal, self.ur, matrix)
        self.assertTrue(any("ungrounded ur path" in e for e in errors))

    def test_missing_upstream_and_duplicate_path_rejected(self):
        mal = deepcopy(self.mal)
        mal["entries"][1]["path"] = mal["entries"][0]["path"]
        errors = validate(self.bald, mal, self.ur, self.matrix)
        self.assertTrue(any("duplicate path" in e for e in errors))
        mal = deepcopy(self.mal)
        mal["truncated"] = True
        errors = validate(self.bald, mal, self.ur, self.matrix)
        self.assertTrue(any("completeness changed" in e for e in errors))

    def test_candidate_not_auto_promoted(self):
        for entry in self.matrix["entries"]:
            self.assertIn(entry["priority"], {"P0", "P1", "P2", "P3"})
            self.assertTrue(entry["proof"])
        self.assertNotIn("release_gate_passed", self.matrix)


if __name__ == "__main__":
    unittest.main()
