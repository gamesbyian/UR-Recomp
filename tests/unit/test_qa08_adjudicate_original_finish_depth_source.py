"""Fail-closed original 2014 Mode1 depth and Win32 pixel-owner decoder."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_adjudicate_original_finish_depth_source as q

GOOD={
    "callback":"3791","cpu_frame":"3791","total_emulated":"3792",
    "x":"121","y":"165","RGB565":"30c0","main_depth":"49","sub_depth":"44",
    "sub_RGB565":"00c0","bgmode":"1","brightness":"7","blank":"0",
    "TM":"17","TS":"10","CGWSEL":"02","CGADSUB":"04",
    "CGRAM_1B":"000d","CGRAM_C6":"04e1","width":"256","height":"224"
}


class OriginalSNES9xDepthTest(unittest.TestCase):
    def test_mode1_depth_is_source_decoded_not_native_layer_guessed(self):
        src=q.decode_mode1_depth(GOOD)
        self.assertEqual(src["main_layer"],"BG3")
        self.assertTrue(src["main_bg3_high_priority"])
        self.assertEqual(src["sub_layer"],"OBJ")
        self.assertEqual(src["sub_obj_priority"],2)
        self.assertEqual(src["native_registered_guest"],3792)
        two={**GOOD,"callback":"3871","cpu_frame":"3871","total_emulated":"3872"}
        self.assertEqual(q.decode_mode1_depth(two)["native_registered_guest"],3872)

    def test_drift_or_wrong_modes_source_coordinates_and_early_cgram_rejected(self):
        for key,value in [("main_depth","48"),("sub_depth","40"),
                          ("BGMode","2"),("bgmode","0"),("TM","13"),
                          ("TS","00"),("CGWSEL","00"),("CGADSUB","44"),
                          ("CGRAM_1B","000c"),("CGRAM_C6","04e0"),
                          ("brightness","15"),("callback","3792"),
                          ("x","120"),("RGB565","38c0")]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                q.decode_mode1_depth({**GOOD,key:value})
        with self.assertRaises(ValueError):
            q.decode_mode1_depth({"x":"121"})


if __name__=="__main__":
    unittest.main()
