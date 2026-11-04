"""Actual 2026 GLB projected-parent coverage in original 64px y bands."""
from pathlib import Path
import unittest

from tools.art.count_real_glb_parent_source_y_bands import (
    PARTS,SOURCE_Y_BANDS,CANONICAL_TOTAL,CANONICAL_PARTS,count_parts,SCHEMA,
)


class SourceYBandPartOccupancyTests(unittest.TestCase):
    def test_each_authored_part_has_own_mask_and_union_counts_are_not_additive(self):
        masks={p:bytearray(4096) for p in PARTS}
        masks["saddle"][3*64+10]=1
        masks["fork_and_frame"][3*64+10]=1
        masks["saddle"][6*64+9]=1
        masks["fork_and_frame"][20*64+11]=1
        masks["tire"][33*64+12]=1
        masks["rim_and_hub"][33*64+12]=1
        masks["pedals"][35*64+17]=1
        receipt=count_parts({p:bytes(v) for p,v in masks.items()})
        self.assertEqual(receipt["full_2026_model_union_64px_pixels"],5)
        self.assertEqual(receipt["full_2026_model_part_occupancy_before_union"],
                         {"tire":1,"rim_and_hub":1,"fork_and_frame":2,
                          "pedals":1,"saddle":2})
        up=receipt["per_source_y_band"]["upper_y0_14"]
        self.assertEqual(up["whole_actual_2026_model_opaque_pixels"],2)
        self.assertEqual(up["per_2026_parent"]["saddle"]["projected_source64_occupied_pixels"],2)
        self.assertEqual(up["per_2026_parent"]["saddle"]["unique_union_silhouette_pixels"],1)
        self.assertEqual(up["per_2026_parent"]["fork_and_frame"]["unique_union_silhouette_pixels"],0)
        self.assertEqual(receipt["per_source_y_band"]["middle_y15_26"]
                         ["whole_actual_2026_model_opaque_pixels"],1)
        self.assertEqual(receipt["per_source_y_band"]["lower_y27_63"]
                         ["whole_actual_2026_model_opaque_pixels"],2)
        self.assertEqual(SOURCE_Y_BANDS,(("upper_y0_14",0,14),
                                         ("middle_y15_26",15,26),
                                         ("lower_y27_63",27,63)))
        self.assertEqual(CANONICAL_TOTAL,267)
        self.assertEqual(CANONICAL_PARTS,{
            "tire":124,"rim_and_hub":70,"fork_and_frame":46,"pedals":14,"saddle":56})
        self.assertEqual(SCHEMA,"UR-ART4K-SOURCE-Y-BAND-REAL-2026-GLB-PARENT-CENSUS/1")

    def test_wrong_parent_source_plane_fails_closed(self):
        masks={p:bytes(4096) for p in PARTS}
        with self.assertRaisesRegex(ValueError,"five real"):
            count_parts(masks)
        bad={p:bytes([1])+bytes(4095) for p in PARTS}
        bad["saddle"]=b"bad"
        with self.assertRaisesRegex(ValueError,"five real"):
            count_parts(bad)
        del bad["saddle"]
        with self.assertRaisesRegex(ValueError,"five real"):
            count_parts(bad)


if __name__=="__main__":
    unittest.main()
