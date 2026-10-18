"""Original 2014 Snes9x layer-priority observer must remain observational."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_instrument_original_snes9x_medal_final_layers as probe

SOURCE = "\n".join((
    probe.REQUIRES,
    probe.ENTRY,
    "GFX.DB = GFX.ZBuffer;",
    probe.OBJ,
    probe.MACRO,
    probe.END,
)) + "\n"

class FinalLayerProbe(unittest.TestCase):
    def test_original_painter_then_each_bg_then_final(self):
        result = probe.patch_source(SOURCE)
        self.assertEqual(result.count(probe.MARK), 1)
        for stage in ('"OBJ"', '"BG"', '"FINAL"'):
            self.assertEqual(result.count('urqa08_original_medal_layer(' + stage), 1)
        self.assertIn("if (sub) return;", result)
        self.assertIn("GFX.DB[p]", result)
        self.assertIn("GFX.S[p]", result)
        self.assertIn("native_frame_proven=0", result)
        self.assertIn("source_callback_proven=0", result)
        self.assertIn("f>=4028 && f<=4036", result)
        self.assertIn("f>=4172 && f<=4180", result)
        self.assertNotIn("Memory.VRAM[", result)
        self.assertNotIn("S9xSetByte(", result)
        self.assertEqual(result.count("DrawBackdrop();"), 1)
        self.assertEqual(result.count(probe.OBJ), 1)

    def test_fail_closed_on_unpinned_or_duplicate_stages(self):
        valid = probe.patch_source(SOURCE)
        cases = ("", valid, SOURCE.replace(probe.REQUIRES, ""),
                 SOURCE.replace(probe.OBJ, ""),
                 SOURCE.replace(probe.OBJ, probe.OBJ + probe.OBJ),
                 SOURCE.replace(probe.MACRO, ""),
                 SOURCE.replace(probe.END, ""))
        for bad in cases:
            with self.subTest(bad=bad[:60]), self.assertRaises(ValueError):
                probe.patch_source(bad)

if __name__ == "__main__":
    unittest.main()
