"""Fail-closed QA08 current real native Snes9x math provenance checks."""
import copy,json,unittest
from pathlib import Path
from tools.check_qa08_current_finish_operands import verify,predict,brightness5
SOURCE=Path(__file__).resolve().parents[2]/"analysis/data/qa08-current-rf017-finish-real-native-pixel-operands-20261017.json"
class QA08CurrentSourceTest(unittest.TestCase):
    def test_real_native_eight_observed_samples(self):
        s=json.loads(SOURCE.read_text())
        self.assertEqual(verify(s)["samples"],8)
    def test_colour_brightness_quantization(self):
        self.assertEqual(brightness5(14,7),7)
        self.assertEqual(brightness5(13,7),6)
        self.assertEqual(brightness5(1,7),0)
        self.assertRaises(ValueError,brightness5,32,7)
    def test_reject_edited_legacy_PPU_operand_or_brightness(self):
        real=json.loads(SOURCE.read_text())
        for field,val in (("pre",[14,0,0]),("br",8),("main",4)):
            altered=copy.deepcopy(real)
            altered["arithmetic"]["samples"][6][field]=val
            with self.subTest(field=field),self.assertRaises(ValueError):
                verify(altered)
    def test_adjoining_correct_and_wrong_real_finish_controls(self):
        real=json.loads(SOURCE.read_text())
        by_x={r["x"]:r for r in real["arithmetic"]["samples"]
              if r["f"]==3680}
        for x in (92,96):
            self.assertNotEqual([v>>3 for v in by_x[x]["final"]],
                                by_x[x]["original"])
        for x in (93,97):
            self.assertEqual([v>>3 for v in by_x[x]["final"]],
                             by_x[x]["original"])
        # An adversary may not forge an all-exact finish source pair.
        altered=copy.deepcopy(real)
        altered["arithmetic"]["samples"][2]["original"] = [
            v>>3 for v in altered["arithmetic"]["samples"][2]["final"]]
        with self.assertRaisesRegex(ValueError,"hypothesis disproved"):
            verify(altered)
    def test_reject_forged_source_identity(self):
        x=json.loads(SOURCE.read_text())
        x["source"]["guest_crc_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            verify(x)
if __name__=="__main__":unittest.main()
