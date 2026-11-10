"""Redcomp edge hypothesis only: no original PPU source or release claims."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import redcomp_course_boundary_probe as probe


def synthetic_wram() -> bytes:
    w = bytearray(0x20000)
    # Full 16384-sector grid, 128x128 coarse cells, 512x512 fine cells.
    w[0x10000 + 13:0x10000 + 15] = b"\x20\x20"
    # All sectors point to fine record 0 except the last X sector of row 0.
    w[0x10000 + 0x000F + 127 * 2:
      0x10000 + 0x000F + 127 * 2 + 2] = (1).to_bytes(2, "little")
    # Left edge fine cell (x=0,y=0), and right edge (x=511,y=0).
    w[0x10000 + 0x800F:0x10000 + 0x800F + 2] = (0x0102).to_bytes(2, "little")
    right = 0x10000 + 0x800F + 32 + 3 * 2
    w[right:right + 2] = (0x0204).to_bytes(2, "little")
    return bytes(w)


# All six header geometries are attested in analysis/data/course-corpus.json.
# The runtime coarse index plane always holds 16,384 entries, but the X
# modulus varies by 64x between the flattest and tallest course families.
COURSE_SHAPES = (
    (256, 4),    # Dragster, Switcher, Wario Paint family
    (128, 8),    # Loopback family
    (64, 16),    # Zoom Zoo / Bowl family
    (32, 32),    # Monster / Jumps family
    (16, 64),    # Wobble / Looper family
    (4, 256),    # Little Dipper
)


def rectangular_course_wram(coarse_header_x: int, coarse_header_y: int) -> bytes:
    """Distinct edge tiles at both Y ends; a structural WRAM fixture only."""
    assert coarse_header_x * coarse_header_y == 1024
    coarse_width = coarse_header_x * 4
    coarse_height = coarse_header_y * 4
    w = bytearray(0x20000)
    # Zero header byte represents 256 (actual 256x4 and 4x256 families).
    w[0x10000 + 13] = coarse_header_x % 256
    w[0x10000 + 14] = coarse_header_y % 256
    coarse_base = 0x10000 + 0x000F
    fine_base = 0x10000 + 0x800F
    for sector_y in (0, coarse_height - 1):
        pos = coarse_base + 2 * (sector_y * coarse_width + coarse_width - 1)
        w[pos:pos + 2] = (1).to_bytes(2, "little")
    # Record 0 belongs to left edge; record 1 to right edge. Make row 0
    # and the last row observably different to catch incorrect Y indexing.
    for record, x_local, row_local, word in (
        (0, 0, 0, 0x0102), (0, 0, 3, 0x0306),
        (1, 3, 0, 0x0204), (1, 3, 3, 0x0408),
    ):
        pos = fine_base + record * 32 + 2 * (row_local * 4 + x_local)
        w[pos:pos + 2] = word.to_bytes(2, "little")
    return bytes(w)


class BoundaryProbeTests(unittest.TestCase):
    def test_wrapped_candidates_distinct_and_current_policy_rejected(self):
        r = probe.compare_edge_policy(synthetic_wram(), row_cell=0, edge_cells=1)
        self.assertEqual(r["grid_cells"], [512, 512])
        self.assertEqual(r["status"], "hypothesis_only_no_original_raster_witness")
        self.assertEqual([x["query_cell"][0] for x in r["rows"]], [-1, 512])
        self.assertEqual([x["redcomp_wrapped_cell"][0] for x in r["rows"]], [511, 0])
        self.assertEqual([x["wrapped_word"] for x in r["rows"]], ["0204", "0102"])
        self.assertEqual([x["wrapped_fine_record"] for x in r["rows"]], [1, 0])
        self.assertTrue(all(x["ur_direct_lookup"] == "reject_outside_grid"
                            and x["original_ppu_match"] == "not_measured"
                            for x in r["rows"]))
        self.assertFalse(r["decoded_stream_identity"]["full_payload_verified"])

    def test_multi_step_modulo_and_determinism(self):
        a = probe.compare_edge_policy(synthetic_wram(), 0, 3)
        b = probe.compare_edge_policy(synthetic_wram(), 0, 3)
        self.assertEqual(a, b)
        self.assertEqual([x["redcomp_wrapped_cell"][0] for x in a["rows"]],
                         [509, 510, 511, 0, 1, 2])

    def test_all_six_usa_course_shape_families_have_distinct_x_wraps(self):
        # Tests only the *candidate* source-word policy: there is no
        # independent original-ROM PPU/VRAM edge frame in this fixture.
        for header_x, header_y in COURSE_SHAPES:
            with self.subTest(header=(header_x, header_y)):
                w = rectangular_course_wram(header_x, header_y)
                cells_x = header_x * 16
                cells_y = header_y * 16
                first = probe.compare_edge_policy(w, row_cell=0, edge_cells=1)
                last = probe.compare_edge_policy(
                    w, row_cell=cells_y - 1, edge_cells=1
                )
                self.assertEqual(first["grid_cells"], [cells_x, cells_y])
                self.assertEqual(last["grid_cells"], [cells_x, cells_y])
                self.assertEqual(
                    [entry["query_cell"][0] for entry in first["rows"]],
                    [-1, cells_x],
                )
                self.assertEqual(
                    [entry["redcomp_wrapped_cell"][0]
                     for entry in first["rows"]],
                    [cells_x - 1, 0],
                )
                self.assertEqual(
                    [entry["wrapped_word"] for entry in first["rows"]],
                    ["0204", "0102"],
                )
                self.assertEqual(
                    [entry["wrapped_word"] for entry in last["rows"]],
                    ["0408", "0306"],
                )
                for report in (first, last):
                    self.assertEqual(
                        report["status"],
                        "hypothesis_only_no_original_raster_witness",
                    )
                    self.assertFalse(
                        report["decoded_stream_identity"]["full_payload_verified"]
                    )
                    self.assertTrue(all(
                        e["original_ppu_match"] == "not_measured"
                        and e["ur_direct_lookup"] == "reject_outside_grid"
                        for e in report["rows"]
                    ))

    def test_narrowest_course_wraps_multiple_times_within_bounded_probe(self):
        # Little Dipper has only 64 fine cells in X, but a 1024-cell
        # Y extent. A bounded edge probe may traverse repeated X domains.
        w = rectangular_course_wram(4, 256)
        r = probe.compare_edge_policy(w, row_cell=0, edge_cells=32)
        self.assertEqual(r["grid_cells"], [64, 4096])
        self.assertEqual(len(r["rows"]), 64)
        self.assertEqual(
            [e["redcomp_wrapped_cell"][0] for e in r["rows"]],
            list(range(32, 64)) + list(range(32)),
        )
        self.assertEqual(r["rows"][31]["wrapped_word"], "0204")
        self.assertEqual(r["rows"][32]["wrapped_word"], "0102")
        self.assertTrue(all(
            e["original_ppu_match"] == "not_measured" for e in r["rows"]
        ))

    def test_rejects_invalid_row_width_identity_and_wram(self):
        w = synthetic_wram()
        for y in (-1, 512):
            with self.assertRaisesRegex(ValueError, "row_cell"):
                probe.compare_edge_policy(w, y, 1)
        for n in (0, 33):
            with self.assertRaisesRegex(ValueError, "edge_cells"):
                probe.compare_edge_policy(w, 0, n)
        with self.assertRaisesRegex(ValueError, "exactly"):
            probe.compare_edge_policy(w[:-1], 0, 1)
        with self.assertRaisesRegex(ValueError, "identity"):
            probe.compare_edge_policy(
                w, 0, 1, identity={"full_payload_verified": False, "fine_record_count": 2},
            )
        with self.assertRaisesRegex(ValueError, "out-of-range fine record"):
            probe.compare_edge_policy(
                w, 0, 1, identity={"full_payload_verified": True, "fine_record_count": 1},
            )

    def test_bound_does_not_make_gameplay_claim(self):
        r = probe.compare_edge_policy(synthetic_wram(), 0, 32)
        self.assertEqual(len(r["rows"]), 64)
        self.assertIn("original-USA BG1", r["next_evidence"])
        self.assertTrue(all(v["original_ppu_match"] == "not_measured" for v in r["rows"]))


if __name__ == "__main__":
    unittest.main()
