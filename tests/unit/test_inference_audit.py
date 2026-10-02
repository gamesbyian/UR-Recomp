import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class InferenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.courses = json.loads(
            (ROOT / "analysis/data/course-corpus.json").read_text(encoding="utf-8")
        )["courses"]
        cls.audit = json.loads(
            (ROOT / "analysis/generated/inference-audit.json").read_text(encoding="utf-8")
        )

    def test_resource_cursor_equation_holds_for_full_corpus(self):
        self.assertEqual(len(self.courses), 45)
        for course in self.courses:
            resources = course["resources"]
            header = course["header"]
            self.assertEqual(
                resources["bytes_from_initial_cursor_through_eof"],
                resources["count"] + 2,
            )
            self.assertEqual(
                resources["terminator_offset"],
                header["resource_cursor_initial"] + resources["count"],
            )
            self.assertEqual(resources["bytes_after_terminator"], 1)

    def test_six_dimension_families_partition_all_courses(self):
        counts = {}
        for course in self.courses:
            key = "x".join(map(str, course["header"]["layout_dims"]))
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(
            counts,
            {
                "256x4": 4,
                "128x8": 3,
                "64x16": 22,
                "32x32": 11,
                "16x64": 4,
                "4x256": 1,
            },
        )

    def test_fixed_area_derived_geometry(self):
        for course in self.courses:
            w, h = course["derived_presentation_geometry"]["world_extent"]
            self.assertEqual(w * h, 67108864)
            self.assertEqual(
                course["derived_presentation_geometry"]["coarse_entry_count"],
                16384,
            )

    def test_audit_records_expected_high_value_findings(self):
        ids = {finding["id"] for finding in self.audit["findings"]}
        for expected in {"IA-C01", "IA-C02", "IA-C03", "IA-C04", "IA-S01", "IA-P01"}:
            self.assertIn(expected, ids)


if __name__ == "__main__":
    unittest.main()
