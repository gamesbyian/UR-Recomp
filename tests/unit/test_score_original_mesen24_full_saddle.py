"""All 24 exact original two-player Mesen ticks, distinct source silhouettes."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art.score_original_mesen24_full_saddle import (
    SCHEMA,TICKS,ARMS,SADDLE_TRIALS,aggregate_original_timeline,main,analyze,
)


class AllOriginalSourceSaddleLeanTests(unittest.TestCase):
    def test_all_original_ticks_and_predeclared_controls_are_fixed(self):
        self.assertEqual((len(TICKS),TICKS[0],TICKS[-1]),(24,1601,1624))
        self.assertEqual(SADDLE_TRIALS,(
            ("axle_root_saddle_neutral",0.),
            ("axle_root_saddle_plus15",15.),
            ("axle_root_saddle_minus15",-15.)))
        self.assertEqual(set(ARMS),{"original_source_2d_rotation",
                                    *(name for name,_ in SADDLE_TRIALS)})
        self.assertIn("ALL24",SCHEMA) if "ALL24" in SCHEMA else self.assertIn("24TICK",SCHEMA)

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
