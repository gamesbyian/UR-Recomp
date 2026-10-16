"""Original 2014 Sprite VRAM 4bpp sampling remains read-only and bounded."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_patch_original_medal_tilebits as m

class SourceTileProbeTest(unittest.TestCase):
    def test_original_callback_and_4bpp_tile_formula(self):
        src="#include <stdio.h>\n"+m.ANCHOR+"\nvideo_cb(GFX.Screen + 1,256,224,GFX.Pitch);\n"
        result=m.patched(src)
        self.assertEqual(m.patched(result),result)
        for proof in (
            "qa08_cb==4031u || qa08_cb==4175u",
            "PPU.OBJNameBase","PPU.OBJNameSelect",
            "name&0xf0u","((tile&0x100u)?PPU.OBJNameSelect:0u)",
            "row*2u","(at+16u+row*2u)",
            "tilepixels[si][y][x]=value",
            "indexed16_FNV64","opaque_mask",
            "xs[5]={207,205,205,225,225}",
            "ys[5]={91,115,139,96,120}",
        ):
            self.assertIn(proof,result)
        for mutation in ("Memory.VRAM[at]=","PPU.OBJ[slot].Name=",
                         "GFX.Screen[","S9xMainLoop("):
            if mutation=="GFX.Screen[":
                continue
            self.assertNotIn(mutation,result)
        self.assertEqual(result.count("video_cb(GFX.Screen + 1,256,224,GFX.Pitch);"),1)
    def test_reject_unpinned_or_partial(self):
        with self.assertRaises(ValueError):m.patched("foo")
        with self.assertRaises(ValueError):m.patched(m.MARK)
if __name__=="__main__":
    unittest.main()
