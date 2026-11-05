"""ROM-free painted area/length constraints with no silhouette-overlap oracle."""
import unittest

from tools.art.evaluate_original_racer_painted_extent import (
    extent_from_endpoints, extent_from_mask, original_variant_extent, compare,
)
from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import ANGLES


def variant(index,top=None,bottom=None,painted=50):
    top=top if top is not None else [20.,10.]
    bottom=bottom if bottom is not None else [20.,20.]
    return {"player":"p1","rgba_sha256":f"{index:064x}",
            "measurement":{"top_centroid_logical_xy":top,
                           "bottom_centroid_logical_xy":bottom,
                           "pixel_count":painted,
                           "signed_axis_angle_from_image_vertical_deg":0.}}


def source_rows():
    return [{"original_binary_mask_sha256":f"{i+1000:064x}",
             "equal_colour_variant_mean_projected_angle_deg":0.,
             "source_colour_variants":[variant(i+1)]}
            for i in range(35)]


def model():
    return {angle:{
        "signed_painted_axis_deg":float(-angle),
        "painted_pixels":30,
        "axial_length_physical_px":10.,
        "painted_area_per_axial_length":3.,
    } for angle in ANGLES}


class PaintedExtentTests(unittest.TestCase):
    def test_translation_invariant_source_length_and_area(self):
        r=extent_from_endpoints([20.,10.],[20.,20.],50)
        self.assertEqual(r["painted_pixels"],50)
        self.assertAlmostEqual(r["axial_length_physical_px"],10.)
        self.assertEqual(r["signed_painted_axis_deg"],0.)
        self.assertAlmostEqual(r["painted_area_per_axial_length"],5.)
        shifted=extent_from_endpoints([25.,15.],[25.,25.],50)
        self.assertEqual(r,shifted)
        tilted=extent_from_endpoints([20.,10.],[26.,18.],50)
        self.assertGreater(tilted["signed_painted_axis_deg"],0.)
        for top,bottom,n in [([20,20],[20,10],50),([20,20],[20,20],50),
                             ([20,10],[20,20],True),([0,10],[64,20],50)]:
            with self.subTest(top=top,bottom=bottom,n=n),self.assertRaises(ValueError):
                extent_from_endpoints(top,bottom,n)

    def test_all_35_source_shapes_count_once_with_bounded_rgb_variants(self):
        shapes=source_rows()
        shapes[0]["source_colour_variants"].append(variant(95,painted=40))
        result=compare(shapes,model())
        s=result["summary"]["all35"]
        self.assertEqual(s["independent_binary_source_masks"],35)
        self.assertEqual(s["original_shapes_with_more_painted_pixels_than_model"],35)
        self.assertAlmostEqual(s["mean_source_to_model_length_ratio"],1.)
        self.assertGreater(s["mean_source_to_model_area_ratio"],1.6)
        self.assertEqual(len(result["per_original_binary_mask"][0]["source_rgb_variants"]),2)
        self.assertFalse(result["per_original_binary_mask"][0]["source_variant_pose_disagreement"])

    def test_source_family_shas_and_paint_variant_authentication(self):
        shapes=source_rows()
        families={r["original_binary_mask_sha256"]:("first16" if i<16 else "additional19")
                  for i,r in enumerate(shapes)}
        r=compare(shapes,model(),families)
        self.assertEqual(r["summary"]["first16"]["independent_binary_source_masks"],16)
        self.assertEqual(r["summary"]["additional19"]["independent_binary_source_masks"],19)
        with self.assertRaisesRegex(ValueError,"source-family"):
            compare(shapes,model(),{})
        shapes[0]["source_colour_variants"][0]["measurement"][
            "signed_axis_angle_from_image_vertical_deg"]=45.
        with self.assertRaisesRegex(ValueError,"receipt inconsistent"):
            original_variant_extent(shapes[0]["source_colour_variants"][0])

    def test_reject_missing_or_repeated_source_groups(self):
        a=source_rows()
        with self.assertRaises(ValueError):
            compare(a[:34],model())
        a[1]["original_binary_mask_sha256"]=a[0]["original_binary_mask_sha256"]
        with self.assertRaisesRegex(ValueError,"duplicated"):
            compare(a,model())
        a=source_rows()
        a[0]["source_colour_variants"]=[variant(5),variant(5)]
        with self.assertRaisesRegex(ValueError,"duplicate original colour"):
            compare(a,model())
        with self.assertRaises(ValueError):
            compare(source_rows(),{0:model()[0]})

    def test_real_raster_extent_requires_binary_and_nonempty(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("NumPy optional, only real material-mask test requires it")
        mask=np.zeros((64,64),dtype=np.uint8)
        for y in range(10,30):
            mask[y,20]=1
        result=extent_from_mask(mask)
        self.assertAlmostEqual(result["axial_length_physical_px"],17.)
        self.assertEqual(result["painted_pixels"],20)
        with self.assertRaises(ValueError):
            extent_from_mask(np.zeros((64,64),dtype=bool))
        mask[10,20]=2
        with self.assertRaisesRegex(ValueError,"64x64 binary"):
            extent_from_mask(mask)


if __name__=="__main__":
    unittest.main()
