"""ROM-free, model-free wheel-disc source-material uncertainty contracts."""
import unittest

from tools.art.audit_original_racer_paint_wheel_disc import (
    disk_band_fractions, envelope, compare_shapes,
    WHEEL_RING_RADIUS_LOGICAL_PX,
)
from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import ANGLES


def disk_points():
    return {(25+i,27+j) for i in range(4) for j in range(6)}


def source_model():
    masks=[]
    images={}
    for i in range(35):
        mask=f"{1000+i:064x}"
        variants=[]
        for k in range(2 if i<6 else 1):
            rgba=f"{100000+i*3+k:064x}"
            variants.append({"rgba_sha256":rgba,
                             "player":"p1",
                             "measurement":{"pixel_count":24}})
            images[rgba]={
                "source_player":"p1",
                "source_binary_mask_sha256":mask,
                "painted_source_pixels":24,
                "all_original_ring_centre_candidates":disk_band_fractions(
                    disk_points(),[[27,29,7],[28,29,7]]),
            }
        masks.append({"original_binary_mask_sha256":mask,
                      "equal_colour_variant_mean_projected_angle_deg":0.,
                      "source_colour_variants":variants})
    model={a:{"blue_model_painted_axis_degrees":float(-a),
              "fraction_inside_source_ring_disc":0.2,
              "fraction_at_or_below_wheel_top":0.3,
              "fraction_at_or_below_wheel_centre":0.1}
           for a in ANGLES}
    return {"source_variants":{"source_masks":masks}},images,model


class WheelDiskEvidenceTests(unittest.TestCase):
    def test_exact_disk_and_wheel_relative_bands_are_not_silhouette_alignment(self):
        pts=disk_points()
        stats=disk_band_fractions(pts,[[27,29,7]])
        self.assertEqual(WHEEL_RING_RADIUS_LOGICAL_PX,7)
        self.assertEqual(len(stats),1)
        self.assertEqual(stats[0]["fraction_inside_source_ring_disc"],1.)
        self.assertEqual(stats[0]["fraction_at_or_below_wheel_top"],1.)
        self.assertTrue(0<stats[0]["fraction_at_or_below_wheel_centre"]<1)
        translated={(x+4,y+3) for x,y in pts}
        self.assertEqual(disk_band_fractions(translated,[[31,32,7]])[0][
            "fraction_inside_source_ring_disc"],1.)

    def test_original_2d_ring_candidates_preserve_both_tied_fractions(self):
        pts={(20,y) for y in range(10,24)}
        stats=disk_band_fractions(pts,[[20,20,7],[20,21,7]])
        self.assertEqual(len(stats),2)
        a,b=envelope(stats,"fraction_at_or_below_wheel_centre")
        self.assertLess(a,b)
        self.assertEqual(a,3/14)
        self.assertEqual(b,4/14)
        self.assertEqual(envelope(stats,"fraction_at_or_below_wheel_top"),
                         (10/14,11/14))

    def test_bad_source_or_fake_wheel_radius_cannot_be_counted(self):
        pts=disk_points()
        for invalid in ([],[[27,29,8]],[[64,29,7]],
                        [[float("nan"),29,7]],[[27,-1,7]]):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                disk_band_fractions(pts,invalid)
        for invalid in (set(),{(2,3)},pts|{(-1,0)},pts|{(2.5,2)}):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                disk_band_fractions(invalid,[[27,29,7]])
        with self.assertRaisesRegex(ValueError,"empty"):
            envelope([], "fraction_inside_source_ring_disc")

    def test_census_one_vote_per_mask_all_41_original_rgb_variants(self):
        chroma,images,model=source_model()
        evidence=compare_shapes(chroma,images,model)
        self.assertEqual(evidence["summary"]["all35"]["distinct_original_binary_masks"],35)
        self.assertEqual(sum(len(r["source_original_RGBA_variants"]) for r in
                             evidence["per_original_binary_mask"]),41)
        bands=evidence["summary"]["all35"]["inside_source_ring_disc"]
        self.assertEqual(bands["source_strictly_greater_with_all_tied_centres"],35)
        self.assertEqual(bands["model_mean"],0.2)
        self.assertLessEqual(bands["source_min_mean"],bands["source_max_mean"])

    def test_source_shape_family_and_rgba_mismatch_fails_closed(self):
        chroma,images,model=source_model()
        identities=[r["original_binary_mask_sha256"]
                    for r in chroma["source_variants"]["source_masks"]]
        family={mask:"first16" if i<16 else "additional19"
                for i,mask in enumerate(identities)}
        e=compare_shapes(chroma,images,model,family)
        self.assertEqual(e["summary"]["first16"]["distinct_original_binary_masks"],16)
        self.assertEqual(e["summary"]["additional19"]["distinct_original_binary_masks"],19)
        with self.assertRaisesRegex(ValueError,"family"):
            compare_shapes(chroma,images,model,{})
        del images[chroma["source_variants"]["source_masks"][0]["source_colour_variants"][0]["rgba_sha256"]]
        with self.assertRaises(ValueError):
            compare_shapes(chroma,images,model)
        chroma,images,model=source_model()
        chroma["source_variants"]["source_masks"][1][
            "original_binary_mask_sha256"]=identities[0]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            compare_shapes(chroma,images,model)


if __name__=="__main__":
    unittest.main()
