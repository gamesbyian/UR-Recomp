"""Bound source observations from true 65 source-registered Win32/2014 1P images."""
import json,unittest
from pathlib import Path
DOC=Path(__file__).resolve().parents[2]/"analysis/data/qa08-current-premath-real-original-oneplayer65-20261017.json"
class SourceReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads(DOC.read_text())
    def test_source_images_are_not_repeated_or_cropped(self):
        r=self.r["source"]
        self.assertEqual(r["frame_count"],65)
        self.assertEqual(r["full_256x224_pixels"],3727360)
        self.assertEqual(r["wrong_rgb5_pixels"],0)
        self.assertEqual(r["unique_real_native_image_hashes"],65)
        self.assertEqual(r["source_first_to_last_changed_rgb5"],26657)
        self.assertEqual(r["native_guest_first"],r["original_callback_first"]+1)
    def test_current_two_real_windows_guest_transcripts_equal(self):
        x=self.r
        self.assertTrue(x["guest"]["clean_current_RF017_same_script_guest_CRC_comparison_completed"])
        self.assertTrue(x["guest"]["current_clean_native_guest_CRC_equivalence_verified"])
        self.assertEqual(x["guest"]["clean_current_RF017_guest_crc_sha256"],
                         x["guest"]["current_experimental_Win32_guest_CRC_sha256"])
        self.assertTrue(x["verified_independent_guest_pair"]["native_guest_CRC_equal"])
        self.assertFalse(x["guest"]["original_snes9x_2014_CPU_equivalence_proven"])
        self.assertFalse(x["quality"]["current_guest_source_parity_accepted"])
    def test_historical_crc_mismatch_cannot_be_qualified(self):
        x=self.r
        self.assertFalse(x["guest"]["historical_guest_CRC_equal"])
        self.assertFalse(x["guest"]["original_snes9x_2014_CPU_equivalence_proven"])
        self.assertFalse(x["quality"]["full_1P_event_exact"])
        self.assertFalse(x["quality"]["physical_4K_7to6_HD_likeness_release_accepted"])
        if not x["guest"]["clean_current_RF017_same_script_guest_CRC_verified"]:
            self.assertFalse(x["quality"]["current_guest_source_parity_accepted"])
            self.assertIsNone(x["guest"]["clean_current_RF017_guest_crc_sha256"])
        else:
            self.assertEqual(x["guest"]["clean_current_RF017_guest_crc_sha256"],
                             x["guest"]["current_experimental_Win32_guest_CRC_sha256"])
if __name__=="__main__":unittest.main()
