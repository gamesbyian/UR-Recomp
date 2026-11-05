"""No-ROM tests for exact-receipt fixed 2D projection-handedness control."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tools.art.evaluate_original_mesen_live_reflection_control as reflection

from tools.art.evaluate_original_mesen_live_reflection_control import (
    evaluate, frozen_inputs, reflect64, lowest_alpha_x2, iou, SCHEMA,
)


class LiveReflectionControlTests(unittest.TestCase):
    def test_frozen_receipts_accept_crlf_checkout_but_reject_tampering(self):
        original = b'{"value": 1}\n'
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            receipt.write_bytes(original.replace(b"\n", b"\r\n"))
            with patch.object(reflection, "DATA", Path(tmp)), patch.object(
                reflection, "BLOBS", {receipt.name: reflection.git_blob_sha(original)}
            ):
                self.assertEqual(frozen_inputs(), ({"value": 1},))
                receipt.write_bytes(b'{"value": 2}\r\n')
                with self.assertRaisesRegex(ValueError, "frozen original/model receipt changed"):
                    frozen_inputs()

    def test_reflecting_both_source_and_registered_model_preserves_iou_and_anchor(self):
        source = bytearray(4096)
        model = bytearray(4096)
        for x, y in ((2, 10), (3, 10), (4, 20), (8, 20), (15, 45)):
            source[y * 64 + x] = 1
        for x, y in ((3, 10), (5, 10), (8, 20), (14, 45)):
            model[y * 64 + x] = 1
        a, b = bytes(source), bytes(model)
        self.assertEqual(iou(a, b), iou(reflect64(a), reflect64(b)))
        self.assertEqual(reflect64(reflect64(a)), a)
        self.assertEqual(lowest_alpha_x2(a) + lowest_alpha_x2(reflect64(a)), 126)
        with self.assertRaisesRegex(ValueError, "binary"):
            reflect64(a[:-1])
        with self.assertRaisesRegex(ValueError, "binary"):
            reflect64(bytes([2]) + a[1:])

    def test_actual_frozen_40_original_vs_real_glb_projection_result(self):
        report = evaluate(*frozen_inputs())
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["by_player"]["blue"], {
            "observations": 20,
            "shared_model_projection_mean_best_of_five_iou": .47986515,
            "red_model_projection_reflected_mean_best_of_five_iou": .47986515})
        self.assertEqual(report["by_player"]["red"], {
            "observations": 20,
            "shared_model_projection_mean_best_of_five_iou": .46554101,
            "red_model_projection_reflected_mean_best_of_five_iou": .48769263})
        self.assertEqual(report["all_40_raw_observations"], {
            "observations": 40,
            "shared_model_projection_mean_best_of_five_iou": .47270308,
            "red_model_projection_reflected_mean_best_of_five_iou": .48377889})
        self.assertEqual(report["unclassified_11_content_component_equal_weight"], {
            "groups": 11,
            "shared_model_projection_mean_best_of_five_iou": .49148426,
            "red_model_projection_reflected_mean_best_of_five_iou": .50544332,
            "improved_groups": 6, "worsened_groups": 1, "unchanged_groups": 4})
        self.assertFalse(report["source_to_2026_glb_pose_mapping_verified"])
        self.assertFalse(report["owner_likeness_approved"])

    def test_rejects_score_mutation_and_content_group_reassignment(self):
        b, s, r = frozen_inputs()
        bad = copy.deepcopy(b)
        bad["per_original_racer_frame_scores"][0]["fixed_camera_iou_by_GLb_pose"]["bank"] = -1
        with self.assertRaisesRegex(ValueError, "score"):
            evaluate(bad, s, r)
        bad = copy.deepcopy(r)
        bad["historical_source_content_components"][0]["members"][0] = [1601, "red"]
        with self.assertRaisesRegex(ValueError, "group"):
            evaluate(b, s, bad)
        bad = copy.deepcopy(s)
        bad["original_red_display_reflection_independently_source_screen_authenticated"] = False
        with self.assertRaisesRegex(ValueError, "evidence"):
            evaluate(b, bad, r)


if __name__ == "__main__":
    unittest.main()
