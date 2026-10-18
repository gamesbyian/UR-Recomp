"""Fail-closed pure checks for bounded late current-epoch CGRAM observer."""
import unittest
from tools import qa08_current_late_cgram_port_patch as p
from tools import qa08_current_late_cgram_witness as w

class LiveLateCgramTests(unittest.TestCase):
    def test_port_observer_is_exactly_additive(self):
        raw=("#include <stdio.h>\n#include <stdlib.h>\n"+p.ANCHOR+
             "case 0x21: break;\ncase 0x22: break;\n")
        x=p.patch_source(raw)
        self.assertEqual(p.patch_source(x),x)
        self.assertEqual(x.count(p.MARK),1)
        self.assertIn("5152 && snes_frame_counter <= 5195",x)
        for bad in (raw.replace("case 0x21:",""),x.replace("src=%u","src=bad"),
                    x+p.TRACE,raw+raw):
            with self.subTest(bad=bad[:32]),self.assertRaises(ValueError):
                p.patch_source(bad)
    @staticmethod
    def sample():
        result=[]
        for frame in (5155,5162,5169,5176,5183,5190):
            for idx in range(4):
                for port,val in ((0x21,0x6c+idx),(0x22,idx),(0x22,0x42)):
                    result.append(f"{w.TAG}frame={frame} v=230 h=100 adr={port:02x} "
                                  f"val={val:02x} src=0 ptr={0x6c+idx:02x} second=0")
        return result
    def test_bounded_real_port_shape(self):
        report=w.parse("\n".join(self.sample()))
        self.assertEqual(report["actual_native_writer_frame_sequence"],
                         [5155,5162,5169,5176,5183,5190])
        self.assertEqual(report["genuine_CPU_input_CGRAM_port_events"],72)
        self.assertEqual(report["palette_6c_to_6f_by_frame"][0]
                         ["colour_words_6c_to_6f_RGB15"],["4200","4201","4202","4203"])
        self.assertFalse(report["guest_or_palette_renderer_fix_authorized"])
    def test_negative_missing_duplicate_wrong_source_order(self):
        lines=self.sample()
        for bad in (
            lines[:-1],
            lines+[lines[-1]],
            [x.replace("src=0","src=1") if i==0 else x for i,x in enumerate(lines)],
            [x.replace("adr=21","adr=20") if i==0 else x for i,x in enumerate(lines)],
            [x.replace("frame=5155","frame=5156") if i==0 else x for i,x in enumerate(lines)],
            [x.replace("val=6c","val=6f") if i==0 else x for i,x in enumerate(lines)]
        ):
            with self.subTest(last=bad[-1]),self.assertRaises(ValueError):
                w.parse("\n".join(bad))
    def test_guest_route_not_waived(self):
        with self.assertRaisesRegex(ValueError,"5484"):
            w.verify("\n".join(self.sample()),[])
        with self.assertRaisesRegex(ValueError,"RF017"):
            w.verify("\n".join(self.sample()),["0xdeadbeef"]*5484)
if __name__=="__main__":unittest.main()
