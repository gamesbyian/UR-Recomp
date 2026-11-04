"""All 24 exact original two-player Mesen ticks, distinct source silhouettes."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art.score_original_mesen24_full_saddle import (
    SCHEMA,TICKS,ARMS,BASELINE_ARMS,SADDLE_TRIALS,CRANK_PHASE_CONTROLS,
    drive_for_original_phase_index,aggregate_original_timeline,main,analyze,
    summary_for_exact_original_source,check_exact_source_evidence,
)


class AllOriginalSourceSaddleLeanTests(unittest.TestCase):
    def test_all_original_ticks_and_predeclared_controls_are_fixed(self):
        self.assertEqual((len(TICKS),TICKS[0],TICKS[-1]),(24,1601,1624))
        self.assertEqual(SADDLE_TRIALS,(
            ("axle_root_saddle_neutral",0.),
            ("axle_root_saddle_plus15",15.),
            ("axle_root_saddle_minus15",-15.)))
        self.assertEqual(set(BASELINE_ARMS),{"original_source_2d_rotation",
                                    *(name for name,_ in SADDLE_TRIALS)})
        self.assertIn("ALL24",SCHEMA) if "ALL24" in SCHEMA else self.assertIn("24TICK",SCHEMA)
        self.assertEqual(CRANK_PHASE_CONTROLS,(
            ("axle_root_saddle_neutral_crank_plus15perphase",0.,15.),
            ("axle_root_saddle_plus15_crank_plus15perphase",15.,15.),
            ("axle_root_saddle_plus15_crank_minus15perphase",15.,-15.)))
        self.assertEqual(len(ARMS),7)
        self.assertEqual(set(ARMS),set(BASELINE_ARMS)|{x for x,_,_ in CRANK_PHASE_CONTROLS})
        for phase in range(24):
            self.assertEqual(drive_for_original_phase_index(phase,15.),15.*phase)
            self.assertEqual(drive_for_original_phase_index(phase,-15.),-15.*phase)
        for phase,step in ((-1,15.),(24,15.),(1.5,15.),
                           (True,15.),(9,14.),(9,float("nan")),(9,True)):
            with self.subTest(phase=phase,step=step),self.assertRaises(ValueError):
                drive_for_original_phase_index(phase,step)

    def test_one_vote_per_unique_original_shape_not_23_repeated_snapshots(self):
        first=bytes([1])+bytes(4095)
        second=bytes([0,1])+bytes(4094)
        original={t:{"alpha":first if t<1624 else second} for t in TICKS}
        predicted={}
        for t in TICKS:
            predicted[t]={
                "original_source_2d_rotation":original[t]["alpha"],
                "axle_root_saddle_neutral":first,
                "axle_root_saddle_plus15":first,
                "axle_root_saddle_minus15":second,
                "axle_root_saddle_neutral_crank_plus15perphase":first,
                "axle_root_saddle_plus15_crank_plus15perphase":first,
                "axle_root_saddle_plus15_crank_minus15perphase":second,
            }
        report=aggregate_original_timeline(original,predicted)
        self.assertEqual(len(report["original_unique_binary_source_alpha_shape_sha256_to_ticks"]),2)
        one=report["arms"]["axle_root_saddle_neutral"]
        self.assertEqual(one["original_chronological_source_frame_count"],24)
        self.assertEqual(one["original_unique_64px_binary_shape_count"],2)
        self.assertAlmostEqual(one["source_frame_pooled_alpha_iou"],23/25,places=8)
        self.assertEqual(one["source_unique_shape_equal_vote_mean_alpha_iou"],0.5)
        self.assertEqual(one["source_actual_timeline_edge_count"],23)
        self.assertEqual(one["source_actual_23_consecutive_edge_change_tp_fp_fn"],
                         {"tp":0,"fp":0,"fn":2})
        self.assertEqual(one["source_actual_23_consecutive_edge_change_pooled_iou"],0.)
        best=report["arms"]["original_source_2d_rotation"]
        self.assertEqual(best["source_frame_pooled_alpha_iou"],1.)
        self.assertEqual(best["source_unique_shape_equal_vote_mean_alpha_iou"],1.)
        self.assertEqual(best["source_actual_23_consecutive_edge_change_pooled_iou"],1.)
        with self.assertRaisesRegex(ValueError,"complete original"):
            aggregate_original_timeline({1601:original[1601]},predicted)
        with self.assertRaisesRegex(ValueError,"complete original"):
            aggregate_original_timeline(original,{1601:predicted[1601]})

    def test_reject_unexpected_source_alpha_and_candidate_control(self):
        original={t:{"alpha":bytes([1])+bytes(4095)} for t in TICKS}
        pred={t:{key:bytes([1])+bytes(4095) for key in ARMS} for t in TICKS}
        original[1604]={"alpha":bytes([2])+bytes(4095)}
        with self.assertRaisesRegex(ValueError,"malformed"):
            aggregate_original_timeline(original,pred)
        original[1604]={"alpha":bytes([1])+bytes(4095)}
        del pred[1604]["axle_root_saddle_plus15"]
        with self.assertRaisesRegex(ValueError,"complete original"):
            aggregate_original_timeline(original,pred)

    def test_actual_sha_locked_original_48_frame_saddle_baseline(self):
        """Freeze exact source+current GLB experimental receipt in GHA.

        Run 41892738666 on prior implementation head 68439277: the extra
        saddle improves static 2D shape but does not recover source motion.
        """
        # These are descriptive receipt constants, not a synthetic source
        # simulator or a second full OpenSCAD source run in the unit suite.
        observed={
            "blue":{
                "original_source_2d_rotation":(19,.82069294,.82528384,.09025788),
                "axle_root_saddle_neutral":(19,.50895141,.51233488,.0203252),
                "axle_root_saddle_plus15":(19,.55176933,.55443157,.01771117),
                "axle_root_saddle_minus15":(19,.48967116,.49233279,.02040816),
            },
            "red":{
                "original_source_2d_rotation":(23,.82181906,.82604553,.10564399),
                "axle_root_saddle_neutral":(23,.55119306,.55143555,.01780822),
                "axle_root_saddle_plus15":(23,.5819645,.58231923,.01641587),
                "axle_root_saddle_minus15":(23,.52993562,.53053689,.01783265),
            },
        }
        for role,arms in observed.items():
            with self.subTest(role=role):
                self.assertEqual(set(arms),set(BASELINE_ARMS))
                for _,(unique,pooled,equal,edge) in arms.items():
                    self.assertEqual(unique,19 if role=="blue" else 23)
                    self.assertTrue(0<edge<pooled<equal+.01<1)
                neutral=arms["axle_root_saddle_neutral"]
                improved=arms["axle_root_saddle_plus15"]
                original=arms["original_source_2d_rotation"]
                self.assertGreater(improved[1],neutral[1])
                self.assertGreater(improved[2],neutral[2])
                self.assertLess(improved[3],neutral[3])
                self.assertLess(improved[1],original[1])
                self.assertLess(improved[3],original[3])
        self.assertEqual(observed["blue"]["axle_root_saddle_plus15"],
                         (19,.55176933,.55443157,.01771117))
        self.assertEqual(observed["red"]["axle_root_saddle_plus15"],
                         (23,.5819645,.58231923,.01641587))

    def test_sha_authenticated_original_real_glb_golden_detects_any_drift(self):
        path=Path(__file__).resolve().parents[2]/(
            "analysis/data/racer-original-mesen24-saddle-temporal-evidence-20261104.json")
        golden=json.loads(path.read_text())
        self.assertEqual(golden["schema"],
                         "UR-ART4K-EXACT-ORIGINAL-MESEN24-SADDLE-TEMPORAL-EVIDENCE/1")
        producer=golden["producer"]
        record={
            "schema":SCHEMA,
            "source_exact_original_Mesen24_archive_sha256":
                producer["original_Mesen24_archive_sha256"],
            "source_exact_ROM_phase_orientation_report_sha256":
                producer["original_pose_report_sha256"],
            "source_exact_64_angle_report_sha256":
                producer["original_axis_sha256"],
            "source_unchanged_7_6_camera_sha256":
                producer["provisional_camera_sha256"],
            "current_source_authored_2026_SCAD_sha256":
                producer["current_2026_authored_SCAD_sha256"],
            "original_1994_3D_mesh_camera_joint_or_source_materials_recovered":False,
            "owner_2026_character_art_likeness_approved":False,
            "original_source_per_role":{},
        }
        for role,arms in golden["reported_per_role"].items():
            record["original_source_per_role"][role]={
                "original_24_tick_samples":{str(t):{"authentic":True} for t in TICKS},
                "arms":{
                    arm:{
                        "original_chronological_source_frame_count":24,
                        "source_actual_timeline_edge_count":23,
                        "original_unique_64px_binary_shape_count":row["unique_shapes"],
                        "source_frame_pooled_alpha_iou":row["chronological_pooled_iou"],
                        "source_unique_shape_equal_vote_mean_alpha_iou":
                            row["unique_shape_equal_vote_mean_iou"],
                        "source_actual_23_consecutive_edge_change_pooled_iou":
                            row["real_23_tick_edge_change_pooled_iou"],
                    } for arm,row in arms.items()
                },
            }
        self.assertEqual(summary_for_exact_original_source(record),
                         golden["reported_per_role"])
        check_exact_source_evidence(record,golden)
        import copy
        bad=copy.deepcopy(record)
        bad["original_source_per_role"]["red"]["arms"][
            "axle_root_saddle_plus15"]["source_frame_pooled_alpha_iou"]+=.0001
        with self.assertRaisesRegex(ValueError,"scores drifted"):
            check_exact_source_evidence(bad,golden)
        bad=copy.deepcopy(record)
        bad["source_unchanged_7_6_camera_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance changed"):
            check_exact_source_evidence(bad,golden)
        bad=copy.deepcopy(record)
        del bad["original_source_per_role"]["blue"]["original_24_tick_samples"]["1601"]
        with self.assertRaisesRegex(ValueError,"all 24 authentic"):
            check_exact_source_evidence(bad,golden)
        tampered=copy.deepcopy(golden)
        tampered["producer"]["original_art_likeness_approved"]=True
        with self.assertRaisesRegex(ValueError,"3D/art likeness"):
            check_exact_source_evidence(record,tampered)

    def test_cli_no_replace_after_all_original_model_diagnostics(self):
        record={"schema":SCHEMA,"original_source_per_role":{
            "blue":{"arms":{"test":{"source_frame_pooled_alpha_iou":1.0}}},
            "red":{"arms":{"test":{"source_frame_pooled_alpha_iou":1.0}}}}}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            inp=[]
            for index in range(4):
                file=root/f"input-{index}.bin";file.write_bytes(b"fixture")
                inp.append(str(file))
            dest=root/"result.json"
            argv=["prog","--source-zip",inp[0],"--pose-report",inp[1],
                  "--axis-report",inp[2],"--camera",inp[3],
                  "--verified-exports",str(root),"--out",str(dest)]
            with patch("sys.argv",argv),patch(
                    "tools.art.score_original_mesen24_full_saddle.analyze",
                    return_value=record),patch("sys.stdout",new_callable=io.StringIO) as output:
                main()
                self.assertIn("OK ART4K_REAL_2026_SADDLE_ALL24_SOURCE_MOTION",
                              output.getvalue())
            self.assertEqual(json.loads(dest.read_text()),record)
            with patch("sys.argv",argv),patch(
                    "tools.art.score_original_mesen24_full_saddle.analyze",
                    return_value=record),patch("sys.stdout",new_callable=io.StringIO):
                with self.assertRaises(FileExistsError):
                    main()


if __name__=="__main__":
    unittest.main()
