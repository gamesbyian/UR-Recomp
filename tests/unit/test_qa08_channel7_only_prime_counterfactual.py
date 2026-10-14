"""Experimental channel-7-only $2100 prime, fail-closed source anchors."""
import unittest

from tools import qa08_patch_channel7_only_prime_counterfactual as selective
from tools import qa08_patch_hdma_prime_counterfactual as global_prime
from tests.unit.test_qa08_hdma_prime_counterfactual import fixture_source


class Ch7OnlyPrimeCounterfactualTests(unittest.TestCase):
    def test_patch_preserves_other_channels_prior_state(self):
        original = fixture_source()
        changed = selective.patch_source(original)
        self.assertEqual(changed.count(selective.MARK), 1)
        self.assertIn("if (i == 7 && (ch->mode & 7) == 0 && !ch->indirect &&", changed)
        self.assertIn("ch->bAdr == 0x00)", changed)
        self.assertIn("      *ch = save;", changed)
        self.assertIn("      ch->repCount--;", changed)
        self.assertIn("      ch->doTransfer = (ch->repCount & 0x80) != 0;", changed)
        self.assertIn("      if ((ch->repCount & 0x7f) == 0)", changed)
        self.assertIn("        dma_hdmaLoadDescriptor(dma, ch);", changed)
        self.assertIn("void dma_doHdma(Dma* dma) {}", changed)
        self.assertEqual(changed.count("dma_transferByte(dma, ch->tableAdr++"), 1)
        self.assertEqual(changed.count("DmaChannel save = *ch;"), 1)
        self.assertFalse(selective.MARK in original)

    def test_refuse_double_patches_and_unpinned_code(self):
        original = fixture_source()
        changed = selective.patch_source(original)
        with self.assertRaisesRegex(ValueError, "already"):
            selective.patch_source(changed)
        globally = global_prime.patch_source(original)
        with self.assertRaisesRegex(ValueError, "already"):
            selective.patch_source(globally)
        for modified in (
            original.replace("DmaChannel save = *ch;", "DmaChannel save = {};", 1),
            original.replace("    *ch = save;", "    ch->repCount=0;", 1),
            original.replace("hdma_pin_oam_address(dma, ch);", "return;", 1),
            original.replace("dma_transferByte(dma, ch->tableAdr++, ch->aBank", "return"),
        ):
            with self.subTest(modified=modified[:90]):
                with self.assertRaises(ValueError):
                    selective.patch_source(modified)

    def test_no_real_pixels_or_other_title_authority_claimed(self):
        self.assertIn("never release code", selective.SELECTIVE)
        self.assertIn("Uniracers 2P brightness seam", selective.SELECTIVE)
        self.assertIn("all other channels", selective.SELECTIVE)


if __name__ == "__main__":
    unittest.main()
