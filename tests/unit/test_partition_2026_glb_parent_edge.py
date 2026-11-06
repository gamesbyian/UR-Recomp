"""Conserved original-source edges versus visible current GLB parent changes."""
import unittest

from tools.art.glb_parent_part_id_raster import PARTS
from tools.art.partition_2026_glb_parent_edge import (
    partition_2026_visible_motion,source_vs_model_motion_regions,
)

def mask(*coords):
    data=bytearray(4096)
    for x,y in coords:
        data[y*64+x]=1
    return bytes(data)

def blank():
    return {part:bytes(4096) for part in PARTS}

class AuthoredVisibleParentEdgeTests(unittest.TestCase):
    def test_unique_overlap_and_hidden_motion_never_double_count(self):
        before=blank()
        after=blank()
        # One upper tire pixel, one middle saddle pixel, one lower
        # tire/rim double pixel, one interior change hidden by frame.
        before["fork_and_frame"]=mask((15,4))
        after["fork_and_frame"]=mask((15,4))
        after["pedals"]=mask((15,4))
        after["tire"]=mask((3,2),(7,38))
        after["rim_and_hub"]=mask((7,38))
        after["saddle"]=mask((4,20))
        part=partition_2026_visible_motion(before,after)
        union=part["whole_visible_2026_union_xor"]
        self.assertEqual(sum(union),3)
        self.assertEqual(union[4*64+15],0)
        disjoint=part["disjoint_candidate_motion_masks"]
        self.assertEqual(sum(disjoint["tire"]),1)
        self.assertEqual(sum(disjoint["saddle"]),1)
        self.assertEqual(sum(disjoint["overlapping_2026_parts_unattributed"]),1)
        self.assertEqual(sum(sum(q) for q in disjoint.values()),3)
        # Two original changed pixels matched, a third source lower
        # pixel missed; ambiguous model overlap is one independent FP.
        result=source_vs_model_motion_regions(mask(),mask((3,2),(4,20),(8,38)),
                                              before,after)
        self.assertEqual(result["source_vs_2026_motion_tp_fp_fn"],
                         {"tp":2,"fp":1,"fn":1})
        bands=result["source_image_bands"]
        self.assertEqual([bands[name]["original_changed_pixel_instances"]
                          for name in ("upper_y0_14","middle_y15_26","lower_y27_63")],
                         [1,1,1])
        upper=bands["upper_y0_14"]["2026_disjoint_visible_parent_motion"]
        self.assertEqual(upper["tire"]["source_changed_pixel_instances_explained"],1)
        lower=bands["lower_y27_63"]["2026_disjoint_visible_parent_motion"]
        self.assertEqual(lower["overlapping_2026_parts_unattributed"][
            "candidate_change_absent_from_source"],1)
        self.assertTrue(result["2026_synthetic_part_names_are_not_original_1994_anatomy"])

    def test_empty_and_corrupted_original_masks_rejected(self):
        z=blank()
        out=source_vs_model_motion_regions(mask(),mask(),z,z)
        self.assertEqual(out["source_vs_2026_motion_iou"],1.)
        self.assertEqual(out["source_vs_2026_motion_tp_fp_fn"],
                         {"tp":0,"fp":0,"fn":0})
        with self.assertRaisesRegex(ValueError,"five authentic"):
            partition_2026_visible_motion({},z)
        with self.assertRaisesRegex(ValueError,"five authentic"):
            partition_2026_visible_motion({**z,"tire":bytes([2])+bytes(4095)},z)
        with self.assertRaisesRegex(ValueError,"two exact"):
            source_vs_model_motion_regions(bytes([2])+bytes(4095),mask(),z,z)
        with self.assertRaisesRegex(ValueError,"two exact"):
            source_vs_model_motion_regions(mask(),bytes(4095),z,z)


if __name__=="__main__":
    unittest.main()
