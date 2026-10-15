"""Fail-closed source guard for disposable genuine countdown ch6+7 prime."""
import unittest

from tools import qa08_patch_channel67_prime_counterfactual as ch67
from tools import qa08_patch_channel57_prime_counterfactual as ch57
from tools import qa08_patch_channel7_only_prime_counterfactual as ch7
from tools import qa08_patch_hdma_prime_counterfactual as gl
from tests.unit.test_qa08_hdma_prime_counterfactual import fixture_source


class Channel67PrimeSourceTests(unittest.TestCase):
    def test_source_matches_actual_channel6_window_mode4_and_channel7_brightness(self):
        before = fixture_source()
        after = ch67.patch_source(before)
        self.assertEqual(after.count(ch67.MARK), 1)
        self.assertIn("i == 6 && (ch->mode & 7) == 4", after)
        self.assertIn("ch->bAdr == 0x26 && ch->aBank == 0x15", after)
        self.assertIn("i == 7 && (ch->mode & 7) == 0", after)
        self.assertIn("ch->bAdr == 0x00", after)
        self.assertIn("*ch = save;", after)
        self.assertEqual(after.count("DmaChannel save = *ch;"), 1)
        self.assertEqual(after.count("dma_transferByte(dma, ch->tableAdr++"), 1)
        self.assertNotIn(ch57.MARK, after)

    def test_refuses_already_modified_or_mismatched_source(self):
        source = fixture_source()
        for candidate in (
            gl.patch_source(source),
            ch7.patch_source(source),
            ch57.patch_source(source),
            ch67.patch_source(source),
            source.replace("hdma_pin_oam_address(dma, ch);", "return;", 1),
        ):
            with self.subTest(sample=candidate[:90]):
                with self.assertRaises(ValueError):
                    ch67.patch_source(candidate)

    def test_synthetic_patch_does_not_certify_native_source_or_shipping(self):
        self.assertIn("source test ONLY", ch67.SELECTIVE)
        self.assertIn("all OTHER channels", ch67.SELECTIVE)


if __name__ == "__main__":
    unittest.main()
