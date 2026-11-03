"""ROM-free source-role and score-integrity tests for live 20-frame / five-GLB diagnostics."""
import copy
import json
from pathlib import Path
import unittest

from tools.art.evaluate_original_mesen_live_pose_matrix import (
    POSES, TICKS, verified_roles, assigned_role, silhouette_iou, summarize_rows,
)


class LiveTwentyUnpairedPoseTests(unittest.TestCase):
    def test_original_historical_fit_withheld_strict_roles_are_never_overwritten(self):
        path = Path(__file__).resolve().parents[2] / (
            "analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json")
        data = json.loads(path.read_text())
        fit, withheld, strict = verified_roles(data)
        self.assertEqual((len(fit), len(withheld), len(strict)), (16, 19, 6))
        self.assertEqual(assigned_role(next(iter(fit)), (fit, withheld, strict)), "fit")
        self.assertEqual(assigned_role(next(iter(strict)), (fit, withheld, strict)),
                         "strict_withheld")
        self.assertEqual(assigned_role("0"*64, (fit, withheld, strict)),
                         "unclassified_live_source")
        corrupt = copy.deepcopy(data)
        corrupt["fit_original_index_plane_sha256"][0] = next(iter(strict))
        with self.assertRaisesRegex(ValueError, "leakage"):
            verified_roles(corrupt)

    def test_binary_silhouette_score_rejects_nonbinary_and_empty(self):
        a = bytes([1, 0, 1, 0]) + bytes(4092)
        b = bytes([1, 1, 0, 0]) + bytes(4092)
        self.assertEqual(silhouette_iou(a, b), 0.33333333)
        for bad in (bytes(4095), bytes([2])+bytes(4095)):
            with self.assertRaisesRegex(ValueError, "binary"):
                silhouette_iou(a, bad)
        with self.assertRaisesRegex(ValueError, "empty"):
            silhouette_iou(bytes(4096), bytes(4096))

    def test_exact_20_by_2_source_matrix_counts_and_no_pose_promotion(self):
        rows = []
        for tick in TICKS:
            for racer in ("blue", "red"):
                scores = {p: 0.2 for p in POSES}
                scores["upright"] = 0.4 if racer == "blue" else 0.3
                rows.append({"tick": tick, "racer": racer,
                             "frozen_source_role": "unclassified_live_source",
                             "unpaired_iou": scores, "unpaired_iou_winner": "upright"})
        result = summarize_rows(rows)
        self.assertEqual(result["original_2D_observations"], 40)
        self.assertEqual(result["unpaired_iou_winner_counts"]["upright"], 40)
        self.assertFalse(result["authentic_source_1994_pose_labels_verified"])
        tampered = copy.deepcopy(rows)
        tampered[1]["unpaired_iou_winner"] = "bank"
        with self.assertRaisesRegex(ValueError, "rank"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[1]["unpaired_iou"]["stunt"] = float("nan")
        with self.assertRaisesRegex(ValueError, "scores"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[2]["tick"] = tampered[1]["tick"]
        with self.assertRaisesRegex(ValueError, "census"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[0]["frozen_source_role"] = "auto-fit"
        with self.assertRaisesRegex(ValueError, "role"):
            summarize_rows(tampered)


if __name__ == "__main__":
    unittest.main()
