"""Strict fail-closed original PPU $2100 diagnostic source-identity tests."""
import unittest
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools import qa08_current_blackout_readonly_patch as p
from tools import qa08_current_blackout_source_witness as v

class TestBlackoutTrace(unittest.TestCase):
    def test_port_anchor_and_idempotence(self):
        s="#include <stdio.h>\n#include <stdlib.h>\n"+p.PORT_ANCHOR
        out=p.patch_port(s)
        self.assertEqual(out,p.patch_port(out))
        self.assertIn("g_ppu_wlog_src",out)
        for broken in (s.replace(p.PORT_ANCHOR,""),out.replace(p.PORT_MARK,"WRONG"),
                       out.replace("frame=%d", "frame=%x"),s+s):
            with self.subTest(broken=broken[:40]),self.assertRaises(ValueError):
                p.patch_port(broken)
    def test_renderer_state_anchor_and_idempotence(self):
        s=p.RASTER_HEADER+p.RASTER_ANCHOR+p.PIXEL_ANCHOR
        out=p.patch_raster(s)
        self.assertEqual(out,p.patch_raster(out))
        self.assertIn("PPU_forcedBlank(ppu)",out)
        self.assertIn("pixelBuffer[2]",out)
        for broken in (out.replace(p.PIXEL_MARK,"WRONG"),
                       out.replace(p.RASTER_MARK,"WRONG"),
                       s.replace(p.RASTER_ANCHOR,""),s+s):
            with self.subTest(broken=broken[:40]),self.assertRaises(ValueError):
                p.patch_raster(broken)
    def test_bad_guest_never_gets_register_credit(self):
        with self.assertRaisesRegex(ValueError,"5484"):
            v.inspect("",[])
        with self.assertRaisesRegex(ValueError,"epoch"):
            v.inspect("",["0xdeadbeef"]*5484)
if __name__=="__main__":unittest.main()
