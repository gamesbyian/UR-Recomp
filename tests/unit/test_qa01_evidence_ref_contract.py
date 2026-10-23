"""QA01 source evidence pointers must be typed, local JSON references.

This guards the shape of an audit pointer, not its existence, provenance,
original/native parity, or any release gate.
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_original_course_event_coverage as audit


class QA01EvidenceRefContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(audit.CATALOG.read_text(encoding="utf-8"))
        cls.evidence = json.loads(audit.EVIDENCE.read_text(encoding="utf-8"))

    def test_current_source_references_remain_valid(self):
        self.assertEqual(len(self.evidence["observations"]), 4)
        for row in self.evidence["observations"]:
            self.assertTrue(audit.canonical_evidence_ref(row["evidence_ref"]))
        self.assertEqual(audit.build_census(self.catalog, self.evidence)["status_counts"],
                         {"partial": 4, "unverified": 131})

    def test_malformed_and_nonlocal_evidence_refs_fail_closed(self):
        malformed = (
            None, True, 1, [], ["analysis/data/evidence.json"],
            {"path": "analysis/data/evidence.json"}, "", " ",
            "/analysis/data/evidence.json", "../analysis/data/evidence.json",
            "analysis/data/../evidence.json", "analysis/data//evidence.json",
            "analysis/data/.hidden.json", "analysis/data/evidence.json/",
            "analysis/data/evidence.txt", "analysis/data/evidence.json\n",
            "analysis\\data\\evidence.json", "https://example.com/evidence.json",
            "reference/evidence.json", "analysis/data/%2e%2e/evidence.json",
        )
        for value in malformed:
            with self.subTest(value=value):
                self.assertFalse(audit.canonical_evidence_ref(value))
                changed = copy.deepcopy(self.evidence)
                changed["observations"][0]["evidence_ref"] = value
                with self.assertRaisesRegex(ValueError, "evidence path"):
                    audit.build_census(self.catalog, changed)

    def test_safe_nested_json_pointer_is_shape_only(self):
        # No I/O or assertion of independent source authentication here.
        value = "analysis/data/qa01/source-observation.json"
        self.assertTrue(audit.canonical_evidence_ref(value))
        changed = copy.deepcopy(self.evidence)
        changed["observations"][0]["evidence_ref"] = value
        result = audit.build_census(self.catalog, changed)
        self.assertEqual(result["entries"][0]["evidence_ref"], value)
        self.assertEqual(result["entries"][0]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
