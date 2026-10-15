"""ROM-free read-only source-all-channel HDMA observer anchoring and limits."""
import unittest

from tools.qa08_patch_hdma_all_channels_source import (
    patch_source, MARK, INSERT,
)
from tools.qa08_patch_hdma_coldata_source import patch_source as existing
from tests.unit.test_qa08_patch_hdma_coldata_source import source_fixture


class AllChannelNativeHdmaSourceTests(unittest.TestCase):
    def test_preserves_actual_BBUS_and_existing_colour_observer(self):
        source = existing(source_fixture())
        patched = patch_source(source)
        self.assertIn(MARK, patched)
        self.assertEqual(patched.count("snes_writeBBus(dma->snes, bAdr, val);"), 1)
        self.assertEqual(patched.count("UR_QA08_HDMA_COLDATA frame="), 1)
        self.assertEqual(patched.count("UR_QA08_HDMA_CGADSUB frame="), 1)
        self.assertEqual(patched.count("UR_QA08_HDMA_INIDISP frame="), 1)
        self.assertIn("g_ppu_wlog_src == kPpuWlogHdma", patched)
        self.assertIn("ppu_wlog_position(&qa08_tagframe, &qa08_line)", patched)
        self.assertIn("src=%02X:%04X", patched)
        self.assertIn("qa08_ch->tableAdr", patched)
        self.assertIn("UR_QA08_HDMA_ALL_OVERFLOW", patched)
        self.assertIn("16384u", patched)
        self.assertEqual(patched.count("void dma_doHdma(Dma* dma)"), 1)

    def test_uninstrumented_or_duplicate_or_changed_source_rejected(self):
        src = existing(source_fixture())
        for changed in (
            source_fixture(),
            patch_source(src),
            src.replace("    snes_writeBBus(dma->snes, bAdr, val);", ""),
            src.replace("    /* UR_QA08_HDMA_COLDATA. Observe only", "    /* wrong. Observe only"),
        ):
            with self.subTest(source=changed[:80]):
                with self.assertRaises(ValueError):
                    patch_source(changed)

    def test_real_pinned_sdd1_fastpath_is_not_the_normal_transfer_anchor(self):
        # The real framework performs a separate SDD1 snes_writeBBus
        # before returning; this does not change the unique normal anchor.
        fixture = existing(source_fixture())
        sdd1 = (
            "static void sdd1_transfer(Dma *dma, uint8_t bAdr, uint8_t val) {\\n"
            "    snes_writeBBus(dma->snes, bAdr, val);\\n"
            "}\\n"
        )
        fixture = fixture.replace("void dma_doHdma(Dma* dma) {}",
                                  sdd1 + "void dma_doHdma(Dma* dma) {}", 1)
        self.assertEqual(fixture.count("snes_writeBBus(dma->snes, bAdr, val);"), 2)
        patched = patch_source(fixture)
        self.assertEqual(patched.count("snes_writeBBus(dma->snes, bAdr, val);"), 2)
        self.assertIn("UR_QA08_HDMA_ALL frame=", patched)

    def test_read_only_block_does_not_write_live_DMA_or_PPU_state(self):
        for line in INSERT.splitlines():
            self.assertNotIn("snes_writeBBus(", line.strip().replace(
                "snes_writeBBus(dma->snes, bAdr, val);",
                ""))  # existing real transfer is preserved exactly once
        self.assertNotIn("dma_hdmaLoadDescriptor", INSERT)
        # A const pointer declaration is not a write to channel state.
        self.assertNotRegex(INSERT, r"(?m)^\s*\*qa08_ch\s*=")
        self.assertNotRegex(INSERT, r"\bqa08_ch->(?:tableAdr|repCount|doTransfer|aBank|size)\s*=")
        self.assertNotIn("dma_transferByte(", INSERT)


if __name__ == "__main__":
    unittest.main()
