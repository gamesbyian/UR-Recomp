"""Bounds actual CPU-direct PPU register provenance without inventing DMA ownership."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from report_ppu_direct_write_provenance import collect


def event(frame, v, cycles, pc, addr, value):
    return (f"PPUPCTRACE frame={frame} v={v} cycles={cycles} pc={pc} "
            f"addr={addr} val={value} ca=0 cb=0 camx=0 camy=0 "
            "edgex=0 edgey=0 camdx=0")


class PpuDirectWriteProvenanceTests(unittest.TestCase):
    def test_same_frame_contiguous_original_pc_sequence(self):
        lines = [
            event(1006, 239, 10, "82D390", "2116", "48"),
            event(1006, 239, 11, "82D393", "2117", "19"),
            event(1006, 239, 12, "82D3A0", "2118", "00"),
            event(1006, 239, 13, "82D3A0", "2119", "38"),
        ]
        report = collect(lines)
        self.assertEqual(report["contiguous_word_quad_count"], 1)
        self.assertEqual(report["contiguous_word_quads"][0]["vmadd_word"], 0x1948)
        self.assertEqual(report["contiguous_word_quads"][0]["source_pcs"][0], "82D390")
        self.assertFalse(report["complete_provenance"])
        self.assertFalse(report["contiguous_word_quads"][0]["final_vram_destination_proven"])

    def test_intervening_register_write_or_absent_half_is_not_pair(self):
        lines = [
            event(7, 239, 1, "82D390", "2116", "48"),
            event(7, 239, 2, "82D393", "2117", "19"),
            "UNRELATED evidence line",
            event(7, 239, 3, "82D3A0", "2118", "00"),
            event(7, 239, 4, "82D3A0", "2119", "38"),
        ]
        self.assertEqual(collect(lines)["contiguous_word_quad_count"], 0)
        lines.pop(2)
        self.assertEqual(collect(lines)["contiguous_word_quad_count"], 1)
        self.assertEqual(collect(lines[:3])["contiguous_word_quad_count"], 0)

    def test_malformed_or_backward_time_must_be_visible(self):
        lines = [
            event(11, 240, 3, "82D390", "2116", "48"),
            event(11, 238, 2, "82D393", "2117", "19"),
            "PPUPCTRACE bad_event",
        ]
        result = collect(lines)
        self.assertEqual(len(result["ordering_violations"]), 1)
        self.assertEqual(result["unparseable_or_unsupported_rows"], 1)
        with self.assertRaises(ValueError):
            collect(lines, from_frame=11, to_frame=10)

    def test_frame_window_and_cross_frame_rejection(self):
        lines = [
            event(5, 239, 10, "82D390", "2116", "48"),
            event(5, 239, 11, "82D393", "2117", "19"),
            event(6, 239, 12, "82D3A0", "2118", "00"),
            event(6, 239, 13, "82D3A0", "2119", "38"),
        ]
        self.assertEqual(collect(lines)["contiguous_word_quad_count"], 0)
        self.assertEqual(collect(lines, from_frame=6)["trace_rows"], 2)


if __name__ == "__main__":
    unittest.main()
