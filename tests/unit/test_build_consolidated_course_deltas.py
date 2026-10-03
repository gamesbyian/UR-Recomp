from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_consolidated_knowledge as mod


class ConsolidatedCourseDeltaTests(unittest.TestCase):
    def test_summary_is_derived_from_hashes_and_structured_deltas(self):
        rnc_manifest = {
            "roms": {
                "usa-retail": {"streams": [
                    {"index": 1, "unpacked_sha256": "same"},
                    {"index": 2, "unpacked_sha256": "usa-two"},
                    {"index": 3, "unpacked_sha256": "usa-three"},
                ]},
                "europe-retail": {"streams": [
                    {"index": 1, "unpacked_sha256": "same"},
                    {"index": 2, "unpacked_sha256": "europe-two"},
                    {"index": 3, "unpacked_sha256": "europe-three"},
                ]},
            }
        }
        resource_manifest = {
            "course_header_and_resource_deltas": {"builds": {"europe-retail": [
                {
                    "index": 2,
                    "fields": {"resource_ids": {"before": [1], "after": [1, 34]}},
                    "resource_list_change": {"kind": "append", "values": [34]},
                },
                {
                    "index": 3,
                    "fields": {
                        "spawn_or_landmark_a": {
                            "before": [10, 20],
                            "after": [10, 18],
                        }
                    },
                },
            ]}}
        }

        result = mod.summarize_europe_course_deltas(
            resource_manifest, rnc_manifest
        )

        self.assertEqual(result["known_changed_streams"], [2, 3])
        self.assertEqual(result["unchanged_resource_lists"], [3])
        self.assertEqual(
            result["changed_resource_lists"],
            [{
                "stream_index": 2,
                "course": mod.NAMES[1],
                "edit": {"kind": "append", "values": [34]},
            }],
        )
        self.assertEqual(result["other_header_deltas"][0]["stream_index"], 3)
        self.assertEqual(
            result["other_header_deltas"][0]["fields"]["spawn_or_landmark_a"],
            {"before": [10, 20], "after": [10, 18]},
        )

    def test_summary_rejects_different_stream_indices(self):
        rnc_manifest = {"roms": {
            "usa-retail": {"streams": [{"index": 1}]},
            "europe-retail": {"streams": [{"index": 2}]},
        }}
        with self.assertRaisesRegex(ValueError, "stream indices differ"):
            mod.summarize_europe_course_deltas({}, rnc_manifest)


if __name__ == "__main__":
    unittest.main()
