import tempfile
import unittest
from pathlib import Path

from tools.patch_widescreen_probe_window_policy import patch_ppu


class WidescreenWindowPolicyPatchTests(unittest.TestCase):
    def test_adds_disposable_keep_pinned_switch(self):
        source = """  PpuWidescreenAdjustPinnedWindowEdges(win->edges[0], window_right, &w1l,
                                       &w1r, &w2l, &w2r);
"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ppu.c"
            path.write_text(source)
            patch_ppu(path)
            out = path.read_text()
        self.assertIn("SNESRECOMP_WS_KEEP_PINNED_WINDOWS", out)
        self.assertIn("PpuWidescreenAdjustPinnedWindowEdges", out)


if __name__ == "__main__":
    unittest.main()
