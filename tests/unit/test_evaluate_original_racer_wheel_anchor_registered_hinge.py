"""Source-only wheel anchor, fourfold raster translation and bounded scoring."""
import unittest
from tools.art.evaluate_original_racer_wheel_anchor_registered_hinge import (
    centre_shift_4x, translate_4x, iou,
)

class WheelRegisteredPoseTests(unittest.TestCase):
    def test_exact_model_axle_to_source_raster_pixel_mapping(self):
        self.assertEqual(centre_shift_4x(33,28,(136.,116.)),(-2,-2))
        self.assertEqual(centre_shift_4x(30,26,(136.,116.)),(-14,-10))
        with self.assertRaisesRegex(ValueError,"nonintegral 4x"):
            centre_shift_4x(33,28,(136.25,116.))
        for args in ((64,28,(136.,116.)),(33,-1,(136.,116.))):
            with self.assertRaises(ValueError):
                centre_shift_4x(*args)

    def test_subsample_is_4x_centre_and_never_crops_model(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("numpy optional on default tool-only worker")
        m=np.zeros((256,256),dtype=np.uint8)
        m[6,6]=1
        translated=translate_4x(m,4,4)
        self.assertEqual(translated[2*64+2],1)
        self.assertEqual(sum(translated),1)
        self.assertEqual(sum(translate_4x(m,1,0)),0)
        m[0,0]=1
        with self.assertRaisesRegex(ValueError,"crop"):
            translate_4x(m,-1,0)
        with self.assertRaisesRegex(ValueError,"crop"):
            translate_4x(m,0,-1)

    def test_iou_retains_actual_raster_coordinate_not_best_shift(self):
        a=bytearray(4096)
        b=bytearray(4096)
        a[64+2]=a[64+3]=1
        b[64+3]=b[64+4]=1
        self.assertEqual(iou(bytes(a),bytes(b)),round(1/3,8))
        self.assertEqual(iou(bytes(a),bytes(a)),1.)
        self.assertEqual(iou(bytes(a),bytes(4096)),0.)
        with self.assertRaisesRegex(ValueError,"binary"):
            iou(bytes(a),b"x"*4096)

    def test_no_arbitrary_subpixel_camera_shift(self):
        with self.assertRaisesRegex(ValueError,"nonintegral 4x"):
            centre_shift_4x(30,28,(136.,116.125))
        with self.assertRaisesRegex(ValueError,"invalid source"):
            centre_shift_4x(True,28,(136.,116.))


if __name__=="__main__":
    unittest.main()
