"""Bounded source-faithful viewport sampling checks, no physical 4K claim."""
import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa06_raster_roi_reference as qa


class H18PixelSampling(unittest.TestCase):
    def test_4k_original_and_widened_policy(self):
        for mode, width, fit, rect in (
            ("original", 256, F(1), [480, 0, 2880, 2160]),
            ("world342", 342, F(512, 513), [0, 0, 3840, 2160]),
        ):
            with self.subTest(mode=mode):
                roi=qa.raster_roi(width,224,3840,2160,horizontal_fit=fit)
                self.assertEqual(roi["roi_xywh"],rect)
                for sx,sy in ((0,0),(width//2,112),(width-1,223)):
                    x0,y0,x1,y1=qa.validated_policy_source_host_span(
                        roi,sx,sy,mode=mode)
                    self.assertLess(x0,x1)
                    self.assertLess(y0,y1)
                    for x,y in ((x0,y0),(x1-1,y1-1)):
                        self.assertEqual(
                            qa.validated_policy_source_pixel_at_host_coordinate(
                                roi,x,y,mode=mode),(sx,sy))

    def test_tampered_policy_is_rejected(self):
        roi=qa.raster_roi(342,224,3840,2160,horizontal_fit=F(512,513))
        wrong=copy.deepcopy(roi)
        wrong["roi_xywh"][0]+=1
        with self.assertRaises(ValueError):
            qa.validated_policy_source_host_span(wrong,0,0,mode="world342")
        with self.assertRaises(ValueError):
            qa.validated_policy_source_host_span(roi,0,0,mode="invalid")

    def test_inverse_matches_all_forward_samples_for_small_grids(self):
        for source in range(1,37):
            for output in range(1,43):
                spans=[qa.source_pixel_host_span(source,output,i)
                       for i in range(source)]
                for host_pixel in range(output):
                    i=qa.source_pixel_at_output_centre(source,output,host_pixel)
                    self.assertTrue(spans[i][0] <= host_pixel < spans[i][1])
                for index,(lo,hi) in enumerate(spans):
                    self.assertTrue(all(
                        qa.source_pixel_at_output_centre(source,output,x)==index
                        for x in range(lo,hi)))

    def test_matte_and_downsampled_source_holes(self):
        roi=qa.raster_roi(256,224,3840,2160)
        self.assertIsNone(qa.validated_policy_source_pixel_at_host_coordinate(
            roi,0,100,mode="original"))
        small=qa.raster_roi(256,224,64,64)
        holes=sum(qa.validated_policy_source_host_span(small,x,50,
                        mode="original")[0] ==
                  qa.validated_policy_source_host_span(small,x,50,
                        mode="original")[2] for x in range(256))
        self.assertGreater(holes,100)


if __name__=="__main__":
    unittest.main()
