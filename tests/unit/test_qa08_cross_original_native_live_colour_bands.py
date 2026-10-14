"""Adversarial independent-original/native channel5 live-register band checks."""
import copy
import json
from pathlib import Path
import unittest
from tools import qa08_cross_original_native_live_colour_bands as subject

ROOT=Path(__file__).resolve().parents[2]/"analysis"/"data"
FILES=("qa08-original-snes9x-2p-hdma-live-pixel-source-handoff-20261014.json",
       "qa08-original-native-channel5-hdma-coldata-source-handoff.json",
       "qa08-2p-original-native-text26-obj-palette-fingerprint.json")

def inputs():
    return [json.loads((ROOT/p).read_text(encoding="utf8")) for p in FILES]


class IndependentOriginalNativeLiveColourTests(unittest.TestCase):
    def test_exact_original_two_emulator_source_bands(self):
        report=subject.check(*inputs())
        self.assertEqual(len(report["source_pairs"]),6)
        self.assertTrue(report["six_real_original_native_source_bytes_and_fixed_RGB15_match"])
        self.assertEqual([x["tag_difference_native_minus_original"] for x in report["source_pairs"]],[2]*6)
        self.assertEqual(report["native_upper_row50_fixed_RGB15"],"0x000F")
        self.assertEqual(report["native_lower_row162_fixed_RGB15"],"0x0260")
        self.assertFalse(report["original_native_final_pixels_equal_proven"])
        self.assertFalse(report["same_input_frame_counters_and_camera_verified"])

    def test_strict_sources_and_no_false_parity(self):
        for key,value in (("downloaded_zip_sha256","0"*64),
                          ("source_WRAM_equals_BBUS_writes",95),
                          ("real_original_Snes9x_live_register_writes",95),
                          ("six_pairs_each_sampled_cpu_frame",False)):
            with self.subTest(change=key):
                data=inputs();data[0][key]=value
                with self.assertRaisesRegex(ValueError,"provenance"):
                    subject.check(*data)
        data=inputs();data[1]["native_PPU_2P_guest_frame"]=2209
        with self.assertRaisesRegex(ValueError,"provenance"):
            subject.check(*data)

    def test_mutations_real_source_register_state_and_extra_priming_rejected(self):
        candidates=((0,"original_beam_v",3), (0,"original_WRAM_CGADSUB","7E:2084"),
                    (0,"COLDATA","2E"),(0,"fixed_RGB15_after_COLDATA","000F"))
        for index,key,value in candidates:
            with self.subTest(field=key):
                data=inputs();data[0]["register_pairs_each_frame"][index][key]=value
                with self.assertRaisesRegex(ValueError,"source, byte|bands"):
                    subject.check(*data)
        for key,value in (("native_write_log_tag",3),
                          ("A_bus_byte_address","7E:2085"),
                          ("COLDATA_value","0x2E"),
                          ("fixed_RGB15_after_write","0x000F")):
            with self.subTest(native=key):
                data=inputs();data[1]["native_writes"][1][key]=value
                with self.assertRaises(ValueError):
                    subject.check(*data)

    def test_true_pixel_register_gates_preserved(self):
        for key,value in (("upper_live_fixed_RGB15","0x0260"),
                          ("source_pairs_each_viewport",12),
                          ("stock_BG3_main_OBJ_subscreen_26_accepted",False)):
            with self.subTest(source=key):
                data=inputs();data[2][key]=value
                with self.assertRaises(ValueError):
                    subject.check(*data)
        data=inputs()
        data[1]["native_writes"][0]["fixed_RGB15_after_write"]="0x000F"
        with self.assertRaisesRegex(ValueError,"priming"):
            subject.check(*data)

if __name__=="__main__":
    unittest.main()
