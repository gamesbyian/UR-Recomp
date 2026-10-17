"""Pinned libretro callback raster-source observer is read-only and bounded."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_patch_original_finish_layer_callback as probe


class Snes9xSourcePatchTest(unittest.TestCase):
    def test_real_original_core_callback_identity_and_no_pixel_mutations(self):
        src=("#include <stdio.h>\n"+"bool8 S9xDeinitUpdate(int width, int height)\n{\n    static int burst_phase = 0;\n"+'video_cb(GFX.Screen + 1, width, height, GFX.Pitch);\n')
        patched=probe.patch_source(src)
        self.assertEqual(patched,probe.patch_source(patched))
        self.assertIn("qa08_actual_callback == 3791u || qa08_actual_callback == 3871u",patched)
        self.assertIn("GFX.ZBuffer[z_at]",patched)
        self.assertIn("GFX.SubZBuffer[z_at]",patched)
        self.assertIn("GFX.Screen[screen_at]",patched)
        self.assertIn("CGRAM_1B=%04x CGRAM_C6=%04x",patched)
        self.assertIn("GFX.PPL",patched)
        self.assertIn("static int burst_phase = 0;",patched)
        self.assertEqual(patched.count("video_cb(GFX.Screen + 1, width, height, GFX.Pitch);"),1)
        for forbidden in ("GFX.Screen[screen_at] =","GFX.ZBuffer[z_at] =",
                          "PPU.CGDATA[0x1b] =","ICPU.Frame ="):
            self.assertNotIn(forbidden,patched)

    def test_reject_tampered_or_drifted_source(self):
        with self.assertRaises(ValueError):
            probe.patch_source("unrelated renderer")
        with self.assertRaises(ValueError):
            probe.patch_source(probe.MARK)
        with self.assertRaises(ValueError):
            probe.patch_source(probe.INTRO*2+"#include <stdio.h>\nvideo_cb(GFX.Screen + 1);")


if __name__=="__main__":
    unittest.main()
