import json
import tempfile
import unittest
from pathlib import Path

from tools.summarize_color_math_state import summarize


class ColorMathSummaryTests(unittest.TestCase):
    def test_decodes_raw_color_math_fields(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            regs = p / "x.regs.json"
            regs.write_text(json.dumps({
                "frame_tag": 12,
                "ppu": {
                    "tm": "13", "ts": "00", "tmw": "00", "tsw": "00",
                    "cgwsel": "02", "cgadsub": "62",
                    "fixed_color": {"r": 1, "g": 2, "b": 3},
                    "inidisp": {"brightness": 15, "forced_blank": 0},
                },
            }))
            row = summarize(regs)
            self.assertTrue(row["subscreen_math_selected"])
            self.assertEqual(row["color_math_layer_mask"], 0x22)
            self.assertTrue(row["half"])
            self.assertFalse(row["subtract"])
            self.assertEqual(row["subscreen_layer_mask"], 0)


if __name__ == "__main__":
    unittest.main()
