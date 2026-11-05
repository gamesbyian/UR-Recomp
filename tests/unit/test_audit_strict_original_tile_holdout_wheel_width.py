"""ROM-free adversarial tests for retrospective tile-disjoint wheel-width audit."""
from pathlib import Path
import unittest

from tools.art.audit_strict_original_tile_holdout_wheel_width import (
    audited_retrospective, compare_fixed_2d_masks, decimal_score,
    git_blob_sha, read_frozen_file,
    WHEEL_BLOB, LOOKUP_BLOB, FROZEN_BLOB,
)

A="a"*64
B="b"*64
C="c"*64
D="d"*64
E="e"*64
F="f"*64


def scores():
    return {D:{"one_x_mask_iou":0.20,"one_point_one_x_mask_iou":0.30},
            E:{"one_x_mask_iou":0.31,"one_point_one_x_mask_iou":0.30},
            F:{"one_x_mask_iou":0.30,"one_point_one_x_mask_iou":0.35}}


class OriginalStrictWheelWidthTests(unittest.TestCase):
    def test_genuine_git_blob_sha_not_plain_hash(self):
        self.assertEqual(git_blob_sha(b"test"),
                         "30d74d258442c7c65512eafab474568dd706c430")
        self.assertNotEqual(git_blob_sha(b"test"),git_blob_sha(b"test\\n"))

    def test_frozen_membership_scoring_and_negative_control(self):
        report=compare_fixed_2d_masks({A:D,B:E,C:F},[A,B,C],[A,C],scores())
        self.assertEqual(report["all_19_original_source_shapes"]["independent_original_2d_source_planes"],3)
        self.assertEqual(report["strict_six_source_tile_disjoint_shapes"]["independent_original_2d_source_planes"],2)
        self.assertEqual(report["strict_six_source_tile_disjoint_shapes"]["width_1_10_wins"],2)
        self.assertEqual(report["all_19_original_source_shapes"]["width_1_10_losses"],1)
        self.assertEqual(report["strict_six_source_tile_disjoint_shapes"]["width_1_10_minus_1_00_mean_delta_iou"],
                         "0.07500000")
        self.assertEqual(sum(r["strictly_tile_disjoint_from_fit"] for r in report["per_original_2d_source_index_plane"]),2)

    def test_reject_missing_duplicate_and_extra_binary_scores(self):
        for malformed in ({D:scores()[D],E:scores()[E]}, {**scores(), "0"*64:scores()[D]}):
            with self.assertRaisesRegex(ValueError,"previously scored"):
                compare_fixed_2d_masks({A:D,B:E,C:F},[A,B,C],[A],malformed)
        with self.assertRaisesRegex(ValueError,"identity invalid"):
            compare_fixed_2d_masks({A:D,B:D,C:F},[A,B,C],[A],scores())
        with self.assertRaisesRegex(ValueError,"identity invalid"):
            compare_fixed_2d_masks({A:D,B:E,C:F},[A,B,C],[A,"1"*64],scores())

    def test_reject_nonfinite_scores_and_missing_hypothesis(self):
        for value in ("NaN","Infinity",-0.1,1.1,True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError,"source"):
                    compare_fixed_2d_masks({A:D,B:E,C:F},[A,B,C],[A],{
                        **scores(),D:{"one_x_mask_iou":value,"one_point_one_x_mask_iou":0.2}})
        with self.assertRaisesRegex(ValueError,"two source scores"):
            compare_fixed_2d_masks({A:D,B:E,C:F},[A,B,C],[A],{
                **scores(),D:{"one_x_mask_iou":0.2}})

    def test_actual_repo_sha_gated_19_and_six_retrospective(self):
        root=Path(__file__).resolve().parents[2]
        wheel=read_frozen_file(root/"analysis/data/racer-wheel-x-genuine-rom-holdout-20261101.json",
                               WHEEL_BLOB)
        lookup=read_frozen_file(root/"analysis/data/racer-original-index-lookup-20261102.json",
                                LOOKUP_BLOB)
        frozen=read_frozen_file(root/"analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json",
                                FROZEN_BLOB)
        report=audited_retrospective(wheel,lookup,frozen)
        all19=report["all_19_original_source_shapes"]
        strict=report["strict_six_source_tile_disjoint_shapes"]
        self.assertEqual(all19["independent_original_2d_source_planes"],19)
        self.assertEqual(strict["independent_original_2d_source_planes"],6)
        self.assertEqual(all19["width_1_00_mean_iou"],"0.38192089")
        self.assertEqual(all19["width_1_10_mean_iou"],"0.41491323")
        self.assertEqual(strict["width_1_00_mean_iou"],"0.38543972")
        self.assertEqual(strict["width_1_10_mean_iou"],"0.41730258")
        self.assertEqual(strict["width_1_10_minus_1_00_mean_delta_iou"],"0.03186286")
        self.assertEqual(strict["width_1_10_wins"],6)
        self.assertEqual(strict["width_1_10_losses"],0)
        self.assertFalse(report["original_sprite_to_experimental_GLb_pose_mapping_verified"])
        self.assertTrue(report["strict_six_selection_is_retrospective_and_not_new_blind_3d_poses"])


if __name__=="__main__":
    unittest.main()
