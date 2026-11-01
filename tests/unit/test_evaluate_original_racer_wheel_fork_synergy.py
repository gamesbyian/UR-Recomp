"""No-ROM/GLB synthetic source-family contracts for crossed ART-4K shape research."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "art4k_source_crossed",ROOT/"tools/art/evaluate_original_racer_wheel_fork_synergy.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def data():
    masks=[f"{i:064x}" for i in range(35)]
    rows={}
    for i,h in enumerate(masks):
        originals=.30+.001*i
        scores={
            module.FIRST: originals,
            module.WHEEL: originals+.04,
            module.FORK: originals+.01,
            module.BOTH: originals+.05,
        }
        rows[h]={k:{"mask_iou":v,
                    "boundary_chamfer_mean_physical_px":2.+.05*j}
                 for j,(k,v) in enumerate(scores.items())}
    partition={
        "fit_binary_shas":masks[:16],
        "withheld_binary_shas":masks[16:],
    }
    return rows,partition


class CrossedSourceShapeTests(unittest.TestCase):
    def test_historical_frozen_exact_two_source_GLb_SHA(self):
        self.assertEqual(module.WIDTHS,(1.0,1.1))
        self.assertEqual(set(module.GLBS),{1.0,1.4})
        self.assertEqual(module.GLBS[1.0],
            "ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04")
        self.assertEqual(module.GLBS[1.4],
            "5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53")

    def test_one_original_shape_one_vote_and_true_crossed_interaction(self):
        rows,split=data()
        result=module.summarizes(rows,split)
        held=result["previously_SHA_disconnected_original_2D_mask_family"]
        self.assertEqual(held["independent_original_binary_mask_count"],19)
        combo=held["candidates"][module.BOTH]
        self.assertEqual(combo["wins_vs_wheel_only"],19)
        self.assertEqual(combo["losses_vs_wheel_only"],0)
        self.assertEqual(combo["mean_IoU_delta_vs_wheel_only"],.01)
        self.assertEqual(combo["mean_IoU_delta_vs_unmodified"],.05)
        self.assertEqual(result["source_first_fit_connected_component"]["independent_original_binary_mask_count"],16)
        self.assertTrue(result["withheld_source_masks_are_not_proven_independent_1994_3D_views"])

    def test_invalid_source_partitions_and_missing_components_refused(self):
        rows,part=data()
        part["withheld_binary_shas"][0]=part["fit_binary_shas"][0]
        with self.assertRaisesRegex(ValueError,"invalid binary-mask"):
            module.summarizes(rows,part)
        rows,part=data()
        del rows["0"*64][module.BOTH]
        with self.assertRaises(ValueError):
            module.summarizes(rows,part)
        rows,part=data()
        del rows["0"*64]
        with self.assertRaises(ValueError):
            module.summarizes(rows,part)

    def test_nonfinite_or_out_of_range_2D_fit_rejected(self):
        for bad in (math.nan,math.inf,-.001,1.1,True):
            rows,part=data()
            rows["0"*64][module.BOTH]["mask_iou"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                module.summarizes(rows,part)
        rows,part=data()
        rows["0"*64][module.WHEEL]["boundary_chamfer_mean_physical_px"]=math.inf
        with self.assertRaises(ValueError):
            module.summarizes(rows,part)


if __name__=="__main__":
    unittest.main()
