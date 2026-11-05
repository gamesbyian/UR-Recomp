"""ROM-free contract for frozen frame-mass disconnected-family source evaluation."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
path=ROOT/"tools/art/evaluate_original_racer_frame_mass_holdout.py"
spec=importlib.util.spec_from_file_location("source_frame_mass_35_holdout",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    shas=[f"{i:064x}" for i in range(35)]
    source={}
    for i,sha in enumerate(shas):
        scores={}
        for j,mass in enumerate(module.MASS_TRIALS):
            scores[str(mass)]={
                "mask_iou":float(.40 + .01*j if i<16 else .35 + .03*j),
                "boundary_chamfer_mean_physical_px":float(2-.1*j),
            }
        source[sha]={"scores":scores}
    split={
        "fit_binary_shas":shas[:16],
        "withheld_binary_shas":shas[16:],
        "fit_connected_windows":["first-1205-1220"],
        "withheld_connected_window_components":[["holdout"]],
    }
    return source,split


class FrameMassSourceHoldoutTests(unittest.TestCase):
    def test_only_preselected_real_source_mass_trials(self):
        self.assertEqual(module.MASS_TRIALS,(1.0,1.4,2.0))
        self.assertEqual(module.EXPECTED_SCAD_SHA,
                         "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984")
        self.assertEqual(module.UNMODIFIED_FIRST_FAMILY_MEAN,.57255469)

    def test_disconnected_original_masks_each_vote_once(self):
        scores,split=fixture()
        result=module.summaries_by_partition(scores,split)
        self.assertEqual(result["fit_connected_component"]["source_independent_binary_mask_count"],16)
        hold=result["previously_unseen_source_mask_holdout"]
        self.assertEqual(hold["source_independent_binary_mask_count"],19)
        self.assertEqual(hold["mass_trials"]["1.4"]["wins_over_unmodified_iou"],19)
        self.assertEqual(hold["mass_trials"]["1.0"]["wins_over_unmodified_iou"],0)
        self.assertEqual(hold["mass_trials"]["2.0"]["losses_to_unmodified_iou"],0)
        self.assertEqual(hold["mass_trials"]["1.4"]["mean_delta_iou_vs_unmodified"],.03)

    def test_no_leaky_or_forged_holdout_can_be_admitted(self):
        rows,split=fixture()
        split["withheld_binary_shas"][0]=split["fit_binary_shas"][0]
        with self.assertRaisesRegex(ValueError,"leaky"):
            module.summaries_by_partition(rows,split)
        rows,split=fixture()
        split["withheld_binary_shas"].pop()
        with self.assertRaises(ValueError):
            module.summaries_by_partition(rows,split)
        rows,split=fixture()
        del rows[next(iter(rows))]
        with self.assertRaises(ValueError):
            module.summaries_by_partition(rows,split)

    def test_cannot_hide_missing_mass_or_forge_nonfinite_source_2d_metrics(self):
        rows,split=fixture()
        del rows[next(iter(rows))]["scores"]["1.4"]
        with self.assertRaisesRegex(ValueError,"missing authentic"):
            module.summaries_by_partition(rows,split)
        for metric,bad in (("mask_iou",math.nan),
                           ("mask_iou",1.01),
                           ("boundary_chamfer_mean_physical_px",float("inf"))):
            rows,split=fixture()
            rows[next(iter(rows))]["scores"]["1.4"][metric]=bad
            with self.subTest(metric=metric,bad=bad),self.assertRaises(ValueError):
                module.summaries_by_partition(rows,split)


if __name__=="__main__":
    unittest.main()
