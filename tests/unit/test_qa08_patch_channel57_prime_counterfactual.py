"""Reject premature promotion and source drift in the selective 5+7 HDMA experiment."""
import unittest

from tests.unit.test_qa08_hdma_prime_counterfactual import fixture_source
from tools import qa08_patch_channel57_prime_counterfactual as combined
from tools import qa08_patch_hdma_prime_counterfactual as global_prime
from tools import qa08_patch_channel7_only_prime_counterfactual as channel7


class Channel57PrimePatchTests(unittest.TestCase):
    def test_only_two_actual_source_modes_consume(self):
        source = fixture_source()
        updated = combined.patch_source(source)
        self.assertEqual(updated.count(combined.MARK), 1)
        self.assertIn("i == 7 && (ch->mode & 7) == 0", updated)
        self.assertIn("ch->bAdr == 0x00", updated)
        self.assertIn("i == 5 && (ch->mode & 7) == 1", updated)
        self.assertIn("ch->bAdr == 0x31", updated)
        self.assertIn("*ch = save;", updated)
        self.assertIn("ch->repCount--;", updated)
        self.assertEqual(updated.count("dma_transferByte(dma, ch->tableAdr++"), 1)
        self.assertEqual(updated.count("void dma_doHdma(Dma* dma)"), 1)
        self.assertNotIn(channel7.MARK, updated)
        self.assertNotIn(global_prime.MARK, updated)

    def test_refuses_unpinned_or_doubly_patched_source(self):
        source = fixture_source()
        for candidate in (
            combined.patch_source(source),
            global_prime.patch_source(source),
            channel7.patch_source(source),
            source.replace("hdma_pin_oam_address(dma, ch);", "return;", 1),
        ):
            with self.subTest(source=candidate[:60]):
                with self.assertRaises(ValueError):
                    combined.patch_source(candidate)

    def test_synthetic_patch_never_certifies_original_or_ships(self):
        self.assertIn("never release", combined.SELECTIVE)
        self.assertIn("Other channels retain", combined.SELECTIVE)
        self.assertIn("production_change=false", __import__("inspect").getsource(combined.main))


if __name__ == "__main__":
    unittest.main()
