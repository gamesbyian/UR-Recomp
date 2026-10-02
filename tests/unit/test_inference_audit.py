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

    def test_second_pass_stream_order_matches_progression_rows(self):
        progression = json.loads(
            (ROOT / "analysis/data/progression-model.json").read_text(encoding="utf-8")
        )
        expected = progression["medal_matrix"]["row_order"]
        actual = [self.courses[i * 5]["tour"] for i in range(9)]
        self.assertEqual(actual, expected)

    def test_second_pass_header_start_relation_is_43_of_45(self):
        self.assertEqual(
            sum(
                1 for row in self.courses
                if row["historical_landmarks"]["start_matches_header_a_x16"]
            ),
            43,
        )

    def test_second_pass_stunt_start_finish_signature(self):
        stunt = [row for row in self.courses if row["track_kind"] == "stunt"]
        non_stunt = [row for row in self.courses if row["track_kind"] != "stunt"]
        self.assertTrue(all(
            row["historical_landmarks"]["start_x"] == row["historical_landmarks"]["finish_x"]
            for row in stunt
        ))
        self.assertFalse(any(
            row["historical_landmarks"]["start_x"] == row["historical_landmarks"]["finish_x"]
            for row in non_stunt
        ))
    def test_historical_track_id_matches_stream_minus_one(self):
        self.assertTrue(all(
            row["historical_landmarks"]["track_id"] == row["stream_index"] - 1
            for row in self.courses
        ))

    def test_resource_bundles_are_ordered_and_adjacent(self):
        catalog = json.loads(
            (ROOT / "analysis/data/course-resource-catalog.json").read_text(encoding="utf-8")
        )
        bundles = {x["id"]: x for x in catalog["structural_bundles"]}
        self.assertTrue(bundles["bundle-03-08"]["all_carriers_preserve_order"])
        self.assertTrue(bundles["bundle-03-08"]["all_carriers_preserve_adjacency"])
        self.assertTrue(bundles["bundle-09-0B"]["all_carriers_preserve_order"])
        self.assertTrue(bundles["bundle-09-0B"]["all_carriers_preserve_adjacency"])
        self.assertTrue(catalog["list_level_invariants"]["stunt_lists_have_no_duplicate_resource_ids"])

    def test_racer_frame_header_popcount_matches_word_count(self):
        presentation = json.loads(
            (ROOT / "analysis/data/presentation-assets.json").read_text(encoding="utf-8")
        )
        frames = presentation["families"][0]["frames"]
        for frame in frames:
            header = bytes.fromhex(frame["record_header_hex"])
            popcount = sum(byte.bit_count() for byte in header)
            self.assertEqual(popcount, frame["packed_word_count"])
            self.assertEqual(frame["record_length"], 4 + 2 * popcount)

if __name__ == "__main__":
    unittest.main()
