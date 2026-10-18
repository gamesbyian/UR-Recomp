"""Stable color-math-negative source mask, no rendered-pixel rewrite."""
import json,unittest
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2]/"analysis/data/qa08-real-win32-premath-results-medal-mask-20261017.json"
class ResultPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.v=json.loads(SOURCE.read_text())
    def test_source_immutable_guest(self):
        self.assertEqual(self.v["source"]["guest_CRC_sha256"],
         "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568")
        self.assertFalse(self.v["limits"]["QA08_QA10_or_release_accepted"])
    def test_grey_and_chromatic_disjoint_pixel_counts(self):
        r=self.v["result"]
        self.assertEqual(r["wrong_both_sources_achromatic"]+r["wrong_chromatic_source"],
                         r["wrong_RGB5_total"])
        self.assertEqual(sum(r["gray_phase_mappings_native_to_original"].values()),
                         r["wrong_both_sources_achromatic"])
    def test_medal_mask_is_static_and_disjoint(self):
        r=self.v["result"];m=r["medals"]
        self.assertEqual(len(m["source_frames"]),25)
        self.assertEqual(m["source_frames"],list(range(4032,5185,48)))
        self.assertEqual(m["pixels_each"]*m["count"],r["wrong_chromatic_source"])
        self.assertEqual(m["upper_91_to_105"]+m["middle_115_to_129"]+m["lower_139_to_153"],m["pixels_each"])
        self.assertEqual(m["large_difference_gt1_pixels_each"]+
                         m["remaining_RGB5_at_most_one_pixels_each"],m["pixels_each"])
        self.assertTrue(m["same_chromatic_discrepancy_mask_all_25"])
        self.assertFalse(self.v["limits"]["RGB5_only_recolor_authorized"])
if __name__=="__main__":unittest.main()
