"""ROM-free painted spatial-covariance 2D controls; no 3D likeness claim."""
import unittest
from tools.art.evaluate_original_racer_paint_spatial_moments import (
    painted_spread, spread_from_binary_mask, compare,
)
from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import ANGLES


def rectangle(x=12,y=15,width=4,height=5):
    return {(a,b) for a in range(x,x+width) for b in range(y,y+height)}


def model():
    return {a:{"painted_axis_degrees":float(-a),"sigma_major_physical_px":3.,
               "sigma_minor_physical_px":2.} for a in ANGLES}


def mock_corpus():
    rows=[]; variants={}
    for i in range(35):
        shape=f"{i+1000:064x}"
        group=[]
        for k in range(2 if i<6 else 1):
            rgba=f"{i*10+k+1:064x}"
            group.append({"rgba_sha256":rgba})
            variants[rgba]={"source_binary_mask_sha256":shape,"source_player":"p1",
                            "sigma_major_physical_px":4.,
                            "sigma_minor_physical_px":4.}
        rows.append({"original_binary_mask_sha256":shape,
                     "equal_colour_variant_mean_projected_angle_deg":0.,
                     "source_colour_variants":group})
    return {"source_variants":{"source_masks":rows}},variants


class PaintedMomentsTests(unittest.TestCase):
    def test_translation_invariance_and_7_to_6_pixel_aspect(self):
        a=painted_spread(rectangle())
        b=painted_spread(rectangle(18,19))
        self.assertEqual(a,b)
        self.assertEqual(a["painted_pixels"],20)
        self.assertGreater(a["sigma_major_physical_px"],a["sigma_minor_physical_px"])
        self.assertFalse(a["original_3d_part_width_recovered"])

    def test_widthlike_variation_exposes_minor_covariance(self):
        thin=painted_spread(rectangle(width=3,height=9))
        broad=painted_spread(rectangle(width=8,height=9))
        self.assertGreater(broad["sigma_minor_physical_px"],
                           thin["sigma_minor_physical_px"])
        with self.assertRaisesRegex(ValueError,"degenerate"):
            painted_spread({(20,y) for y in range(12)})
        for invalid in (set(),{(-1,10)}|rectangle(),
                        {(12.5,20)}|rectangle()):
            with self.assertRaises(ValueError):
                painted_spread(invalid)

    def test_all_35_binary_masks_each_one_vote_and_all_41_rgb_variants(self):
        corpus,variants=mock_corpus()
        r=compare(corpus,variants,model())
        all_shapes=r["summary"]["all35"]
        self.assertEqual(all_shapes["independent_binary_masks"],35)
        self.assertAlmostEqual(all_shapes["mean_source_to_model_major_spread_ratio"],4/3)
        self.assertAlmostEqual(all_shapes["mean_source_to_model_minor_spread_ratio"],2.)
        self.assertEqual(all_shapes["source_minor_spread_exceeds_model_count"],35)
        self.assertEqual(len(r["per_original_binary_mask"][0]["source_original_RGBA_variants"]),2)
        self.assertEqual(sum(len(x["source_original_RGBA_variants"])
                             for x in r["per_original_binary_mask"]),41)

    def test_source_identity_rejects_alias_and_family_leakage(self):
        corpus,variants=mock_corpus()
        families={r["original_binary_mask_sha256"]:("first16" if i<16 else "additional19")
                  for i,r in enumerate(corpus["source_variants"]["source_masks"])}
        r=compare(corpus,variants,model(),families)
        self.assertEqual(r["summary"]["first16"]["independent_binary_masks"],16)
        self.assertEqual(r["summary"]["additional19"]["independent_binary_masks"],19)
        with self.assertRaisesRegex(ValueError,"family"):
            compare(corpus,variants,model(),{})
        corpus["source_variants"]["source_masks"][1]["original_binary_mask_sha256"]=(
            corpus["source_variants"]["source_masks"][0]["original_binary_mask_sha256"])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            compare(corpus,variants,model())

    def test_binary_raster_and_invalid_paint_points(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("NumPy optional for true image raster")
        mask=np.zeros((64,64),dtype=np.uint8)
        mask[15:20,12:16]=1
        self.assertEqual(spread_from_binary_mask(mask)["painted_pixels"],20)
        mask[15,12]=3
        with self.assertRaisesRegex(ValueError,"binary"):
            spread_from_binary_mask(mask)
        with self.assertRaises(ValueError):
            spread_from_binary_mask(np.ones((10,10),dtype=np.uint8))


if __name__=="__main__":
    unittest.main()
