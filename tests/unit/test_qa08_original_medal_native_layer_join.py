"""Bounded original/native Mode3 medal live pixel and OAM source contracts."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_medal_native_layer_join as m

class MedalJoinTest(unittest.TestCase):
    def test_mode3_pinned_snes9x_source_main_depth(self):
        self.assertEqual(m.decode_original_mode3_main_depth(40,0x13),"OBJ priority1")
        self.assertEqual(m.decode_original_mode3_main_depth(39,0x13),"BG1 low priority")
        for z,tm in ((40,0),(39,0x10),(33,0x13),(48,0x13)):
            with self.subTest(z=z,tm=tm),self.assertRaises(ValueError):
                m.decode_original_mode3_main_depth(z,tm)
    def test_two_registered_correct_source_callbacks_and_oam_delta(self):
        self.assertEqual(m.PAIRS,((4031,4032),(4175,4176)))
        self.assertEqual(m.PIXELS,((207,91),(205,115),(205,139),(225,96),(225,120)))
        self.assertEqual(m.SLOTS,(96,97,98,99,112,113,114))
        self.assertEqual([m.EXPECTED_NAME_DELTA[k] for k in m.SLOTS],[2,2,0,0,-2,-2,-2])
        with self.assertRaises(ValueError):
            m.original_rgb5(b"short",205,115)
    def test_unverified_source_archive_rejected_before_PPU_interpretation(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            fake=Path(folder)/"fabricated.zip";fake.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError,"source archive"):
                m.assess(fake,fake,fake)
if __name__=="__main__":
    unittest.main()
