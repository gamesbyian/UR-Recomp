"""Snes9x genuine original PPU tile-call source probe boundaries.

The original is captured at the source paint function, not a guessed
sprite/VRAM decoder; no changes to actual guest or RGB frame rendering.
"""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_instrument_original_snes9x_medal_tile_calls as src

SOURCE=("\n".join((src.HEADER,
                  "GFX.DB = GFX.ZBuffer;",
                  "DrawOBJS(D + 4);",
                  "for (uint32 Y = GFX.StartY, Offset = Y * GFX.PPL;",
                  src.METHOD,
                  src.DRAW,
                  src.CLIPPED))+"\n")

class PinnedOriginalTileProbe(unittest.TestCase):
    def test_patches_only_two_actual_sprite_painter_call_sites(self):
        patched=src.patch_source(SOURCE)
        self.assertIn(src.MARK,patched)
        self.assertIn("ICPU.Frame",patched)
        self.assertEqual(patched.count("DrawTile(source_tile,O,TileLine,1);"),1)
        self.assertEqual(patched.count(
            "DrawClippedTile(source_tile,O,x-X,w,TileLine,1);"),1)
        self.assertIn("GFX.DB[y*GFX.PPL+x]",patched)
        self.assertIn("GFX.S[y*GFX.PPL+x]",patched)
        self.assertIn('"original_guest_phase_proven=0',patched)
        self.assertNotIn("Memory.VRAM[",patched)
        self.assertNotIn("S9xSetByte",patched)

    def test_rejects_stale_or_repeated_core_anchors(self):
        good=src.patch_source(SOURCE)
        for bad in (
            "",
            good,
            SOURCE.replace(src.CLIPPED,""),
            SOURCE.replace(src.DRAW,src.DRAW+src.DRAW),
            SOURCE.replace("GFX.DB = GFX.ZBuffer;", "GFX.DB = GFX.SubZBuffer;"),
            SOURCE.replace("DrawOBJS(D + 4);","DrawOBJS(D + 5);"),
        ):
            with self.subTest(before=bad[:40]),self.assertRaises(ValueError):
                src.patch_source(bad)

    def test_original_frame_neighborhoods_only_no_native_equivalence(self):
        patched=src.patch_source(SOURCE)
        self.assertIn("f>=4028 && f<=4036",patched)
        self.assertIn("f>=4172 && f<=4180",patched)
        self.assertIn("depth<32",patched)
        self.assertIn("q.armed[i]",patched)
        self.assertIn("original_guest_phase_proven=0",patched)

if __name__=="__main__":
    unittest.main()
