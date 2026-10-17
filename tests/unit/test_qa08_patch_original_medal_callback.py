"""Fail-close original Snes9x two-frame medal live pixel and OAM observer."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_patch_original_medal_callback as x

class MedalSourceTest(unittest.TestCase):
    def test_only_original_callbacks_two_frames_five_pixels_seven_oam(self):
        raw="#include <stdio.h>\n"+x.ANCHOR+"\nvideo_cb(GFX.Screen + 1,256,224,GFX.Pitch);\n"
        revised=x.patch_source(raw)
        self.assertEqual(revised,x.patch_source(revised))
        for line in ("qa08_cb==4031u || qa08_cb==4175u",
                     "qa08_xs[5]={207,205,205,225,225}",
                     "qa08_ys[5]={91,115,139,96,120}",
                     "qa08_slots[7]={96,97,98,99,112,113,114}",
                     "GFX.Screen[si]","GFX.ZBuffer[zi]","GFX.SubZBuffer[zi]",
                     "PPU.OBJ[slot].Name"):
            self.assertIn(line,revised)
        self.assertEqual(revised.count("video_cb(GFX.Screen + 1,256,224,GFX.Pitch);"),1)
        for forbidden in ("GFX.Screen[si] =","PPU.OBJ[slot].Name =",
                          "GFX.ZBuffer[zi] =","ICPU.Frame ="):
            self.assertNotIn(forbidden,revised)
    def test_unknown_core_or_duplicate_mark_rejected(self):
        with self.assertRaises(ValueError):
            x.patch_source("unrelated graphics engine")
        with self.assertRaises(ValueError):
            x.patch_source(x.MARK)
        with self.assertRaises(ValueError):
            x.patch_source(x.ANCHOR*2+"#include <stdio.h>\nvideo_cb(GFX.Screen + 1);")
if __name__=="__main__":
    unittest.main()
