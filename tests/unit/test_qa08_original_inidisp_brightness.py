"""True original source $2100 brightness-zero vs bit7 forced blank contract."""
import unittest
from tools import check_qa08_original_inidisp_brightness as check
from tools import instrument_snesref_qa08_original_hdma_ppu as patch

def receipt():
    return {
        "USA_ROM_SHA256":check.ROM,"original_script_SHA256":check.ROUTE,
        "original_t480_WRAM_SHA256":check.WRAM,
        "source_65816_writer_PCs":18,
        "actual_executed_original_instruction_count":55,
        "second_camera_0DDB":1,"in_race_0313":1,
        "native_same_input_frame_parity_proven":False,
    }

def logs():
    rows=[]
    for i,(v,val,bright) in enumerate(((111,"00",0),(113,"0F",15))):
        rows.append(
            f"UR_QA08_ORIGINAL_INIDISP frame=1989 v={v} cycles={120+i} "
            f"channel=3 mode=0 indirect=0 base=00 source=7E:207{i+1} "
            f"wram={val} bbus=00 value={val} brightness={bright} forced=0")
    return rows

def ppuw():
    return ("#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
            "1989\t111\t294\t2100\t00\thdma\n"
            "1989\t113\t293\t2100\t0F\thdma\n")

class OriginalInidispBrightnessTests(unittest.TestCase):
    def test_synthetic_original_brightness_observer_bounded(self):
        self.assertIn("UR_QA08_ORIGINAL_INIDISP",patch.PROBE)
        self.assertIn("PPU.Brightness",patch.PROBE)
        self.assertIn("PPU.ForcedBlanking",patch.PROBE)
        self.assertIn("qa08_original_inidisp_hdma(Byte);",patch.patch_source(
            '#include "dma.h"\n'+patch.FUNCTION+"\nif (CPU.InDMAorHDMA) {}\n"
            +"if (Byte & 0x80) {}\nPPU.FixedColourRed   = Byte & 0x1f;\n"
            +patch.CASE00+patch.CASE31+patch.CASE32+"\n}\n"))

    def test_original_zero_brightness_has_no_forced_bit7(self):
        result=check.check("\n".join(logs()),receipt(),ppuw())
        self.assertEqual(result["observed_original_GO_brightness_zero_tag"],111)
        self.assertEqual(result["observed_original_GO_brightness_15_restore_tag"],113)
        self.assertEqual(result["actual_original_GO_hdma_channel_at_zero"],3)
        self.assertFalse(result["source_hardware_forced_blank_bit_set_for_split"])
        self.assertTrue(result["source_real_brightness_set_zero_causes_black"])
        self.assertFalse(result["native_actual_INIDISP_transfer_and_PPU_pixel_mapping_proven"])

    def test_forged_channel_frame_brightness_flag_and_clock_rejected(self):
        for old,new in (
            ("frame=1989","frame=1987"),
            ("channel=3","channel=8"),
            ("brightness=0","brightness=15"),
            ("forced=0","forced=1"),
            ("mode=0","mode=8"),
            ("v=111","v=263"),
            ("bbus=00","bbus=31"),
        ):
            with self.subTest(field=old):
                records=logs();records[0]=records[0].replace(old,new)
                with self.assertRaises(ValueError):
                    check.check("\n".join(records),receipt(),ppuw())
        with self.assertRaisesRegex(ValueError,"chronology"):
            check.check("\n".join(reversed(logs())),receipt(),ppuw())

    def test_independent_original_PPUW_and_source_route_required(self):
        with self.assertRaisesRegex(ValueError,"independent PPUW"):
            check.check("\n".join(logs()),receipt(),ppuw().replace("294","293").replace("0F","0E"))
        bad=receipt();bad["original_script_SHA256"]="0"*64
        with self.assertRaisesRegex(ValueError,"oracle"):
            check.check("\n".join(logs()),bad,ppuw())
        with self.assertRaisesRegex(ValueError,"overflow"):
            check.check("UR_QA08_ORIGINAL_INIDISP_OVERFLOW frame=1989 max=256",receipt(),ppuw())

if __name__=="__main__":
    unittest.main()
