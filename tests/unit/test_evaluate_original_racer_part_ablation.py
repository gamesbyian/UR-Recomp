"""ROM-free regression of actual five-part GLB silhouette attribution."""
import importlib.util
from pathlib import Path
import unittest
try:
    import numpy as np
except ImportError:
    np=None

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "art4k_parts",ROOT/"tools/art/evaluate_original_racer_part_ablation.py")
model=importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class SourcePartLeaveOneOutTests(unittest.TestCase):
    def test_exact_source_parts_and_original_GLb_SHA_are_frozen(self):
        self.assertEqual(len(model.PARTS),5)
        self.assertEqual(model.source_owned_part("saddle__material_1"),"saddle")
        self.assertEqual(model.source_owned_part("rim_and_hub__material_4"),"rim_and_hub")
        self.assertEqual(len(model.ACTUAL_GLB_SHA),2)
        self.assertEqual(model.ACTUAL_GLB_SHA["unchanged"],
            "ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04")
        self.assertEqual(model.ACTUAL_GLB_SHA["wheel1p1_fork1p4"],
            "5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53")
        for node in ("saddle","fork","wheel__material_0","tire__material_5junk"):
            with self.subTest(node=node),self.assertRaises(ValueError):
                model.source_owned_part(node)

    @unittest.skipIf(np is None,"numpy is an optional original-source art dependency")
    def test_true_and_false_positive_unique_source_part_pixels(self):
        source=np.zeros((64,64),dtype=np.uint8)
        full=np.zeros_like(source)
        absent=np.zeros_like(source)
        source[6,6]=1;source[7,7]=1
        full[6,6]=1;full[7,7]=1;full[8,8]=1
        absent[6,6]=1
        row=model.lost_pixel_stats(source,full,absent)
        self.assertEqual(row["source_owned_unique_model_pixels_removed"],2)
        self.assertEqual(row["original_true_positive_pixels_lost"],1)
        self.assertEqual(row["original_false_positive_pixels_removed"],1)
        self.assertEqual(row["original_source_false_negative_pixels_remaining"],0)
        self.assertEqual(row["whole_model_source_mask_iou"],round(2/3,8))
        self.assertEqual(row["without_part_source_mask_iou"],.5)

    @unittest.skipIf(np is None,"numpy is an optional original-source art dependency")
    def test_non_subtractive_2D_part_or_invalid_masks_rejected(self):
        original=np.zeros((64,64),dtype=np.uint8)
        original[0,0]=1
        full=original.copy()
        removed=original.copy()
        removed[0,1]=1
        with self.assertRaises(ValueError):
            model.lost_pixel_stats(original,full,removed)
        with self.assertRaises(ValueError):
            model.lost_pixel_stats(original,full,np.zeros((64,64),dtype=np.uint8))
        with self.assertRaises(ValueError):
            model.lost_pixel_stats(original,full[:8],full)

    def test_one_original_shape_one_vote_and_part_importance(self):
        keys=["a"*64,"b"*64]
        per={}
        for k in keys:
            per[k]={"parts":{part:{
                "original_true_positive_pixels_lost":4,
                "original_false_positive_pixels_removed":5,
                "whole_model_source_mask_iou":.5,
                "without_part_source_mask_iou":.6 if part=="saddle" else .4,
            } for part in model.PARTS}}
        result=model.summarize_family(per,keys)
        self.assertEqual(result["saddle"]["source_independent_binary_masks"],2)
        self.assertEqual(result["saddle"]["original_false_positive_pixels_removed_across_masks"],10)
        self.assertEqual(result["saddle"]["masks_better_without_part"],2)
        self.assertEqual(result["saddle"]["mean_iou_without_part_minus_full"],.1)
        self.assertEqual(result["tire"]["masks_worse_without_part"],2)
        for invalid in ([],keys+keys[:1],keys+["c"*64]):
            with self.assertRaises(ValueError):
                model.summarize_family(per,invalid)


if __name__=="__main__":
    unittest.main()
