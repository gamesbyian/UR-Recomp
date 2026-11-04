"""Locked 7:6 camera backprojection for two *2026 authored* pivot hypotheses."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.art.compare_source_orbit_to_candidate_pivots import (
    CAMERA_SHA, SOURCE_SHA, SCHEMA,
    projection, source_backprojection, audit,
)

ROOT=Path(__file__).resolve().parents[2]


class SourceOrbitPivotTests(unittest.TestCase):
    def test_camera_projection_inverse_recovers_plane_not_depth(self):
        camera=json.loads((ROOT/"analysis/data/racer-inverse-side-provisional-1205.json").read_text())
        source=projection(camera,(0.,0.,1.8))
        self.assertAlmostEqual(source[0],33.5,places=8)
        self.assertAlmostEqual(source[1],20.9,places=8)
        line=source_backprojection(camera,source)
        self.assertAlmostEqual(line["world_point_at_zero_declaration_depth"][0],0)
        self.assertAlmostEqual(line["world_point_at_zero_declaration_depth"][2],1.8)
        self.assertFalse(line["world_depth_coordinate_identified"])
        self.assertEqual(len(line["unconstrained_camera_depth_direction_world"]),3)
        # The camera projects the depth axis away. These are indistinguishable.
        self.assertEqual(projection(camera,(0,-5,1.8)),source)
        self.assertEqual(projection(camera,(0,+5,1.8)),source)
        with self.assertRaises(ValueError):
            projection(camera,(0,float("nan"),1.8))

    def test_original_source_orbit_vs_two_historical_source_pivots(self):
        axis=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        cam=(ROOT/"analysis/data/racer-inverse-side-provisional-1205.json").read_bytes()
        self.assertEqual(hashlib.sha256(axis).hexdigest(),SOURCE_SHA)
        self.assertEqual(hashlib.sha256(cam).hexdigest(),CAMERA_SHA)
        result=audit(axis,cam)
        self.assertEqual(result["schema"],SCHEMA)
        x,y=result["source_original_24x64_2D_orbit_mean_source_pixel_xy"]
        self.assertAlmostEqual(x,31.515625,places=8)
        self.assertAlmostEqual(y,19.5859375,places=8)
        line=result["source_orbit_centre_backprojected_world_line"]
        self.assertAlmostEqual(line["world_point_at_zero_declaration_depth"][0],-0.2436951754,places=7)
        self.assertAlmostEqual(line["world_point_at_zero_declaration_depth"][2],1.9383223684,places=7)
        points=result["hypothetical_existing_2026_part_pivots"]
        axle=points["historical_2026_wheel_axle"]
        midbody=points["historical_2026_continuous_stunt_midbody"]
        self.assertAlmostEqual(axle["distance_in_7_6_corrected_source_display_pixel_units"],9.2097892243,places=5)
        self.assertAlmostEqual(midbody["distance_in_7_6_corrected_source_display_pixel_units"],2.66204199,places=5)
        self.assertGreater(axle["distance_in_7_6_corrected_source_display_pixel_units"],
                           midbody["distance_in_7_6_corrected_source_display_pixel_units"])
        self.assertTrue(result["shared_camera_7_6_and_glb_model_same_scale_not_independently_verified"])
        self.assertFalse(result["original_source_1994_camera_or_mesh_recovered"])
        self.assertFalse(result["original_1994_3D_joint_pivot_recovered"])

    def test_corrupted_source_or_camera_rejected(self):
        cam=(ROOT/"analysis/data/racer-inverse-side-provisional-1205.json").read_bytes()
        with self.assertRaisesRegex(ValueError,"original ROM"):
            audit(b"{}",cam)
        axis=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        with self.assertRaisesRegex(ValueError,"camera"):
            audit(axis,b"{}")


if __name__=="__main__":
    unittest.main()
