"""Source-specific original-ROM/real GLB pose comparison numerical safety."""
import json
import math
from pathlib import Path
import unittest

from tools.art.score_original_mesen24_fixed_pivot_glb import (
    SCHEMA, ARM_NAMES, EVENTS, SELECTED,
    check_receipts, source_center, rotate_source_2d, anchor, metric,
)

try:
    import numpy as np
    from tools.art.score_original_mesen24_fixed_pivot_glb import registered_mask4
except ImportError:
    np=None


class GenuineSourceGLBPivotScoreContracts(unittest.TestCase):
    def test_frozen_two_events_and_four_3D_arms_plus_2D_nulls(self):
        self.assertEqual(set(EVENTS),{"blue","red"})
        self.assertEqual(SELECTED["blue"],[1602,1603,1609,1610])
        self.assertEqual(SELECTED["red"],[1605,1606,1609,1610])
        self.assertEqual(len(ARM_NAMES),7)
        self.assertIn("source_original_2d_rotation",ARM_NAMES)
        self.assertIn("wheel_axle_root_plus_phase",ARM_NAMES)
        self.assertIn("historical_midbody_root_only",ARM_NAMES)

    def test_true_64px_alpha_comparison_and_no_false_pixel_registration(self):
        original=bytearray(4096)
        original[37*64+31]=1
        original[37*64+32]=1
        orig=bytes(original)
        self.assertEqual(anchor(orig),(63,74))
        static=metric(orig,orig)
        self.assertEqual((static["tp"],static["fp"],static["fn"],static["iou"]),
                         (2,0,0,1.0))
        fake=bytearray(4096)
        fake[37*64+32]=1
        result=metric(orig,bytes(fake))
        self.assertEqual((result["tp"],result["fp"],result["fn"],result["iou"]),
                         (1,0,1,0.5))
        with self.assertRaises(ValueError):
            metric(b"bad",orig)
        with self.assertRaises(ValueError):
            anchor(bytes(4096))

    def test_fixed_original_image_rotation_requires_no_per_tick_fit(self):
        source=bytearray(4096)
        source[29*64+31]=1
        first=bytes(source)
        self.assertEqual(rotate_source_2d(first,0,(31.5,19.5)),first)
        next_image=rotate_source_2d(first,16,(31.5,19.5))
        self.assertEqual(sum(next_image),1)
        self.assertEqual(next_image[19*64+22],1)
        with self.assertRaisesRegex(ValueError,"binary original"):
            rotate_source_2d(bytes(4096),1.5,(31.5,19.5))

    def test_even_only_source_bbox_center_is_fixed_across_all_64_angles(self):
        source={"source_phase_variation_bbox_by_ROM_angle_index":
                {str(i):[10+i%3,11,21+i%3,22] for i in range(64)}}
        x,y=source_center(source)
        self.assertEqual(y,16.5)
        self.assertGreater(x,15.5)
        source["source_phase_variation_bbox_by_ROM_angle_index"]["5"]=[-1,0,3,4]
        # This bad odd source is not part of the fit. It is never consulted.
        self.assertEqual(source_center(source),(x,y))
        source["source_phase_variation_bbox_by_ROM_angle_index"]["4"]=[-1,0,3,4]
        with self.assertRaisesRegex(ValueError,"bounding box"):
            source_center(source)

    def test_missing_sha_checked_source_data_fails_before_any_model(self):
        with self.assertRaisesRegex(ValueError,"SHA mismatch"):
            check_receipts(b"",b"{}",b"{}",b"{}")


@unittest.skipUnless(np is not None,"optional NumPy")
class MaskRegistrationTests(unittest.TestCase):
    def test_single_full_4x_source_alpha_anchor_preserves_pixel_identity(self):
        array=np.zeros((256,256),dtype=bool)
        array[4*37+2,4*31+2]=True
        original=registered_mask4(array,(63,74),(63,74))
        self.assertEqual(original[37*64+31],1)
        self.assertEqual(sum(original),1)
        shifted=registered_mask4(array,(65,74),(63,74))
        self.assertEqual(shifted[37*64+32],1)
        self.assertEqual(sum(shifted),1)
        with self.assertRaisesRegex(ValueError,"clip"):
            registered_mask4(array,(500,74),(63,74))


if __name__=="__main__":
    unittest.main()
