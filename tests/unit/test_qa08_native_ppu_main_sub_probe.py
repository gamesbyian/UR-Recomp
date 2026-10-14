"""Adversarial source-probe and strict native PPU pixel parser unit tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import qa08_patch_ppu_pixel_compose_probe as patcher
from tools import check_qa08_native_main_sub_pixel_probe as checker


def log_line(y, *, frame=2208, final="9C3131", sub=None, math=1,
             present=1, fixed=None, sub15=None):
    if sub is None:
        sub = "A6B3" if y == 50 else "A4C3"
    if fixed is None:
        fixed = "000F" if y == 50 else "0260"
    if sub15 is None:
        sub15 = "18C6" if present else "0000"
    return (f"UR_QA08_NATIVE_PPU_PIXEL frame={frame} x=133 y={y} "
            f"main=F21B sub={sub} main15=000D sub15={sub15} "
            f"final={final} cgadsub=04 cgwsel=02 fixed15={fixed} "
            f"math={math} rendered_sub=1 sub_present={present} clip_main=1")


class NativePixelProbeTests(unittest.TestCase):
    def test_source_instrumentation_only_one_exact_pinned_compositor(self):
        original = ("static NOINLINE void PpuDrawWholeLine(Ppu *ppu, uint y) {\n"
                    + patcher.ANCHOR + "}\n")
        changed = patcher.patch_source(original)
        self.assertIn("UR_QA08_NATIVE_PPU_PIXEL", changed)
        self.assertIn("main15=%04X sub15=%04X", changed)
        self.assertIn("ppu->bgBuffers[1].data[i]", changed)
        self.assertEqual(changed.count(patcher.ANCHOR), 1)
        with self.assertRaisesRegex(ValueError, "already applied"):
            patcher.patch_source(changed)

    def test_upstream_ppu_code_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, "compositor source"):
            patcher.patch_source("static NOINLINE void PpuDrawWholeLine() {}\n")

    def test_two_synthetic_samples_require_exact_native_rgb_and_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"ppu.log"
            raw=bytearray(342*224*4)
            for y in (50,162):
                idx=4*(342*y+133)
                raw[idx:idx+4]=bytes((156,49,49,255))
            p.write_text(log_line(50)+"\n"+log_line(162)+"\n")
            result=checker.read_samples(p,bytes(raw))
            self.assertEqual(len(result),2)
            self.assertEqual(result[(133,50)]["main_layer"],2)
            self.assertEqual(result[(133,50)]["sub_layer"],6)
            self.assertEqual(result[(133,162)]["sub_layer"],4)
            self.assertEqual(result[(133,50)]["live_fixed_RGB15"],"0x000F")
            self.assertEqual(result[(133,162)]["live_fixed_RGB15"],"0x0260")
            self.assertEqual(result[(133,50)]["native_composed_RGB5"],[19,6,6])
            self.assertTrue(result[(133,50)]["math_eligible_at_window_and_layer"])
            p.write_text(log_line(50,frame=2207)+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "frame"):
                checker.read_samples(p,bytes(raw))
            p.write_text(log_line(50,final="010000")+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "RGB disagrees"):
                checker.read_samples(p,raw)
            p.write_text(log_line(50,sub="0400")+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "registers"):
                checker.read_samples(p,raw)

            # The exact original after-removal PPU uses no subscreen colour
            # and adds the live per-line *fixed* operand instead.
            empty_sub = ("0500")
            raw_top=4*(342*50+133)
            raw_bottom=4*(342*162+133)
            raw[raw_top:raw_top+4]=bytes((231,0,0,255))
            raw[raw_bottom:raw_bottom+4]=bytes((107,156,0,255))
            p.write_text(log_line(50,final="E70000",sub=empty_sub,present=0)+
                         "\n"+log_line(162,final="6B9C00",sub=empty_sub,present=0)+"\n")
            absent=checker.read_samples(p,bytes(raw))
            self.assertEqual(absent[(133,50)]["native_composed_RGB5"],[28,0,0])
            self.assertEqual(absent[(133,162)]["native_composed_RGB5"],[13,19,0])
            self.assertEqual(absent[(133,50)]["sub_operand"],"per-line-fixed-colour")
            p.write_text(log_line(50, fixed="0260")+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError,"field registers"):
                checker.read_samples(p,bytes(raw))
            # Restore the stock synthetic raster after the two deliberately
            # different after-removal output colours before testing duplicate
            # log lines, otherwise the SHA/RGB guard correctly rejects first.
            raw[raw_top:raw_top+4]=bytes((156,49,49,255))
            raw[raw_bottom:raw_bottom+4]=bytes((156,49,49,255))
            p.write_text(log_line(50)+"\n"+log_line(50)+"\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                checker.read_samples(p,raw)

    def test_original_P7_hash_still_required(self):
        raw=bytes(342*224*4)
        digest=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"original.pam"
            p.write_bytes(checker.PAM+raw)
            self.assertEqual(checker.load_pam(p,digest),raw)
            with self.assertRaisesRegex(ValueError,"SHA differs"):
                checker.load_pam(p,"0"*64)
            p.write_bytes(checker.PAM+raw[:-1])
            with self.assertRaisesRegex(ValueError,"not an exact"):
                checker.load_pam(p,digest)


if __name__=="__main__":
    unittest.main()
