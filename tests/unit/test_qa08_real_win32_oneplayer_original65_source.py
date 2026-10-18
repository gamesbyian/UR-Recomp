"""Source-locked actual 2014 1P moving-race 65-frame native graphics receipt."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/"analysis/data/qa08-real-win32-2014-original-1p65-source-20261017.json"
class AuthenticOnePlayer(unittest.TestCase):
    def setUp(self): self.x=json.loads(FILE.read_text())
    def test_original_and_native_source_sha(self):
        x=self.x
        self.assertEqual(x["source"]["original_NO_TURBO_controller_script_SHA256"],
                         "74527132f85e136985edfe5de9b84172a4d1a3ecd8814af7c6e481fd0603d56b")
        self.assertEqual(x["source"]["native_complete_5447frame_guest_CRC_sha256"],
                         "465ec5930c0d84b451c4c633d915184dbec44f2dd7728a0bb49093d913b69244")
        self.assertEqual(len(x["source"]["native_all_65_complete_P7_frame_SHA256_sequence_digest"]),64)
    def test_geometry_and_exact_source_counts(self):
        p=self.x["actual_source_comparison"]
        self.assertEqual(p["native_guest_frames"]["first"],
                         p["original_callbacks"]["first"]+1)
        self.assertEqual(p["native_guest_frames"]["last"],
                         p["original_callbacks"]["last"]+1)
        self.assertEqual(p["actual_RGB5_source_pixels_compared"],
                         p["real_1p_race_source_frames"]*p["per_frame_full_256x224_pixels"])
        self.assertEqual(p["actual_RGB5_source_pixels_compared"],3727360)
        self.assertEqual(p["source_exact_full_frames"],65)
        self.assertEqual(p["RGB5_pixel_differences"],0)
        self.assertEqual(p["missing_or_duplicate_frames"],0)
    def test_do_not_infer_full_gameplay_or_release(self):
        self.assertTrue(all(value is False for value in self.x["limits"].values()))
        self.assertFalse(self.x["limits"]["relative_1P_raster_improvement_over_unmodified_baseline_qualified"])
if __name__=="__main__":unittest.main()
