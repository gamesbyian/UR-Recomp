import tempfile
import unittest
from pathlib import Path

from tools.patch_widescreen_probe_composition_trace import patch_ppu


class CompositionTracePatchTests(unittest.TestCase):
    def test_injects_bounded_trace_before_scanout(self):
        source = """  uint32 *dst = (uint32*)&ppu->renderBuffer[(y - 1) * ppu->renderPitch], *dst_org = dst;
        int pixel = (bits >> 0) & 1 | (bits >> 7) & 2 |
                    (bits >> 14) & 4 | (bits >> 21) & 8;
        if (pixel == 0) continue;
"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ppu.c"
            path.write_text(source)
            patch_ppu(path)
            out = path.read_text()
        self.assertIn("SNESRECOMP_WS_EDGE_TRACE", out)
        self.assertIn("WS_EDGE frame=", out)
        self.assertIn("WS_OBJ_CAND frame=", out)
        self.assertLess(out.index("WS_EDGE frame="), out.index("uint32 *dst"))


if __name__ == "__main__":
    unittest.main()
