"""ROM-free original 40-source painted-axis and model mirroring controls."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from tools.art.audit_original_racer_chroma_axes import painted_axis
from tools.art.select_original_mesen_live_pose_exemplars import visible_rgba
from tools.art.audit_original_mesen_live_camera_axis_sensitivity import (
    SCHEMA, EXPECTED_AXES, ARMS, frozen_glb_axes, axis_gap, summarize,
)


def coloured_source() -> bytes:
    pixels=bytearray(64*64*4)
    for y in range(8,31):
        for dx in range(3):
            x=8+y//2+dx
            pixels[4*(y*64+x):4*(y*64+x)+4]=bytes([255,0,0,255])
    return bytes(pixels)


class OriginalSourceProjectionAxisTests(unittest.TestCase):
    def test_original_red_actual_screen_reflection_inverts_source_axis(self):
        held=coloured_source()
        visible=visible_rgba(held,"red")
        source=painted_axis(held,"p1")
        screen=painted_axis(visible,"p1")
        self.assertGreater(source["pixel_count"],12)
        self.assertEqual(source["pixel_count"],screen["pixel_count"])
        self.assertAlmostEqual(
            source["signed_axis_angle_from_image_vertical_deg"],
            -screen["signed_axis_angle_from_image_vertical_deg"],places=5)
        self.assertEqual(visible_rgba(visible,"red"),held)

    def test_model_orientation_arms_declared_once_per_racer(self):
        blue=-20.0
        red=-20.0
        self.assertEqual(axis_gap(blue,EXPECTED_AXES,red=False,
                                  arm=ARMS[0]),
                         axis_gap(blue,EXPECTED_AXES,red=False,arm=ARMS[1]))
        self.assertNotEqual(axis_gap(red,EXPECTED_AXES,red=True,arm=ARMS[0]),
                            axis_gap(red,EXPECTED_AXES,red=True,arm=ARMS[1]))
        self.assertEqual(axis_gap(-6.944131,EXPECTED_AXES,red=True,
                                  arm=ARMS[1]),0)
        self.assertEqual(axis_gap(6.944131,EXPECTED_AXES,red=True,
                                  arm=ARMS[0]),0)
        for wrong in ("best","auto","",None):
            with self.subTest(arm=wrong),self.assertRaisesRegex(ValueError,"immutable"):
                axis_gap(0.,EXPECTED_AXES,red=True,arm=wrong)
        for wrong in (True,float("nan"),float("inf"),90):
            with self.subTest(angle=wrong),self.assertRaisesRegex(ValueError,"immutable"):
                axis_gap(wrong,EXPECTED_AXES,red=True,arm=ARMS[0])

    def test_historic_exact_model_5_pose_axes_and_camera_cannot_drift(self):
        path=Path(__file__).resolve().parents[2] / (
            "analysis/data/racer-original-vs-glb-painted-axis-coverage-20261101.json")
        frozen=json.loads(path.read_text())
        self.assertEqual(frozen_glb_axes(frozen),EXPECTED_AXES)
        bad=dict(frozen)
        bad["experimental_pose_paint_axes_deg"]={
            **EXPECTED_AXES,"bank":9.3}
        with self.assertRaisesRegex(ValueError,"frozen"):
            frozen_glb_axes(bad)
        bad={**frozen,"provisional_camera_sha256":"0"*64}
        with self.assertRaisesRegex(ValueError,"frozen"):
            frozen_glb_axes(bad)
        bad={**frozen,"caveats":{**frozen["caveats"],"owner_character_likeness_approved":True}}
        with self.assertRaisesRegex(ValueError,"frozen"):
            frozen_glb_axes(bad)

    def test_invalid_source_sequence_fails_before_summary(self):
        missing=[{"tick":t,"racer":"blue","nearest_projected_angle_gap_deg":{
            arm:0.0 for arm in ARMS}} for t in range(1601,1605)]
        with self.assertRaisesRegex(ValueError,"census"):
            summarize(missing)

    def test_actual_original_40_source_results_do_not_approve_3d(self):
        path=Path(__file__).resolve().parents[2]/(
            "analysis/data/racer-original-mesen-live40-camera-axis-sensitivity-20261103.json")
        row=json.loads(path.read_text())
        self.assertEqual(row["schema"],SCHEMA)
        self.assertEqual(row["original_source_zip_sha256"],
                         "709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f")
        self.assertEqual(row["source_pixel_aspect"],"7:6")
        self.assertEqual(row["model_projection_orientation_arms"],list(ARMS))
        a=row["summary"]["shared_model_projection"]
        b=row["summary"]["red_model_projection_reflected"]
        self.assertEqual(a["source_observations_gap_over_10_deg"],28)
        self.assertEqual(b["source_observations_gap_over_10_deg"],18)
        self.assertEqual(a["source_observations_gap_over_20_deg"],7)
        self.assertEqual(b["source_observations_gap_over_20_deg"],4)
        self.assertEqual(a["mean_nearest_glb_axis_gap_deg"],13.514623)
        self.assertEqual(b["mean_nearest_glb_axis_gap_deg"],10.325687)
        self.assertEqual(
            (a["by_original_racer"]["red"]["source_observations_gap_over_10_deg"],
             b["by_original_racer"]["red"]["source_observations_gap_over_10_deg"]),
            (15,5))
        self.assertEqual(a["by_original_racer"]["blue"],b["by_original_racer"]["blue"])
        for label in ("model_mirror_choice_optimized_per_source",
                      "experimental_glb_geometry_or_camera_fitted",
                      "genuine_original_1994_3D_camera_or_joint_pose_recovered",
                      "source_to_2026_GLb_pose_labels_verified",
                      "model_painted_frame_equals_original_3D_anatomical_part",
                      "owner_likeness_approved"):
            self.assertIs(row[label],False)

if __name__ == "__main__":
    unittest.main()
