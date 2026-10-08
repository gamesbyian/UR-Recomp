from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_live_course_world_cells as probe

FIXTURE = ROOT / "analysis/data/dragster-finish-live-course-cells.json"
SPATIAL = ROOT / "analysis/generated/dragster-presentation-spatial-contract.json"


def synthetic_wram() -> bytearray:
    w = bytearray(probe.WRAM_SIZE)
    # 32x32 header -> 128x128 coarse sectors.
    w[probe.COURSE_BASE + 13:probe.COURSE_BASE + 15] = b"\x20\x20"
    # Sector (1,2) uses fine record #1; all others use zero record.
    sector = 2 * 128 + 1
    w[probe.COARSE_BASE + 2 * sector:probe.COARSE_BASE + 2 * sector + 2] = b"\x01\x00"
    # Fine record 1, local cell (2,3) picks C000 slot 5.
    cell = 3 * 4 + 2
    offset = probe.FINE_BASE + 32 + 2 * cell
    w[offset:offset + 2] = b"\x0A\x00"
    w[probe.C000_BASE + 5] = 0x14
    return w


class LiveCourseWorldCellProbeTests(unittest.TestCase):
    def test_placed_16x16_surface_reads_runtime_c000_behavior(self):
        w = synthetic_wram()
        # Sector (1,2) starts at (64,128); cell (2,3) is at (96,176).
        shape = probe.read_world_shape(w)
        p = probe.world_cell(w, 99, 180, *shape)
        self.assertEqual(p["world_rect"], [96, 176, 111, 191])
        self.assertEqual(p["coarse_sector"], [1, 2])
        self.assertEqual(p["fine_record_id"], 1)
        self.assertEqual(p["fine_cell"], [2, 3])
        self.assertEqual(p["packed_word"], "000A")
        self.assertEqual(p["c000_slot"], 5)
        self.assertEqual(p["c000_behavior_code"], 0x14)
        self.assertEqual(p["a000_range"], [160, 191])

    def test_special_word_does_not_invent_a_resource_slot(self):
        w = synthetic_wram()
        r = probe.world_cell(w, 0, 0, *probe.read_world_shape(w))
        self.assertEqual(r["packed_word"], "0000")
        self.assertIsNone(r["c000_slot"])
        self.assertIsNone(r["c000_behavior_code"])
        self.assertIsNone(r["a000_range"])

    def test_rectangle_returns_unique_cells_and_explicit_identity_limit(self):
        w = synthetic_wram()
        result = probe.query_rect(w, (95, 175, 112, 192))
        self.assertEqual(result["cell_count"], 9)
        self.assertFalse(result["stream_identity"]["full_payload_verified"])
        self.assertEqual(result["cells"][0]["world_rect"], [80, 160, 95, 175])
        self.assertEqual(result["cells"][4]["world_rect"], [96, 176, 111, 191])

    def test_invalid_runtime_layout_coordinates_or_record_fail_closed(self):
        w = synthetic_wram()
        with self.assertRaisesRegex(ValueError, "exactly"):
            probe.read_world_shape(w[:-1])
        w[probe.COURSE_BASE + 14] = 0x10
        with self.assertRaisesRegex(ValueError, "16384"):
            probe.read_world_shape(w)
        w = synthetic_wram()
        with self.assertRaisesRegex(ValueError, "outside runtime course extent"):
            probe.world_cell(w, 8192, 0, *probe.read_world_shape(w))
        with self.assertRaisesRegex(ValueError, "reversed"):
            probe.query_rect(w, (3, 4, 2, 4))
        with self.assertRaisesRegex(ValueError, "bounded"):
            probe.query_rect(w, (0, 0, 1023, 1023), max_cells=1)
        with self.assertRaisesRegex(ValueError, "outside course world extent"):
            probe.query_rect(w, (0, 0, 8192, 0))
        # Record #1 exists in physical WRAM, but a verified stream with only
        # record #0 must reject the record even though the bytes are readable.
        with self.assertRaisesRegex(ValueError, "out-of-range fine record"):
            probe.query_rect(
                w, (96, 176, 111, 191),
                stream_identity={"fine_record_count": 1},
            )
        sector = 2 * 128 + 1
        w[probe.COARSE_BASE + 2 * sector:probe.COARSE_BASE + 2 * sector + 2] = b"\xff\xff"
        with self.assertRaisesRegex(ValueError, "out-of-range fine record"):
            probe.world_cell(w, 96, 176, *probe.read_world_shape(w))

    def test_live_reference_fixture_agrees_with_independent_rom_spatial_contract(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        spatial = json.loads(SPATIAL.read_text(encoding="utf-8"))
        cp = spatial["resources"]["checkpoint_finish"]
        self.assertEqual(fixture["provenance"]["guest_frame"], 2903)
        self.assertEqual(len(fixture["cells"]), 16)
        self.assertEqual(fixture["course"]["coarse_grid"], [1024, 16])
        index = {}
        for sector in cp["coarse_sector_placements"]:
            for cell in sector["checkpoint_local_cells"]:
                x = sector["world_rect"][0] + cell["local_x"] * 16
                y = sector["world_rect"][1] + cell["local_y"] * 16
                index[x, y] = (
                    sector["record_id"], cell["word_hex"], cell["c000_slot"]
                )
        for c in fixture["cells"]:
            key = tuple(c["world_origin"])
            self.assertIn(key, index)
            self.assertEqual(
                index[key],
                (c["fine_record_id"], c["packed_word"], c["c000_slot"]),
                key,
            )
            self.assertEqual(c["c000_behavior_code"], 0x14)

    def test_native_fixture_can_be_replayed_through_exact_world_cell_lookup(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        w = bytearray(probe.WRAM_SIZE)
        w[probe.COURSE_BASE + 13:probe.COURSE_BASE + 15] = b"\x00\x04"
        # Only three sectors and their fine records are needed for the
        # captured finish rectangle. Everything else remains zero.
        for c in fixture["cells"]:
            x, y = c["world_origin"]
            sx, sy = x // 64, y // 64
            coarse_off = probe.COARSE_BASE + 2 * (sy * 1024 + sx)
            w[coarse_off:coarse_off + 2] = c["fine_record_id"].to_bytes(2, "little")
            lx, ly = x // 16 % 4, y // 16 % 4
            off = probe.FINE_BASE + c["fine_record_id"] * 32 + (ly * 4 + lx) * 2
            w[off:off + 2] = int(c["packed_word"], 16).to_bytes(2, "little")
            w[probe.C000_BASE + c["c000_slot"]] = c["c000_behavior_code"]
        result = probe.query_rect(w, tuple(fixture["query_rect"]))
        self.assertEqual(result["cell_count"], len(fixture["cells"]))
        expected = {tuple(c["world_origin"]): c for c in fixture["cells"]}
        for cell in result["cells"]:
            key = tuple(cell["world_rect"][:2])
            self.assertEqual(cell["fine_record_id"], expected[key]["fine_record_id"])
            self.assertEqual(cell["packed_word"], expected[key]["packed_word"])
            self.assertEqual(cell["c000_slot"], expected[key]["c000_slot"])
            self.assertEqual(cell["c000_behavior_code"], expected[key]["c000_behavior_code"])


if __name__ == "__main__":
    unittest.main()
