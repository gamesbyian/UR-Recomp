"""Adversarial native $2100 INIDISP real HDMA writer acceptance tests."""
import json
from pathlib import Path
import unittest
from tools import check_qa08_native_split_inidisp_source as source
from tools import qa08_patch_hdma_coldata_source as patch

ROOT=Path(__file__).resolve().parents[2]/"analysis/data"
def references():
    return (
        json.loads((ROOT/"qa08-original-native-channel5-hdma-coldata-source-handoff.json").read_text()),
        json.loads((ROOT/"qa08-original-native-2p-split-seam-rgb5-pixel-parity-20261014.json").read_text())
    )

def mock_lines():
    # Placeholder unit contract, NOT observed original/native DMA timing!
    return [
        "UR_QA08_HDMA_INIDISP frame=2208 tagframe=2208 line=114 channel=3 "
        "bbus=00 value=00 src=7E:2081 mode=0 indirect=0 "
        "table=2082 bank=7E live_inidisp=00",
        "UR_QA08_HDMA_INIDISP frame=2208 tagframe=2208 line=116 channel=3 "
        "bbus=00 value=0F src=7E:2083 mode=0 indirect=0 "
        "table=2084 bank=7E live_inidisp=0F",
    ]

class NativeInidispSourceTests(unittest.TestCase):
    def test_source_patch_read_only_and_fail_closed(self):
        # Validate emitted probe against anchored pinned DMA source format.
        self.assertIn("UR_QA08_HDMA_INIDISP",patch.PATCH)
        self.assertIn("bAdr == 0x00",patch.PATCH)
        self.assertIn("dma->snes->ppu->inidisp",patch.PATCH)
        self.assertIn("g_ppu_wlog_src == kPpuWlogHdma",patch.PATCH)
        self.assertIn("snes_writeBBus(dma->snes, bAdr, val)",patch.PATCH)
        self.assertIn("qa08_inidisp_writes == 2048u",patch.PATCH)
        self.assertNotIn("dma->snes->ppu->inidisp = val",patch.PATCH)

    def test_synthetic_log_checker_does_not_assume_channel_or_split_line(self):
        native,seam=references()
        result=source.check("\n".join(mock_lines())+"\n",native,seam)
        self.assertEqual(result["actual_native_INIDISP_events"],2)
        self.assertEqual(result["first_native_forced_blank_tags"],[114])
        self.assertEqual(result["first_native_unblank_tags"],[116])
        self.assertFalse(result["native_render_row_vs_original_frame_phase_source_accepted"])

    def test_bad_guest_frame_register_channel_source_or_order_rejected(self):
        for old,new in (
            ("frame=2208","frame=2209"),
            ("tagframe=2208","tagframe=2209"),
            ("channel=3","channel=8"),
            ("bbus=00","bbus=31"),
            ("live_inidisp=00","live_inidisp=0F"),
            ("line=114","line=263"),
            ("mode=0","mode=8"),
            ("indirect=0","indirect=2"),
        ):
            with self.subTest(field=old):
                native,seam=references()
                rows=mock_lines()
                rows[0]=rows[0].replace(old,new)
                with self.assertRaises(ValueError):
                    source.check("\n".join(rows),native,seam)
        native,seam=references()
        with self.assertRaisesRegex(ValueError,"chronological"):
            source.check("\n".join(reversed(mock_lines())),native,seam)

    def test_untrusted_source_or_no_return_blanking_rejected(self):
        native,seam=references()
        native["native_PPU_2P_guest_frame"]=2209
        with self.assertRaisesRegex(ValueError,"not admitted"):
            source.check("\n".join(mock_lines()),native,seam)
        native,seam=references()
        seam["identical_pixels_after_channel_bit_depth_normalization"]=57344
        with self.assertRaisesRegex(ValueError,"not admitted"):
            source.check("\n".join(mock_lines()),native,seam)
        native,seam=references()
        with self.assertRaisesRegex(ValueError,"forced-blank"):
            source.check(mock_lines()[0]+"\n"+mock_lines()[0],native,seam)
        with self.assertRaisesRegex(ValueError,"limit"):
            source.check("UR_QA08_HDMA_INIDISP_OVERFLOW frame=2208 limit=2048",
                         native,seam)

if __name__=="__main__":
    unittest.main()
