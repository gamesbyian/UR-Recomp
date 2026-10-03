from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_course_resource_lists as mod


def payload(*, cursor: int = 0x10, resources: bytes = b"\x01\x24\xff") -> bytes:
    data = bytearray(0x20)
    data[2] = 45
    data[3:11] = bytes.fromhex("44 00 32 00 45 00 33 00")
    data[11:13] = cursor.to_bytes(2, "little")
    data[13:15] = bytes([0, 4])
    data[cursor : cursor + len(resources)] = resources
    return bytes(data)


class CourseResourceListTests(unittest.TestCase):
    def test_parser_decodes_header_tail_and_zero_dimension_sentinel(self):
        result = mod.parse_course_resource_list(payload())
        self.assertEqual(result["stunt_time_or_mode"], 45)
        self.assertEqual(result["spawn_or_landmark_a"], [68, 50])
        self.assertEqual(result["spawn_or_landmark_b"], [69, 51])
        self.assertEqual(result["resource_ids"], [0x01, 0x24])
        self.assertEqual(result["resource_terminator_offset"], 0x12)
        self.assertEqual(result["layout_dims"], [256, 4])

    def test_parser_rejects_invalid_cursor_and_unterminated_list(self):
        with self.assertRaisesRegex(ValueError, "outside decoded payload"):
            mod.parse_course_resource_list(payload(cursor=0x40))
        with self.assertRaisesRegex(ValueError, "no FF terminator"):
            mod.parse_course_resource_list(payload(resources=b"\x01" * 0x10))

    def test_usage_fingerprint_is_order_independent_but_position_sensitive(self):
        occurrences = [(2, 2, 4), (1, 1, 3)]
        self.assertEqual(
            mod.usage_fingerprint(occurrences),
            mod.usage_fingerprint(list(reversed(occurrences))),
        )
        self.assertNotEqual(
            mod.usage_fingerprint(occurrences),
            mod.usage_fingerprint([(2, 2, 5), (1, 1, 3)]),
        )

    def test_cross_build_matching_allows_renumbered_resources(self):
        def build(resource_id: int, fingerprint: str) -> dict:
            return {
                "resource_usage": {
                    "resources": [
                        {"resource_id": resource_id, "usage_fingerprint": fingerprint}
                    ]
                }
            }

        matches = mod.build_cross_build_matches(
            {"left": build(0x24, "same-shape"), "right": build(0x31, "same-shape")}
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["left_resource_ids"], [0x24])
        self.assertEqual(matches[0]["right_resource_ids"], [0x31])
        self.assertFalse(matches[0]["same_numeric_ids"])

    def test_course_comparison_records_exact_append_and_header_delta(self):
        reference = [{
            "index": 1,
            "stunt_time_or_mode": 0,
            "spawn_or_landmark_a": [10, 20],
            "spawn_or_landmark_b": [30, 40],
            "resource_ids": [1, 2],
            "layout_dims": [32, 32],
        }]
        candidate = [{
            **reference[0],
            "spawn_or_landmark_a": [10, 18],
            "resource_ids": [1, 2, 0x22],
        }]

        changes = mod.compare_course_headers(reference, candidate)

        self.assertEqual(changes[0]["index"], 1)
        self.assertEqual(
            changes[0]["fields"]["spawn_or_landmark_a"],
            {"before": [10, 20], "after": [10, 18]},
        )
        self.assertEqual(
            changes[0]["resource_list_change"],
            {"kind": "append", "values": [0x22]},
        )

    def test_course_comparison_rejects_misaligned_corpora(self):
        with self.assertRaisesRegex(ValueError, "different lengths"):
            mod.compare_course_headers([], [{"index": 1}])
        with self.assertRaisesRegex(ValueError, "different stream ordering"):
            mod.compare_course_headers([{"index": 1}], [{"index": 2}])

    def test_stale_output_check_is_read_only_and_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "current.txt"
            stale = Path(temp_dir) / "stale.txt"
            missing = Path(temp_dir) / "missing.txt"
            directory = Path(temp_dir) / "directory.txt"
            current.write_text("expected\n", encoding="utf-8")
            stale.write_text("old\n", encoding="utf-8")
            directory.mkdir()

            result = mod.stale_outputs(
                {
                    current: "expected\n",
                    stale: "expected\n",
                    missing: "expected\n",
                    directory: "expected\n",
                }
            )

            self.assertEqual(result, [stale, missing, directory])
            self.assertEqual(stale.read_text(encoding="utf-8"), "old\n")
            self.assertFalse(missing.exists())
            self.assertTrue(directory.is_dir())

    def test_preserved_corpus_matches_checked_in_manifests(self):
        if not all((ROOT / path).exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        manifest = mod.build_manifest()
        self.assertEqual(mod.stale_outputs(mod.generated_contents(manifest)), [])
        self.assertEqual(json.loads(mod.JSON_OUT.read_text(encoding="utf-8")), manifest)
        for build in manifest["builds"].values():
            self.assertEqual(build["resource_usage"]["course_count"], 45)
        deltas = manifest["course_header_and_resource_deltas"]["builds"]
        self.assertEqual(
            [item["index"] for item in deltas["europe-retail"]], [4, 26, 36]
        )
        self.assertEqual(deltas["legacy-beta"], [])
        self.assertEqual(deltas["pal-prototype-1994-11-29"], [])
        for item in deltas["europe-retail"][1:]:
            self.assertEqual(
                item["resource_list_change"], {"kind": "append", "values": [0x22]}
            )


if __name__ == "__main__":
    unittest.main()
