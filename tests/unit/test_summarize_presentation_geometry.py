import json
import tempfile
import unittest
from pathlib import Path

from tools.summarize_presentation_geometry import row_metrics, summarize_dir, summarize_dump


class PresentationGeometryTests(unittest.TestCase):
    def test_row_metrics_detect_bottom_content(self):
        raw = bytearray(4 * 4 * 4)
        # Width=4, height=4. Put one non-black BGRX pixel on final row.
        raw[(3 * 4 + 2) * 4 : (3 * 4 + 3) * 4] = bytes((1, 2, 3, 0))
        r = row_metrics(bytes(raw), 4, 4, rows=1)
        self.assertEqual(r["bottom"]["nonzero_pixels"], 1)
        self.assertEqual(r["last_row"]["nonzero_pixels"], 1)

    def test_summarize_dump_carries_geometry_registers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tag = "x"
            (root / f"{tag}.info.json").write_text(json.dumps({
                "frame": 10, "fb_width": 2, "fb_height": 2
            }))
            (root / f"{tag}.regs.json").write_text(json.dumps({"ppu": {
                "setini": "00", "screen_height": 224, "interlace": 0,
                "pseudo_hires": 0, "inidisp": {"brightness": 15, "forced_blank": 0},
                "bgmode": 1, "mosaic_size": 1, "tm": "13", "ts": "10",
                "tmw": "00", "tsw": "00", "cgwsel": "02", "cgadsub": "7F"
            }}))
            (root / f"{tag}.fb.bgrx").write_bytes(bytes(2 * 2 * 4))
            row = summarize_dump(root, tag)
            self.assertEqual(row["ppu"]["screen_height"], 224)
            self.assertEqual(row["framebuffer"]["height"], 2)

    def test_summarize_dir_accepts_core_without_debug_regs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tag = "beetle"
            (root / f"{tag}.info.json").write_text(json.dumps({
                "frame": 20, "fb_width": 2, "fb_height": 2,
                "core_name": "Beetle"
            }))
            (root / f"{tag}.fb.bgrx").write_bytes(bytes(2 * 2 * 4))
            report = summarize_dir(root)
            self.assertEqual(report["checkpoints"][0]["core_name"], "Beetle")
            self.assertIsNone(report["checkpoints"][0]["ppu"])


if __name__ == "__main__":
    unittest.main()
