"""Named-policy source-centre coverage does not imply physical acceptance."""
import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa06_raster_roi_reference as qa

class Coverage(unittest.TestCase):
    def test_4k_full_source_centres(self):
        for mode,w,fit in (("original",256,F(1)),("world342",342,F(512,513))):
            roi=qa.raster_roi(w,224,3840,2160,horizontal_fit=fit)
            result=qa.audit_named_policy_sampling_coverage(roi,mode=mode)
            self.assertTrue(result["full_source_centre_coverage"])
            self.assertEqual(result["skipped_source_pixels"],0)
            self.assertFalse(result["physical_screenshot_observed"])
            self.assertEqual(result["release_gate_credit"],0)

    def test_downsampled_host_skips_source_pixel_centres(self):
        roi=qa.raster_roi(256,224,64,64)
        result=qa.audit_named_policy_sampling_coverage(roi,mode="original")
        self.assertFalse(result["full_source_centre_coverage"])
        self.assertGreater(result["skipped_source_pixels"],0)

    def test_tampered_roi_is_rejected(self):
        roi=qa.raster_roi(342,224,3840,2160,horizontal_fit=F(512,513))
        wrong=copy.deepcopy(roi)
        wrong["roi_xywh"][2]-=1
        with self.assertRaises(ValueError):
            qa.audit_named_policy_sampling_coverage(wrong,mode="world342")

    def test_wrong_mode_is_rejected(self):
        roi=qa.raster_roi(256,224,3840,2160)
        with self.assertRaises(ValueError):
            qa.audit_named_policy_sampling_coverage(roi,mode="world342")
        with self.assertRaises(ValueError):
            qa.audit_named_policy_sampling_coverage(roi,mode="unsupported")

if __name__=="__main__":
    unittest.main()
