"""Conservative original pixel vs 2026 parent support; no inferred source anatomy."""
import unittest
from tools.art.audit_source_registered_glb_parent_overlap import (
    SCHEMA,TICKS,ARMS,parent_overlap)
from tools.art.glb_parent_part_id_raster import PARTS


class RegisteredGLBParentTests(unittest.TestCase):
    def test_original_and_projected_model_support_conserved_by_part(self):
        original=bytearray(4096);parents={p:bytearray(4096) for p in PARTS}
        original[3*64+10]=1;original[3*64+11]=1
        original[4*64+10]=1;original[33*64+8]=1
        parents["saddle"][3*64+10]=1
        parents["saddle"][3*64+11]=1
        parents["fork_and_frame"][3*64+10]=1
        parents["fork_and_frame"][4*64+11]=1
        parents["tire"][33*64+8]=1
        parents["rim_and_hub"][33*64+8]=1
        r=parent_overlap(bytes(original),{p:bytes(m) for p,m in parents.items()})
        self.assertEqual(r["whole_original_vs_2026_alpha"]["tp"],3)
        self.assertEqual(r["whole_original_vs_2026_alpha"]["fp"],1)
        self.assertEqual(r["whole_original_vs_2026_alpha"]["fn"],1)
        upper=r["source_y_regions"]["upper_y0_14"]
        self.assertEqual((upper["tp"],upper["fp"],upper["fn"]),(2,1,1))
        self.assertEqual(upper["nonexclusive_2026_projection_pixels"],1)
        self.assertEqual(upper["authored_2026_parent_projection"]["saddle"]
                         ["exclusive_model_original_overlap"],1)
        self.assertEqual(r["source_y_regions"]["lower_y27_63"]
                         ["nonexclusive_2026_projection_pixels"],1)

    def test_bad_binary_and_missing_parts_fail(self):
        blank={p:bytes(4096) for p in PARTS}
        with self.assertRaises(ValueError):parent_overlap(b"bad",blank)
        with self.assertRaises(ValueError):
            parent_overlap(bytes(4096),{"saddle":bytes(4096)})
        blank["saddle"]=bytes([2])+bytes(4095)
        with self.assertRaises(ValueError):parent_overlap(bytes(4096),blank)

    def test_frozen_source_events_and_alternatives(self):
        self.assertEqual(TICKS,{"blue":1603,"red":1606})
        self.assertEqual(ARMS,("static_2026_3d","wheel_axle_root_only",
                               "historical_midbody_root_only"))
        self.assertTrue(SCHEMA.endswith("PARENT-OVERLAP/1"))


if __name__=="__main__":unittest.main()
