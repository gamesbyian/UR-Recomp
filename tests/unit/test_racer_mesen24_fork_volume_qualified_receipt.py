"""Long-lived audit of exact authenticated 2P×24 original-vs-one-GLB scores.

The source artifact and old experimental stack can expire or change. These
numbers preserve the observed original-CI outcome, without copying original
ROM pixels or claiming original 1994 anatomy, camera or art approval.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/"analysis/data/racer-art4k-mesen24-fork-crown-qualified-20261105.json"
METRICS=("source_frame_pooled_alpha_iou",
         "source_unique_shape_equal_vote_mean_alpha_iou",
         "source_actual_23_consecutive_edge_change_pooled_iou")
PINS={
 "source_head_sha":"35e28238ce308a256cf2463682b108a9580f2cae",
 "source_USA_ROM_sha256":"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
 "source_original_Mesen24_zip_sha256":"28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6",
 "source_2026_SCAD_sha256":"e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984",
 "source_provisional_7_6_camera_sha256":"1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028",
}


class FrozenOriginalForkVolumeEvidenceTests(unittest.TestCase):
    def test_original_two_roles_28_arms_and_sha_evidence_pins(self):
        report=json.loads(FILE.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"],
                         "UR-ART4K-REAL-MESEN24-FORK-CROWN-QUALIFIED-SOURCE-SCORE/1")
        for key,value in PINS.items():
            self.assertEqual(report[key],value,key)
        self.assertEqual(report["source_qualification_run_id"],42099979791)
        self.assertEqual(report["source_exact_job_id"],127499918916)
        self.assertEqual(report["source_artifact_id"],13449649356)
        self.assertEqual(report["source_historical_existing_controls_count"],24)
        self.assertEqual(report["source_new_crown_controls_count"],4)
        self.assertIs(report["source_historical_controls_exact_match_against_previous_experiment"],True)
        self.assertEqual((report["source_original_chronological_frame_count_per_racer"],
                          report["source_original_true_consecutive_edges_per_racer"]),(24,23))
        self.assertIs(report["source_1994_3d_mesh_camera_material_or_physical_width_recovered"],False)
        self.assertIs(report["owner_likeness_approved"],False)
        self.assertIs(report["shipping_art_approved"],False)
        roles=report["source_all28_named_controls_per_role"]
        self.assertEqual(set(roles),{"blue","red"})
        self.assertEqual(set(roles["blue"]),set(roles["red"]))
        self.assertEqual(len(roles["blue"]),28)
        for role,expected_unique in (("blue",19),("red",23)):
            for arm,row in roles[role].items():
                with self.subTest(role=role,arm=arm):
                    self.assertEqual(row["original_unique_64px_binary_shape_count"],
                                     expected_unique)
                    self.assertEqual(set(row),{*METRICS,"original_unique_64px_binary_shape_count"})
                    for metric in METRICS:
                        self.assertTrue(0<=row[metric]<=1)

    def test_signed_six_objective_deltas_and_wheel_drive_matched_control(self):
        record=json.loads(FILE.read_text(encoding="utf-8"))
        roles=record["source_all28_named_controls_per_role"]
        deltas=record["source_new_crown_same_mechanical_control_deltas"]
        self.assertEqual(len(deltas),4)
        for arm,entry in deltas.items():
            baseline=entry["matched_control"]
            self.assertTrue(baseline.startswith("axle_root_saddle_world_level_"))
            self.assertEqual(arm.split("_")[-3:],baseline.split("_")[-3:])
            from_current=[round(roles[r][arm][m]-roles[r][baseline][m],8)
                          for r in ("blue","red") for m in METRICS]
            self.assertEqual([round(x,8) for x in entry["signed_source_six_objective_delta"]],
                             from_current)
            self.assertEqual(entry["strictly_dominates_matched_control"],
                             all(x>=0 for x in from_current) and any(x>0 for x in from_current))
            self.assertEqual(entry["dominated_by_matched_control"],
                             all(x<=0 for x in from_current) and any(x<0 for x in from_current))
            self.assertFalse(entry["strictly_dominates_matched_control"])
        self.assertTrue(all(entry["dominated_by_matched_control"]
                            for arm,entry in deltas.items() if "narrow090" in arm))
        self.assertTrue(all(not entry["dominated_by_matched_control"]
                            for arm,entry in deltas.items() if "full110" in arm))


if __name__=="__main__":
    unittest.main()
