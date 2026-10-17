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
    def test_reject_forged_source_identity(self):
        x=json.loads(SOURCE.read_text())
        x["source"]["guest_crc_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            verify(x)
if __name__=="__main__":unittest.main()
