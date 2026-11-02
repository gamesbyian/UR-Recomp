"""ROM-free unit tests for the five-GLB original-ROM pose matrix reducer."""
import copy
import unittest
from tools.art.evaluate_original_racer_five_pose_matrix import validate_matrix_rows, POSES


class RealOriginalPoseMatrixTests(unittest.TestCase):
    def example(self):
        return [{
            "source_binary_mask_sha256": h,
            "unpaired_pose_scores": {p: {"mask_iou": .5} for p in POSES},
            "unpaired_best_fit_pose": "bank",
        } for h in ("a"*64, "b"*64)]

    def test_complete_unique_original_masks(self):
        rows = self.example()
        self.assertTrue(validate_matrix_rows(rows, {"a"*64: None, "b"*64: None}))

    def test_missing_or_duplicated_masks(self):
        rows = self.example()
        with self.assertRaises(ValueError):
            validate_matrix_rows(rows[:1], {"a"*64: None, "b"*64: None})
        rows[1]["source_binary_mask_sha256"] = "a"*64
        with self.assertRaises(ValueError):
            validate_matrix_rows(rows, {"a"*64: None, "b"*64: None})

    def test_missing_pose_or_malformed_row(self):
        for mutation in ("missing", "nan", "outside", "not_dict", "wrong_best"):
            rows = self.example()
            if mutation == "missing":
                del rows[0]["unpaired_pose_scores"]["stunt"]
            elif mutation == "nan":
                rows[0]["unpaired_pose_scores"]["bank"]["mask_iou"] = float("nan")
            elif mutation == "outside":
                rows[0]["unpaired_pose_scores"]["bank"]["mask_iou"] = 2
            elif mutation == "not_dict":
                rows[0] = None
            else:
                rows[0]["unpaired_best_fit_pose"] = "invented_1994_pose"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_matrix_rows(rows, {"a"*64: None, "b"*64: None})


if __name__ == "__main__":
    unittest.main()
