"""ROM-free arithmetic re-audit of fixed real-Mesen24 rig motion negative control."""
import hashlib
import json
from pathlib import Path
import unittest

REPORT=Path(__file__).resolve().parents[2]/"analysis/data/racer-original-mesen24-continuous-pose-control-20261103.json"
REPORT_SHA="4fc431cbcdc21e2c84197869fd52e1131b5332215c27d44f48227fc577623b32"
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
MODEL_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"


class RigMotionEvidenceTests(unittest.TestCase):
    def test_frozen_original_and_model_sources_and_no_fit_claim(self):
        raw=REPORT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),REPORT_SHA)
        self.assertNotIn(b"\r",raw)
        r=json.loads(raw)
        self.assertEqual(r["schema"],"UR-ART4K-AUTHENTIC-MESEN24-VS-2026-FIVE-PARENT-MOTION-CONTROLS/1")
        self.assertEqual(r["source_original_ticks"],list(range(1601,1625)))
        self.assertEqual(r["original_consecutive_source_24_zip_sha256"],SOURCE_SHA)
        self.assertEqual(r["candidate_actual_upright_glb_sha256"],MODEL_SHA)
        self.assertEqual(r["provisional_fixed_camera_sha256"],CAMERA_SHA)
        self.assertTrue(r["fixed_source_anchor_selected_once_at_tick1601"])
        self.assertTrue(r["no_fitted_phase_camera_geometry_or_frame_translation"])
        self.assertFalse(r["original_1994_3d_animation_or_art_approved"])

    def test_all_three_arms_account_for_every_source_and_model_edge(self):
        r=json.loads(REPORT.read_bytes())
        arms=r["arms"]
        self.assertEqual(set(arms),{
            "static_neutral","direct_drive_24deg_per_tick",
            "same_drive_plus_sinusoidal_frame_pitch_10deg"})
        for name,arm in arms.items():
            self.assertEqual(arm["samples"],24)
            self.assertEqual(set(arm["per_player"]),{"blue","red"})
            for player,data in arm["per_player"].items():
                source_count={"blue":660,"red":659}[player]
                self.assertEqual(data["original_changed_pixels_sum"],source_count)
                self.assertEqual(data["original_changed_edges"],23)
                self.assertEqual(data["model_held_edges"]+data["model_changed_edges"],23)
                source=data["original_changed_pixels_sum"]
                model=data["model_changed_pixels_sum"]
                both=data["change_pixel_intersection"]
                self.assertLessEqual(both,min(source,model))
                self.assertEqual(data["change_pixel_recall"],round(both/source,8))
                self.assertEqual(data["change_pixel_precision"],
                                 round(both/model,8) if model else 0.0)
                self.assertEqual(data["change_pixel_iou"],
                                 round(both/(source+model-both),8))
                self.assertGreaterEqual(data["mean_24_source_silhouette_iou"],0)
                self.assertLessEqual(data["mean_24_source_silhouette_iou"],1)

    def test_negative_control_is_specific_not_global_3d_rejection(self):
        arms=json.loads(REPORT.read_bytes())["arms"]
        static=arms["static_neutral"]
        drive=arms["direct_drive_24deg_per_tick"]
        pitched=arms["same_drive_plus_sinusoidal_frame_pitch_10deg"]
        self.assertEqual(static["parameters"]["per_tick_drive_deg"],0)
        self.assertEqual(drive["parameters"]["per_tick_drive_deg"],24)
        self.assertEqual(pitched["parameters"]["pitch_amplitude_deg"],10)
        for player in ("blue","red"):
            a=static["per_player"][player]
            b=drive["per_player"][player]
            c=pitched["per_player"][player]
            self.assertEqual(a["model_changed_edges"],0)
            self.assertEqual(b["model_changed_edges"],23)
            self.assertEqual(c["model_changed_edges"],23)
            self.assertEqual(b["model_changed_pixels_sum"],816)
            self.assertEqual(c["model_changed_pixels_sum"],1247)
            self.assertEqual(b["change_pixel_intersection"],c["change_pixel_intersection"])
            self.assertLess(b["mean_24_source_silhouette_iou"],a["mean_24_source_silhouette_iou"])
            self.assertGreater(c["mean_24_source_silhouette_iou"],a["mean_24_source_silhouette_iou"])
            self.assertLess(c["change_pixel_iou"],b["change_pixel_iou"])


if __name__=="__main__":
    unittest.main()
