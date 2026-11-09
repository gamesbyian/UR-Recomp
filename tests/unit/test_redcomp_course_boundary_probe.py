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
