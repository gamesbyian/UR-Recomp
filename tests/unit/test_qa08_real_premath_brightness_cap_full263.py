"""Authentic measured Win32 candidate vs 2014 full-frame graphics-source envelope."""
import json,unittest
from pathlib import Path
FILE=(Path(__file__).resolve().parents[2]/"analysis/data/"
      "qa08-real-win32-premath-brightness-cap-full263-20261017.json")
class QA08SourcePreMath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=json.loads(FILE.read_text())
    def test_exact_source_and_no_release_credit(self):
        x=self.x
        self.assertEqual(x["schema"],"qa08-real-Win32-2p-263-premath-brightness-cap-source-verdict/1")
        self.assertEqual(x["sources"]["full_5484_guest_CRC_transcript_SHA256"],
                         "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568")
        self.assertFalse(x["limitations"]["merge_to_production_approved"])
        self.assertFalse(x["limitations"]["QA08_QA10_release_gates_accepted"])
    def test_pixel_conservation_and_region_sum(self):
        x=self.x["comparison"]
        self.assertEqual(x["frames"]*x["pixels_per_frame"],x["all_pixels"])
        self.assertEqual(x["all_pixels"],15081472)
        self.assertEqual(x["baseline_wrong_RGB5"]-x["corrected_RGB5_pixels"]
                         +x["newly_wrong_RGB5_pixels"],x["experimental_wrong_RGB5"])
        for baseline, key in (("baseline_wrong","baseline_wrong_RGB5"),
                              ("experimental_wrong","experimental_wrong_RGB5"),
                              ("corrected","corrected_RGB5_pixels"),
                              ("newly_wrong","newly_wrong_RGB5_pixels")):
            self.assertEqual(sum(a[baseline] for a in x["regions"]),x[key])
        self.assertEqual(sum(a["frames"] for a in x["regions"]),x["frames"])
    def test_critical_control_and_regression_bounded(self):
        x=self.x
        zones={a["name"]:a for a in x["comparison"]["regions"]}
        for region in ("setup","moving","finish"):
            self.assertEqual(zones[region]["experimental_wrong"],0)
            self.assertEqual(zones[region]["newly_wrong"],0)
        for region in ("setup","moving","finish","results"):
            self.assertEqual(zones[region]["newly_wrong"],0)
        self.assertEqual(zones["blackout"]["newly_wrong"],1042)
        self.assertEqual(x["blackout"]["sole_regressed_native_frame"],4016)
        self.assertEqual(sum(x["blackout"]["regressed_rgb5_counts"].values()),1042)
        self.assertFalse(x["blackout"]["overpaint_or_hold_black_allowed"])
if __name__=="__main__":unittest.main()
