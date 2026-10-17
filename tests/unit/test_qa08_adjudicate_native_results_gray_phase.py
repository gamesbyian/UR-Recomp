"""Bounded source-only native results 4-state palette source verifier."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_adjudicate_native_results_gray_phase as m

class OriginalNativeResultsPhaseTest(unittest.TestCase):
    def test_source_cryptographic_pins_and_full_frame_geometry(self):
        self.assertEqual(len(m.ANOMALY_FRAMES),13)
        self.assertEqual(m.ANOMALY_FRAMES[0],4064)
        self.assertEqual(m.ANOMALY_FRAMES[-1],5408)
        self.assertEqual(len(list(m.GUEST_FRAMES)),263)
        self.assertEqual(m.GEOMETRY_BYTES,256*224*4)
        self.assertEqual(m.GUEST_CRC,"c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876")
        self.assertEqual(len(m.GRAY_ROTATION),4)

    def test_raw_rgb5_converts_only_snes_six_bit_green(self):
        n=m.GEOMETRY_BYTES//4
        # Original BGRX pixel first, Windows RGBA pixel first.
        orig=bytes([132,132,132,0])+bytes(4*(n-1))
        win=bytes([123,123,123,255])+bytes(4*(n-1))
        # Expand original green from its five MSBs as true source comparator.
        # 132 >>3 = 16, restored green is 132.
        result=m.tally(orig,win)
        self.assertEqual(result["total_wrong_RGB5_pixels"],1)
        self.assertEqual(result["four_state_gray_rotation_wrong_pixels"],1)
        self.assertEqual(result["gray_rotation_counts"]["123->132"],1)
        with self.assertRaises(ValueError):
            m.tally(orig[:-1],win)

    def test_rejects_unauthenticated_source_archive(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            p=Path(td)/"fake.zip"
            p.write_bytes(b"not source evidence")
            with self.assertRaises(ValueError):
                m.validate_archive(p,m.ORIGINAL_ZIP)

if __name__=="__main__":
    unittest.main()
