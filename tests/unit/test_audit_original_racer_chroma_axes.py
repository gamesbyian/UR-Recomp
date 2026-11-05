"""Dependency-free synthetic tests of source-authenticated 2D chroma axes."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "source_chroma_axis", ROOT/"tools/art/audit_original_racer_chroma_axes.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def frame(player="p1", slant=1, crop=False):
    raw=bytearray(64*64*4)
    r,g,b=(231,57,33) if player=="p1" else (28,89,222)
    for y in range(10,30 if not crop else 16):
        shift=(y-10)*slant//3
        for x in (27+shift,28+shift,29+shift):
            if 0<=x<64:
                i=4*(y*64+x)
                raw[i:i+4]=bytes((r,g,b,255))
    return bytes(raw)


class ChromaAxisTests(unittest.TestCase):
    def test_positive_and_negative_source_projected_angles(self):
        right=mod.painted_axis(frame(slant=1),"p1")
        left=mod.painted_axis(frame(slant=-1),"p1")
        self.assertEqual(right["player_colour_indicator"],"red")
        self.assertGreater(right["signed_axis_angle_from_image_vertical_deg"],0)
        self.assertLess(left["signed_axis_angle_from_image_vertical_deg"],0)
        self.assertFalse(right["source_geometry_or_joints_recovered"])
        self.assertEqual(right["top_3_nonempty_rows"],[10,11,12])
        self.assertEqual(right["bottom_3_nonempty_rows"],[27,28,29])

    def test_blue_player_uses_existing_original_chroma_classifier(self):
        blue=mod.painted_axis(frame("p2",1),"p2")
        self.assertEqual(blue["player_colour_indicator"],"blue")
        self.assertEqual(blue["pixel_count"],60)
        with self.assertRaisesRegex(ValueError,"too few"):
            mod.painted_axis(frame("p2",1),"p1")

    def test_rejects_bad_alpha_size_cropped_chroma(self):
        with self.assertRaises(ValueError):
            mod.painted_axis(b"", "p1")
        with self.assertRaises(ValueError):
            mod.painted_axis(frame(),"p3")
        bad=bytearray(frame());bad[3]=120
        with self.assertRaisesRegex(ValueError,"non-binary"):
            mod.painted_axis(bytes(bad),"p1")
        with self.assertRaisesRegex(ValueError,"insufficient"):
            mod.painted_axis(frame(crop=True),"p1")

    def test_same_original_mask_variants_get_single_shape_vote(self):
        original=mod.painted_axis(frame(),"p1")
        other=mod.painted_axis(frame("p2"),"p2")
        inputs=[
            {"player":p,"binary_mask_sha256":"a"*64,
             "source_rgba_sha256":sha,"representation_id":ident,
             "measurement":measurement}
            for p,sha,ident,measurement in [
                ("p1","1"*64,"r1",original),
                ("p1","1"*64,"r1-repeat",original),
                ("p2","2"*64,"b1",other),
            ]
        ]
        result=mod.reduce_source_variants(inputs)
        self.assertEqual(result["independent_exact_source_binary_masks"],1)
        v=result["source_masks"][0]
        self.assertEqual(v["different_player_or_palette_variants"],2)
        self.assertEqual(len(v["source_colour_variants"][0]["representation_ids"]),2)
        self.assertTrue(result["one_vote_per_exact_binary_mask"])
        inputs[1]["measurement"]=dict(original,pixel_count=999)
        with self.assertRaisesRegex(ValueError,"measured differently"):
            mod.reduce_source_variants(inputs)

    def test_empty_and_forged_representation_rejected(self):
        with self.assertRaises(ValueError):
            mod.reduce_source_variants([])
        m=mod.painted_axis(frame(),"p1")
        for broken in (
            {"player":"other","binary_mask_sha256":"a"*64,
             "source_rgba_sha256":"1"*64,"representation_id":"wrong",
             "measurement":m},
            {"player":"p1","binary_mask_sha256":"a",
             "source_rgba_sha256":"1"*64,"representation_id":"wrong",
             "measurement":m},
        ):
            with self.assertRaises(ValueError):
                mod.reduce_source_variants([broken])


if __name__=="__main__":
    unittest.main()
