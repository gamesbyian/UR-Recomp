"""ROM-free original raster temporal motion witness acceptance."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "art4k_original_timeline",ROOT/"tools/art/audit_original_racer_temporal_motion.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def source(player, rgba, mask, contact, angle):
    return {
        "player":player,"source_rgba_sha256":rgba*64,
        "source_binary_mask_sha256":mask*64,
        "visible_bottom_alpha_anchor_x2_y2":contact,
        "source_painted_axis_angle_deg":angle,
    }


class OriginalRasterTimelineTests(unittest.TestCase):
    def test_realistic_held_frames_changing_alpha_and_paint(self):
        reps={
            "p1a":source("p1","1","a",[67,76],12),
            "p1b":source("p1","1","a",[67,76],12),
            "p1c":source("p1","2","a",[67,76],12.5),
            "p1d":source("p1","3","b",[69,74],8),
            "p2a":source("p2","4","c",[68,76],-2),
            "p2b":source("p2","5","d",[70,76],-2),
        }
        rows=[
            {"window":"first","guest_frame":1205,
             "representations":{"p1":"p1a","p2":"p2a"}},
            {"window":"first","guest_frame":1206,
             "representations":{"p1":"p1b","p2":"p2a"}},
            {"window":"first","guest_frame":1207,
             "representations":{"p1":"p1c","p2":"p2b"}},
            {"window":"first","guest_frame":1210,
             "representations":{"p1":"p1d","p2":"p2b"}},
        ]
        result=mod.frame_edges(rows,reps)
        self.assertEqual(result["registered_source_windows"],1)
        self.assertEqual(result["source_observed_player_frame_pairs"],6)
        self.assertEqual(result["actually_consecutive_original_guest_frame_pairs"],4)
        self.assertEqual(result["identical_source_rgba_holds"],3)
        self.assertEqual(result["source_binary_silhouette_changes"],2)
        self.assertEqual(result["source_paint_only_changes"],1)
        witness=result["windows"][0]
        p1=[e for e in witness["observed_original_source_transitions"]
            if e["player"]=="p1"]
        self.assertEqual([e["to_guest_frame"] for e in p1],[1206,1207,1210])
        self.assertEqual(p1[-1]["guest_frame_step"],3)
        self.assertFalse(p1[-1]["actually_adjacent_guest_frames"])
        self.assertEqual(p1[-1]["visible_bottom_alpha_anchor_delta_x2_y2"],[2,-2])
        self.assertEqual(p1[-1]["painted_axis_angle_delta_deg"],-4.5)
        self.assertFalse(p1[-1]["true_1994_3d_joint_or_camera_transition_identified"])

    def test_missing_player_cannot_be_bridged(self):
        reps={
            "a":source("p1","1","a",[67,76],0),
            "b":source("p1","2","b",[68,76],2),
            "x":source("p2","3","c",[69,76],2)
        }
        rows=[
            {"window":"second","guest_frame":1,"representations":{"p1":"a"}},
            {"window":"second","guest_frame":2,"representations":{"p2":"x"}},
            {"window":"second","guest_frame":3,"representations":{"p1":"b"}},
        ]
        with self.assertRaisesRegex(ValueError,"lacks any"):
            mod.frame_edges(rows,reps)

    def test_repeated_and_out_of_order_frame_refused(self):
        rep={"a":source("p1","1","a",[67,76],0)}
        for numbers in ((2,2),(3,2)):
            with self.subTest(numbers=numbers),self.assertRaisesRegex(
                ValueError,"duplicated or nonmonotonic"):
                mod.frame_edges([
                    {"window":"first","guest_frame":n,"representations":{"p1":"a"}}
                    for n in numbers],rep)

    def test_same_rgba_hash_different_binary_mask_refused(self):
        p=source("p1","1","a",[67,76],0)
        q=source("p1","1","b",[67,76],0)
        with self.assertRaisesRegex(ValueError,"identical original RGB"):
            mod.classify_pair(p,q)

    def test_wrong_player_mismatch_and_unknown_identity_refused(self):
        reps={"a":source("p1","1","a",[67,76],0),
              "b":source("p2","2","b",[67,76],0)}
        rows=[
            {"window":"first","guest_frame":1,"representations":{"p1":"a"}},
            {"window":"first","guest_frame":2,"representations":{"p1":"b"}},
        ]
        with self.assertRaisesRegex(ValueError,"wrong player"):
            mod.frame_edges(rows,reps)
        rows[1]["representations"]={"p1":"unknown"}
        with self.assertRaisesRegex(ValueError,"invalid registered"):
            mod.frame_edges(rows,reps)


if __name__=="__main__":
    unittest.main()
