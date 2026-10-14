"""Synthetic source-contract tests for a disposable native HDMA byte probe."""
import tempfile
import unittest
from pathlib import Path

from tools import qa08_patch_hdma_coldata_source as tool


def source_fixture():
    return ('#include "ppu.h"\n'
            'static void dma_transferByte(Dma *dma, uint16_t addr, uint8_t bank, '
            'uint8_t dst, bool fromB, int channel);\n'
            'void dma_doHdma(Dma* dma) {}\n'
            'static void ordinary(Dma *dma, uint8_t bAdr, uint8_t val) {\n'
            + tool.ANCHOR + '\n}\n')


class OriginalNativeHdmaSourceTests(unittest.TestCase):
    def test_exact_one_normal_DMA_byte_path_patched_read_only(self):
        old=source_fixture()
        result=tool.patch_source(old)
        self.assertIn("UR_QA08_HDMA_COLDATA_FRAME",result)
        self.assertIn("bAdr == 0x32",result)
        self.assertIn("UR_QA08_HDMA_CGADSUB frame=",result)
        self.assertIn("bAdr == 0x31",result)
        self.assertIn("channel == 5",result)
        self.assertIn("dma->snes->ppu->cgadsub",result)
        self.assertIn("qa08_cgadsub_writes == 2048u",result)
        self.assertIn("kPpuWlogHdma",result)
        self.assertIn("aBank, aAdr",result)
        self.assertIn("dma->snes->ppu->fixedColor",result)
        self.assertIn("ppu_wlog_position(&tagged_frame, &tagged_line)",result)
        self.assertEqual(result.count("snes_writeBBus(dma->snes, bAdr, val)"),1)
        self.assertEqual(result.count("UR_QA08_HDMA_COLDATA frame="),1)
        self.assertIn("limit=2048",result)
        with self.assertRaisesRegex(ValueError,"already applied"):
            tool.patch_source(result)

    def test_missing_or_repeated_pinned_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError,"layout changed"):
            tool.patch_source("#include \"ppu.h\"\n"+tool.ANCHOR)
        with self.assertRaisesRegex(ValueError,"layout changed"):
            tool.patch_source(source_fixture()+tool.ANCHOR)

    def test_check_only_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            target=root/"runner/src/snes/dma.c"
            target.parent.mkdir(parents=True)
            target.write_text(source_fixture())
            self.assertEqual(tool.apply(root,True),target)
            self.assertEqual(target.read_text(),source_fixture())
            tool.apply(root,False)
            self.assertIn("UR_QA08_HDMA_COLDATA",target.read_text())
            with self.assertRaises(ValueError):
                tool.apply(root,False)


if __name__=="__main__":
    unittest.main()
