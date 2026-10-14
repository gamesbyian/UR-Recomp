"""Adversarial source-probe and strict native PPU pixel parser unit tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import qa08_patch_ppu_pixel_compose_probe as patcher
from tools import check_qa08_native_main_sub_pixel_probe as checker


def log_line(y, *, frame=2208, final="000000", sub="0401", math=1):
    return (f"UR_QA08_NATIVE_PPU_PIXEL frame={frame} x=133 y={y} "
            f"main=0201 sub={sub} main15=000D sub15=18C6 "
            f"final={final} cgadsub=04 cgwsel=02 fixed15=0260 "
            f"math={math} rendered_sub=1 sub_present=1 clip_main=1")


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
            raw=bytes(342*224*4)
            p.write_text(log_line(50)+"\n"+log_line(162)+"\n")
            result=checker.read_samples(p,raw)
            self.assertEqual(len(result),2)
            self.assertEqual(result[(133,50)]["main_layer"],2)
            self.assertEqual(result[(133,50)]["sub_layer"],4)
            self.assertTrue(result[(133,50)]["math_eligible_at_window_and_layer"])
            p.write_text(log_line(50,frame=2207)+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "frame"):
                checker.read_samples(p,raw)
            p.write_text(log_line(50,final="010000")+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "RGB disagrees"):
                checker.read_samples(p,raw)
            p.write_text(log_line(50,sub="0400")+"\n"+log_line(162)+"\n")
            with self.assertRaisesRegex(ValueError, "registers"):
                checker.read_samples(p,raw)
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
