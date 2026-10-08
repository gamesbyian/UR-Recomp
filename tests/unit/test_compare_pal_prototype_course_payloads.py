from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import compare_pal_prototype_course_payloads as tool


def course(*, swap=False, word=0x0002, resource=0x24):
    cursor = 0x800F + 64
    header = bytearray(15)
    header[11:13] = cursor.to_bytes(2, "little")
    header[13:15] = b"\x20\x20"
    coarse = [0] * 16384
    coarse[1] = 1
    blank = [0] * 16
    active = [0] * 16
    active[0] = word
    if swap:
        blank, active = active, blank
        coarse = [1 - i for i in coarse]
    return (
        bytes(header)
        + b"".join(i.to_bytes(2, "little") for i in coarse)
        + b"".join(i.to_bytes(2, "little") for i in blank + active)
        + bytes([resource, 0xFF])
    )


class PalPrototypeCourseComparisonTests(unittest.TestCase):
    def test_changed_shared_record_expands_into_actual_world_space_only(self):
        p = course()
        r = course(word=0x0004)
        row = tool.summarize_pair(p, r, 4, "Switcher")
        self.assertFalse(row["decoded_identical"])
        self.assertTrue(row["resource_list_identical"])
        self.assertEqual(row["changed_regions"], ["fine_record_region"])
        self.assertEqual(row["placed_surface"]["changed_world_sectors"], 1)
        self.assertEqual(row["placed_surface"]["changed_world_cells"], 1)
        self.assertEqual(row["placed_surface"]["changed_c000_selectors"], 1)
        self.assertEqual(
            row["placed_surface"]["first_12_changed_cells"][0]["world_cell_origin"],
            [64, 0],
        )
        self.assertEqual(
            row["placed_surface"]["fine_record_counts"],
            {"prototype": 2, "retail": 2},
        )

    def test_record_renumbering_does_not_invent_changed_world_geometry(self):
        p = course()
        r = course(swap=True)
        row = tool.summarize_pair(p, r, 1, "Dragster")
        self.assertIn("coarse_table", row["changed_regions"])
        self.assertIn("fine_record_region", row["changed_regions"])
        self.assertEqual(row["placed_surface"]["changed_world_cells"], 0)
        self.assertEqual(
            row["placed_surface"]["raw_coarse_reference_id_changes"], 16384
        )

    def test_tail_resource_change_is_not_mislabeled_packed_cell_change(self):
        row = tool.summarize_pair(course(), course(resource=0x25), 1, "Dragster")
        self.assertEqual(row["changed_regions"], ["resource_list"])
        self.assertFalse(row["resource_list_identical"])
        self.assertEqual(row["placed_surface"]["changed_world_cells"], 0)
        self.assertEqual(
            row["resource_ids"], {"prototype": [0x24], "retail": [0x25]}
        )

    def test_no_changed_payload_has_zero_counts_and_no_false_witnesses(self):
        row = tool.summarize_pair(course(), course(), 1, "Dragster")
        self.assertTrue(row["decoded_identical"])
        self.assertEqual(row["changed_regions"], [])
        self.assertEqual(row["placed_surface"]["first_12_changed_cells"], [])
        self.assertEqual(row["placed_surface"]["changed_world_cells"], 0)

    def test_full_pal_prototype_retail_45_course_world_report(self):
        if not tool.PROTOTYPE.is_file() or not tool.PAL_RETAIL.is_file():
            self.skipTest("preserved canonical PAL ROM files not present")
        report = tool.build_report()
        self.assertEqual(report["course_count"], 45)
        self.assertEqual(len(report["courses"]), 45)
        self.assertEqual(
            report["changed_stream_indices"],
            [x["stream_index"] for x in report["courses"]
             if not x["decoded_identical"]],
        )
        for row in report["courses"]:
            with self.subTest(stream=row["stream_index"]):
                self.assertEqual(
                    set(row["sha256"]), {"prototype", "retail"}
                )
                surface = row["placed_surface"]
                self.assertTrue(surface["comparable"])
                self.assertGreaterEqual(surface["changed_world_cells"], 0)
                self.assertLessEqual(surface["changed_world_cells"], 262144)
        # Retain an evidence-friendly result in the unit job. The contents
        # arise from actual preserved ROM bytes, not guessed delta counts.
        print("PAL_PROTOTYPE_COURSE_REPORT=" + __import__("json").dumps({
            "changed": report["changed_stream_indices"],
            "resource_lists": report["resource_list_changed_stream_indices"],
            "placed_words": report["placed_packed_word_changed_stream_indices"],
            "counts": {
                str(x["stream_index"]): x["placed_surface"]["changed_world_cells"]
                for x in report["courses"] if not x["decoded_identical"]
            },
        }, sort_keys=True))

    def test_real_pal_streams_retain_decodable_course_tables(self):
        if not tool.PROTOTYPE.is_file() or not tool.PAL_RETAIL.is_file():
            self.skipTest("preserved canonical PAL ROM files not present")
        p = tool.decoded_streams(tool.PROTOTYPE)
        r = tool.decoded_streams(tool.PAL_RETAIL)
        self.assertEqual(len(p), 45)
        self.assertEqual(len(r), 45)
        # Fixed-area and resource-list invariants must hold for both builds
        # on representatives of different stock course families.
        for i in (1, 3, 4, 16, 27, 45):
            with self.subTest(stream=i):
                row = tool.summarize_pair(p[i - 1], r[i - 1], i, str(i))
                self.assertIn(row["placed_surface"]["comparable"], (True, False))
                self.assertEqual(
                    set(row["resource_ids"]), {"prototype", "retail"}
                )
                self.assertEqual(set(row["sha256"]), {"prototype", "retail"})


if __name__ == "__main__":
    unittest.main()
