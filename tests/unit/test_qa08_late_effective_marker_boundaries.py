"""ROM-free fail-closed admission of QA08 effective-PPU native log event names.

The Windows producer retains every line beginning UR_QA08_LATE_, so a
fabricated event that embeds a genuine marker must never count as a pixel.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_late_effective_trace_verify as witness


class EffectivePpuMarkerBoundaryTests(unittest.TestCase):
    def test_genuine_source_row_remains_admitted(self):
        x, y = witness.POINTS[0]
        line = (
            f"UR_QA08_LATE_PPU_SOURCE frame=5184 x={x} logical_y={y} "
            f"ppu_line={y+1} sub=0 layer=0 directcolor=0 "
            "index=6c selected_rgb555=56b5 cgram_index_word=56b5 "
            "cgram6c=56b5 cgram6d=4a52 cgram6e=4631 cgram6f=4210 "
            "inidisp=0f cgadsub=00 cgwsel=00"
        )
        self.assertEqual(witness.parse_row(line)[0], "source")
        self.assertIsNone(witness.parse_row("DEBUG " + line))
        with self.assertRaisesRegex(ValueError, "unknown effective-PPU"):
            witness.parse_row("UR_QA08_LATE_FAKE " + line)

    def test_unknown_and_prefixed_override_events_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown effective-PPU"):
            witness.parse_row("UR_QA08_LATE_FAKE frame=5184")
        with self.assertRaisesRegex(ValueError, "host OBJ palette override"):
            witness.parse_row("UR_QA08_LATE_SPAN_OBJECT_OVERRIDE frame=5184")
        self.assertIsNone(witness.parse_row("INFO unrelated renderer event"))


if __name__ == "__main__":
    unittest.main()
