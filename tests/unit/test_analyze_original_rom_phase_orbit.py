"""Precise 2D source orbit, without attributing original 1994 joints."""
import json
import math
from pathlib import Path
import unittest
from tools.art.analyze_original_rom_phase_orbit import (
    SOURCE_SHA, SCHEMA, harmonic, audit,
)

ROOT=Path(__file__).resolve().parents[2]


class SourcePhaseOrbitTests(unittest.TestCase):
    def test_synthetic_64_position_harmonic_and_constant_null(self):
        xs=[31.5-10*math.sin(2*math.pi*i/64) for i in range(64)]
        ys=[19.5+10*math.cos(2*math.pi*i/64) for i in range(64)]
        x,y=harmonic(xs),harmonic(ys)
        self.assertAlmostEqual(x["mean_source_pixel_center"],31.5,places=10)
        self.assertAlmostEqual(y["mean_source_pixel_center"],19.5,places=10)
        self.assertAlmostEqual(x["sin_first_harmonic"],-10,places=10)
        self.assertAlmostEqual(y["cos_first_harmonic"],10,places=10)
        self.assertLess(x["rmse_source_pixels"],1e-10)
        self.assertLess(y["rmse_source_pixels"],1e-10)
        self.assertAlmostEqual(x["first_harmonic_R_squared"],1)
        with self.assertRaises(ValueError):harmonic(xs[:63])
        with self.assertRaises(ValueError):harmonic([float("nan")]*64)

    def test_original_64_orientation_source_bbox_orbit_and_no_3d_claim(self):
        raw=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        import hashlib
        self.assertEqual(hashlib.sha256(raw).hexdigest(),SOURCE_SHA)
        result=audit(raw)
        self.assertEqual(result["schema"],SCHEMA)
        x,y=result["source_x_first_harmonic"],result["source_y_first_harmonic"]
        self.assertAlmostEqual(x["mean_source_pixel_center"],31.515625,places=6)
        self.assertAlmostEqual(y["mean_source_pixel_center"],19.5859375,places=6)
        self.assertAlmostEqual(x["sin_first_harmonic"],-9.717594751,places=5)
        self.assertAlmostEqual(y["cos_first_harmonic"],10.314349801,places=5)
        self.assertLess(x["rmse_source_pixels"],0.44)
        self.assertLess(y["rmse_source_pixels"],0.46)
        self.assertGreater(x["first_harmonic_R_squared"],0.99)
        self.assertGreater(y["first_harmonic_R_squared"],0.99)
        self.assertEqual(result["source_x_region_bbox_width_values"],[12,13])
        self.assertFalse(result["original_1994_3D_camera_mesh_or_joint_axis_recovered"])
        self.assertFalse(result["source_orientation_index_physically_calibrated_in_degrees"])
        self.assertFalse(result["source_phase_is_real_wheel_rotation_calibrated"])

    def test_wrong_source_report_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            audit(b"{}")


if __name__=="__main__":
    unittest.main()
