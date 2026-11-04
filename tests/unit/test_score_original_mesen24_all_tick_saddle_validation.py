"""Actual 24-tick two-player source temporal benchmark, frozen 2026 GLB pose laws."""
import unittest
from tools.art.score_original_mesen24_all_tick_saddle_validation import (
    TICKS,ARMS,PRIOR_EIGHT_TICK_POOLED,change_plane,pooled_binary_metrics,SCHEMA,
)


class FullOriginalMesenSaddleMotionTests(unittest.TestCase):
    def test_source_timeline_and_frozen_old_eight_tick_oracles(self):
        self.assertEqual(TICKS,tuple(range(1601,1625)))
        self.assertEqual(len(TICKS)-1,23)
        self.assertEqual(len(ARMS),7)
        self.assertEqual(PRIOR_EIGHT_TICK_POOLED["blue"]
                         ["wheel_axle_root_saddle_lean_plus15"],0.56812169)
        self.assertEqual(PRIOR_EIGHT_TICK_POOLED["red"]
                         ["wheel_axle_root_saddle_lean_plus15"],0.58201058)
        self.assertEqual(PRIOR_EIGHT_TICK_POOLED["blue"]
                         ["source_original_2d_rotation"],0.83754513)
        self.assertEqual(PRIOR_EIGHT_TICK_POOLED["red"]
                         ["source_original_2d_rotation"],0.82731214)
        self.assertIn("SADDLE-TEMPORAL/1",SCHEMA)

    def test_true_chronological_change_mask_not_equality_mask(self):
        a=bytearray(4096);b=bytearray(4096)
        a[2]=1;a[3]=1
        b[2]=1;b[4]=1
        change=change_plane(bytes(a),bytes(b))
        self.assertEqual(sum(change),2)
        self.assertEqual(change[2],0)
        self.assertEqual(change[3],1)
        self.assertEqual(change[4],1)
        self.assertEqual(change_plane(bytes(a),bytes(a)),bytes(4096))
        with self.assertRaises(ValueError):
            change_plane(bytes(a),b"broken")

    def test_same_source_and_candidate_y_bands_add_to_whole(self):
        first=bytearray(4096)
        first[3*64+3]=1;first[22*64+5]=1;first[32*64+8]=1
        second=bytearray(4096)
        second[3*64+3]=1;second[22*64+6]=1;second[32*64+8]=1
        third=bytearray(4096)
        third[3*64+3]=1;third[22*64+5]=1;third[32*64+7]=1
        source={1601:bytes(first),1602:bytes(first)}
        pred={1601:bytes(second),1602:bytes(third)}
        r=pooled_binary_metrics(source,pred,(1601,1602))
        self.assertEqual(r["tp_fp_fn"],{"tp":3,"fp":3,"fn":3})
        self.assertEqual(r["source_frames"],2)
        self.assertEqual(r["fixed_source_y_bands"]["upper_y0_14"]["tp"],2)
        self.assertEqual(r["fixed_source_y_bands"]["middle_y15_26"]["tp"],0)
        self.assertEqual(r["fixed_source_y_bands"]["lower_y27_63"]["tp"],1)
        self.assertAlmostEqual(r["pooled_iou"],1/3,places=8)
        with self.assertRaises(ValueError):
            pooled_binary_metrics(source,pred,(1601,1603))
        with self.assertRaises(ValueError):
            pooled_binary_metrics(source,pred,(1601,1601))


if __name__=="__main__":
    unittest.main()
