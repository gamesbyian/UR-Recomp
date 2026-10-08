from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_course_checkpoint_placements as mod


def synthetic_course() -> bytes:
    # Two 32-byte fine records; only record #1 includes target slot #1.
    cursor = 0x800F + 64
    header = bytearray(15)
    header[11:13] = cursor.to_bytes(2, "little")
    header[13:15] = b"\x20\x20"  # 32x32 -> 128x128 coarse sectors
    coarse = [0] * 16384
    coarse[0] = 1
    coarse[1] = 1
    record0 = [0] * 16
    record1 = [0] * 16
    record1[0] = 0x0002  # C000 slot #1
    record1[5] = 0x0004  # C000 slot #2
    return (
        bytes(header)
        + b"".join(x.to_bytes(2, "little") for x in coarse)
        + b"".join(x.to_bytes(2, "little") for x in record0 + record1)
        + b"\x24\xff"
    )


class CheckpointSpatialPlacementTests(unittest.TestCase):
    def test_target_cells_use_both_coarse_and_fine_coordinates(self):
        cells = mod.place_resource_cells(
            synthetic_course(), [{"resource_id": 0x24, "start": 1, "end": 1}]
        )
        self.assertEqual(len(cells), 2)
        self.assertEqual([x["world_cell"] for x in cells], [
            [0, 0, 15, 15], [64, 0, 79, 15],
        ])
        self.assertEqual({x["c000_slot"] for x in cells}, {1})
        self.assertEqual({x["fine_record_id"] for x in cells}, {1})

    def test_slot_range_not_resource_id_numeric_equality(self):
        # Resource 0x24 owns slot #2 here; the two slot #1 cells must NOT match.
        cells = mod.place_resource_cells(
            synthetic_course(), [{"resource_id": 0x24, "start": 2, "end": 2}]
        )
        self.assertEqual([x["world_cell"] for x in cells], [
            [16, 16, 31, 31], [80, 16, 95, 31],
        ])
        self.assertEqual(mod.place_resource_cells(synthetic_course(), [], 0x24), [])

    def test_historical_x_probe_does_not_infer_finish_event(self):
        cells = mod.place_resource_cells(
            synthetic_course(), [{"resource_id": 0x24, "start": 1, "end": 1}]
        )
        result = mod.summarize_placements(cells, probe_x=70, query_rect=(60, 0, 70, 12))
        probe = result["historical_finish_x_probe"]
        self.assertEqual(probe["matching_candidate_cells"], 1)
        self.assertEqual(probe["closest_candidate_x_distance"], 0)
        self.assertEqual(result["query"]["candidate_count"], 1)
        self.assertEqual(result["query"]["candidate_cells"][0]["world_cell"], [64, 0, 79, 15])
        self.assertEqual(result["event_authority"], "unconfirmed for individual placements")

    def test_bad_sector_and_alignment_rejected(self):
        data = bytearray(synthetic_course())
        data[15:17] = b"\x02\x00"
        with self.assertRaisesRegex(ValueError, "invalid fine record"):
            mod.place_resource_cells(
                bytes(data), [{"resource_id": 0x24, "start": 1, "end": 1}]
            )
        data = bytearray(synthetic_course())
        data[11:13] = (0x800F + 1).to_bytes(2, "little")
        with self.assertRaisesRegex(ValueError, "fine-record boundary"):
            mod.place_resource_cells(
                bytes(data), [{"resource_id": 0x24, "start": 1, "end": 1}]
            )

    def test_usa_dragster_matches_accepted_spatial_sector_count(self):
        if not mod.ROM.is_file():
            self.skipTest("private canonical USA ROM not present")
        result = mod.inspect_course(mod.ROM.read_bytes(), stream_index=1)
        self.assertEqual(result["resource_0x24_c000_ranges"], [[6, 14]])
        self.assertEqual(result["summary"]["candidate_coarse_sectors"], 31)
        self.assertGreater(result["summary"]["candidate_world_cells"], 0)
        self.assertEqual(result["world_extent"], [65536, 1024])

    def test_usa_stunt_course_has_no_checkpoint_resource(self):
        if not mod.ROM.is_file():
            self.skipTest("private canonical USA ROM not present")
        result = mod.inspect_course(mod.ROM.read_bytes(), stream_index=3)
        self.assertTrue(result["is_stunt"])
        self.assertFalse(result["resource_0x24_present"])
        self.assertEqual(result["summary"]["candidate_world_cells"], 0)


if __name__ == "__main__":
    unittest.main()
