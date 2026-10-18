"""Validate source-pinned, strictly read-only current result owner hooks."""
import unittest
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools import qa08_current_result_pixel_owner_patch as p
from tools import qa08_current_result_cgram_port_patch as c
from tools import qa08_current_result_source_witness as w

class TestCurrentResultReadOnly(unittest.TestCase):
    def test_pixel_anchors_fail_closed_and_idempotent(self):
        source=("#include <stdbool.h>\n"+p.INTRO+
                p.MAIN+p.WINDOW+p.MATH_END+p.SUB+p.END)
        patched=p.patch_source(source)
        self.assertEqual(p.patch_source(patched),patched)
        self.assertIn("snes_frame_counter == 4048",patched)
        self.assertIn("UR_QA08_WIN_OAM_LINE",patched)
        self.assertNotIn("brightness_pixel_lut",patched)
        for bad in (source.replace(p.MAIN,""),patched.replace("mainLayer =","newLayer ="),
                    patched.replace(p.MARK,"UNEXPECTED"),source+source):
            with self.subTest(bad=bad[:35]),self.assertRaises(ValueError):
                p.patch_source(bad)
    def test_cgram_genuine_port_scope_and_idempotence(self):
        raw='#include <stdio.h>\n#include <stdlib.h>\n'+c.ANCHOR+'case 0x21: ;\ncase 0x22: ;\n'
        done=c.patch_source(raw)
        self.assertEqual(c.patch_source(done),done)
        self.assertIn("4024 && snes_frame_counter <= 4184",done)
        self.assertIn("UR_QA08_WIN_CURRENT_CGRAM_WRITE",done)
        with self.assertRaises(ValueError):
            c.patch_source(done.replace("src=%u", "src=999"))
    def test_inspection_rejects_empty_and_wrong_guest(self):
        with self.assertRaisesRegex(ValueError,"5484"):
            w.inspect("",[])
        with self.assertRaisesRegex(ValueError,"RF-017 / route changed"):
            w.inspect("",["0xdeadbeef"]*5484)
if __name__=="__main__":unittest.main()
