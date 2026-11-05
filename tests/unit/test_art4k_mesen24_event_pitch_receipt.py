"""ROM-free precise re-accounting of two event-local 2026 pitch controls."""
import hashlib,json
from pathlib import Path
import unittest

REPORT=Path(__file__).resolve().parents[2]/"analysis/data/racer-original-mesen24-event-pitch-control-20261103.json"
SHA="fb64781ac7dfbb8de11012c2d569647358aca824cb6fc6cec073fbd795f39323"

class EventPitchTests(unittest.TestCase):
    def test_source_receipt_pinned_and_no_original_3d_claim(self):
        raw=REPORT.read_bytes()
        self.assertEqual(hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest(),SHA)
        r=json.loads(raw)
        self.assertEqual(r["schema"],"UR-ART4K-MESEN24-PREDECLARED-TWO-UPPER-EDGES-FRAME-STEP-CONTROL/1")
        self.assertEqual(r["original_source_archive_sha256"],"28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6")
        self.assertEqual(r["original_upright_2026_glb_sha256"],"efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5")
        self.assertTrue(r["source_event_edges_seen_in_advance_and_not_blind"])
        self.assertTrue(r["source_model_registration_fixed_at_tick1601"])
        self.assertFalse(r["original_1994_camera_pose_or_bone_mapping_recovered"])
        self.assertEqual(r["only_predeclared_after_pitches_degrees"],[0,10,-10])

    def test_exact_two_events_and_each_band_add_up(self):
        r=json.loads(REPORT.read_bytes())["per_source_player"]
        self.assertEqual(set(r),{"blue","red"})
        self.assertEqual(r["blue"]["actual_source_edge"],[1602,1603])
        self.assertEqual(r["red"]["actual_source_edge"],[1605,1606])
        for player,event in r.items():
            expected={"blue":[27,20,57],"red":[20,41,58]}[player]
            self.assertEqual(set(event["all_controls"]),{"0","10","-10"})
            self.assertEqual(event["part_motion_before_frame_pitch_deg"],0)
            for key,v in event["all_controls"].items():
                bands=v["source_y_band_details"]
                self.assertEqual([b["source_changed_pixels"] for b in bands],expected)
                self.assertEqual(sum(b["source_changed_pixels"] for b in bands),v["source_delta_pixels"])
                # Source-Y bands cover the original occupied envelope only.
                # The rigid pitch model can generate EXTRA changes outside it.
                self.assertLessEqual(sum(b["model_changed_pixels"] for b in bands),
                                     v["model_delta_pixels"])
                self.assertEqual(sum(b["intersect_changed_pixels"] for b in bands),v["change_pixel_intersection"])
                s=v["source_delta_pixels"];m=v["model_delta_pixels"];hit=v["change_pixel_intersection"]
                self.assertEqual(v["change_recall"],round(hit/s,8))
                self.assertEqual(v["change_precision"],round(hit/m,8))
                self.assertEqual(v["change_iou"],round(hit/(s+m-hit),8))

    def test_pitched_rig_misses_most_original_event_upper_changes(self):
        per=json.loads(REPORT.read_bytes())["per_source_player"]
        for player,v in per.items():
            arms=v["all_controls"]
            self.assertEqual(arms["0"]["source_y_band_details"][0]["model_changed_pixels"],0)
            self.assertGreater(arms["10"]["source_y_band_details"][0]["model_changed_pixels"],
                               arms["10"]["source_y_band_details"][0]["source_changed_pixels"]*2)
            self.assertGreater(arms["-10"]["source_y_band_details"][0]["model_changed_pixels"],
                               arms["-10"]["source_y_band_details"][0]["source_changed_pixels"]*2)
            self.assertLess(arms["10"]["change_iou"],arms["0"]["change_iou"])
        # The red pitch experiment also introduces change beyond the
        # original source silhouette's observed vertical envelope.
        red=per["red"]["all_controls"]
        self.assertEqual(red["-10"]["model_delta_pixels"]-
                         sum(x["model_changed_pixels"]
                             for x in red["-10"]["source_y_band_details"]),27)
        self.assertEqual(red["10"]["model_delta_pixels"]-
                         sum(x["model_changed_pixels"]
                             for x in red["10"]["source_y_band_details"]),28)

if __name__=="__main__":
    unittest.main()
