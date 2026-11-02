"""ROM-free 7:6 painted-endpoint vector and optional visible-blue controls."""
import math
import unittest
from tools.art.audit_original_racer_painted_frame_length import (
    physical_painted_vector, visible_blue_endpoints,
)


class SourcePaintEndpointTests(unittest.TestCase):
    def test_physical_length_and_signed_axis(self):
        v=physical_painted_vector([2,2],[8,12])
        self.assertEqual(v["dx_physical_px"],7.)
        self.assertEqual(v["dy_physical_px"],10.)
        self.assertEqual(v["length_physical_px"],round(math.sqrt(149),8))
        self.assertEqual(v["angle_from_image_vertical_deg"],round(
            math.degrees(math.atan2(7,10)),8))

    def test_absolute_translation_is_irrelevant(self):
        a=physical_painted_vector([3.25,10.5],[15.5,27.25])
        b=physical_painted_vector([23.25,4.5],[35.5,21.25])
        self.assertEqual(a,b)

    def test_invalid_source_endpoints_fail_closed(self):
        for top,bottom in (([0,1],[4,0]),([2,2],[2,2]),
                           ([float("nan"),1],[2,4]),
                           ([2,2],[float("inf"),4]),
                           ([1],[4,5]),(None,[3,7])):
            with self.subTest(top=top,bottom=bottom),self.assertRaises(ValueError):
                physical_painted_vector(top,bottom)


try:
    import numpy as np
except ImportError:
    np=None


@unittest.skipUnless(np is not None,"offline NumPy is optional")
class DepthVisibleBlueEndpointTests(unittest.TestCase):
    def test_64px_source_painted_pixel_centres(self):
        m=np.zeros((64,64),dtype=np.uint8)
        for y in range(10,26):
            m[y,20]=1
        v=visible_blue_endpoints(m)
        self.assertEqual(v["dx_physical_px"],0.)
        self.assertEqual(v["length_physical_px"],13.)
        self.assertEqual(v["angle_from_image_vertical_deg"],0.)

    def test_empty_and_invalid_material_masks(self):
        with self.assertRaises(ValueError):
            visible_blue_endpoints(np.zeros((64,64),dtype=np.uint8))
        m=np.zeros((64,64),dtype=np.uint8)
        m[10,20]=2
        with self.assertRaisesRegex(ValueError,"binary"):
            visible_blue_endpoints(m)


if __name__=="__main__":
    unittest.main()
