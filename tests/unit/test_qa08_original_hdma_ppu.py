"""Read-only original source PPU HDMA channel5 strict contract; ROM-free adversarial tests."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import instrument_snesref_qa08_original_hdma_ppu as patch
from tools import check_qa08_original_hdma_ppu as witness

LAYOUT = (Path(__file__).resolve().parents[2] / "analysis" / "data" /
          "qa08-original-2p-channel5-executed-opcode-table-layout.json")


def inputs():
    layout = json.loads(LAYOUT.read_text(encoding="utf8"))
    receipt = {
        "USA_ROM_SHA256": witness.ROM,
        "original_script_SHA256": witness.SCRIPT,
        "original_t480_WRAM_SHA256": witness.WRAM,
        "source_65816_writer_PCs": 18,
        "second_camera_0DDB": 1, "in_race_0313": 1,
        "native_same_input_frame_parity_proven": False,
    }
    return layout, receipt


def observed(frame=1782, beam=4):
    # Synthetic source-level report. It does not claim that the original
    # game actually produces these events; only the genuine workflow can.
    records = []
    for i, (addr, val, fixed) in enumerate(
            [(0x2085,"04","0260"), (0x2086,"2F","026F"),
             (0x2088,"04","026F"), (0x2089,"40","000F"),
             (0x208B,"04","000F"), (0x208C,"80","000F"),
             (0x208E,"04","000F"), (0x208F,"20","0000"),
             (0x2091,"04","0000"), (0x2092,"53","0260"),
             (0x2094,"04","0260"), (0x2095,"80","0260")]):
        bbus = "31" if i%2==0 else "32"
        records.append(
            f"UR_QA08_ORIGINAL_HDMA_PPU frame={frame} v={beam+i//2} "
            f"cycles={100+i} channel=5 mode=1 indirect=0 bbus={bbus} "
            f"base=31 source=7E:{addr:04X} original_wram={val} "
            f"byte={val} cgadsub=04 cgwsel=02 fixed15={fixed}")
    return records


def evaluate(lines, *, adjust=None):
    layout, receipt = inputs()
    if adjust is not None:
        adjust(layout,receipt)
    with tempfile.TemporaryDirectory() as d:
        log=Path(d)/"source.log"
        log.write_text("\n".join(lines)+"\n",encoding="utf8")
        return witness.check(log, receipt, layout)


class OriginalPpuHdmatraceTests(unittest.TestCase):
    def test_source_patch_on_original_core_is_guarded_and_read_only(self):
        stock = (
            '#include "dma.h"\n'
            +patch.FUNCTION+'\n'
            ' if (CPU.InDMAorHDMA) { }\n'
            ' if (Byte & 0x80) {}\n'
            ' PPU.FixedColourRed   = Byte & 0x1f;\n'
            +patch.CASE31+"\n"+patch.CASE32+"\n}\n")
        generated=patch.patch_source(stock)
        self.assertIn("CPU.InHDMA",generated)
        self.assertIn("CPU.CurrentDMAorHDMAChannel != 5", generated)
        self.assertIn("UR_QA08_ORIGINAL_HDMA_PPU_WINDOW",generated)
        self.assertIn('strcmp(arm, "source-go-t480")',generated)
        self.assertIn("PPU.FixedColourBlue << 10",generated)
        self.assertIn("frame >= 1988u && frame <= 1990u",generated)
        self.assertIn("qa08_original_hdma_live_ppu(Byte, 0x2131)",generated)
        self.assertIn("qa08_original_hdma_live_ppu(Byte, 0x2132)",generated)
        with self.assertRaisesRegex(ValueError,"already applied"):
            patch.patch_source(generated)
        with self.assertRaisesRegex(ValueError,"source changed"):
            patch.patch_source(stock.replace("case 0x2132: // COLDATA","case 0x2132: // DELETED"))

    def test_admitted_synthetic_source_event_contract(self):
        report=evaluate(observed())
        self.assertEqual(report["actual_original_PPU_2131_2132_writes"],12)
        self.assertEqual(report["actual_original_channel5_register_pairs"],6)
        self.assertEqual(report["source_expected_byte_matches"],12)
        self.assertEqual(report["actual_WRAM_PPU_byte_matches"],12)
        self.assertEqual(report["actual_mode1_pairs"][0]["source_first"],"7E:2085")
        self.assertFalse(report["real_original_native_identical_frame_input_PPU_parity"])
        self.assertFalse(report["actual_original_Snes9x_finished_PPU_RGB_pixels_sampled"])

    def test_unexpected_source_byte_remains_observed_deviation(self):
        lines=observed()
        lines[1]=lines[1].replace("byte=2F","byte=2E")
        report=evaluate(lines)
        self.assertEqual(report["source_expected_byte_matches"],11)
        self.assertEqual(report["actual_WRAM_PPU_byte_matches"],11)
        self.assertFalse(report["actual_mode1_pairs"][0]["source_matches_original_executed_table"])

    def test_forged_register_order_address_mode_or_beam_fails(self):
        cases=[("channel=5","channel=4"),("mode=1","mode=0"),
               ("indirect=0","indirect=1"),("bbus=31","bbus=33"),
               ("base=31","base=32"),("source=7E:2085","source=7E:2084"),
               ("v=4","v=262"),("frame=1782","frame=1784"),
               ("cgadsub=04","cgadsub=05")]
        for old,new in cases:
            with self.subTest(bad=old):
                lines=observed()
                lines[0]=lines[0].replace(old,new)
                with self.assertRaises(ValueError):
                    evaluate(lines)
        ls=observed()
        ls[0],ls[1]=ls[1],ls[0]
        with self.assertRaises(ValueError):
            evaluate(ls)
        with self.assertRaises(ValueError):
            evaluate(observed()[:-1])
        with self.assertRaisesRegex(ValueError,"overflow"):
            evaluate(observed()+[
                "UR_QA08_ORIGINAL_HDMA_PPU_OVERFLOW frame=1782 max=128"])

    def test_unequal_2p_script_rom_and_false_parity_rejected(self):
        for key, value in (("USA_ROM_SHA256","0"*64),
                           ("original_script_SHA256","0"*64),
                           ("native_same_input_frame_parity_proven",True)):
            with self.subTest(key=key):
                def change(layout, receipt):
                    receipt[key]=value
                with self.assertRaisesRegex(ValueError,"receipt"):
                    evaluate(observed(),adjust=change)

if __name__=="__main__":
    unittest.main()
