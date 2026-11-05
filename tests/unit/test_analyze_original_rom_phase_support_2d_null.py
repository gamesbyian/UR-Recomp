"""Retrospective original ROM phase-support motion under honest 2D nulls."""
import hashlib
import json
import math
from pathlib import Path
import unittest

from tools.art.analyze_original_rom_phase_support_2d_null import (
    PIXELS, ROM_SHA, AXIS_REPORT_SHA, CONTROLS, SCHEMA,
    bbox, even_index_harmonic, harmonic_at, predict_2d, compare, audit,
)

ROOT = Path(__file__).resolve().parents[2]


class OriginalPhaseSupport2DNullTests(unittest.TestCase):
    def test_harmonic_even_fit_does_not_use_odd_angles(self):
        vals = [20 + 7*math.cos(2*math.pi*i/64) - 3*math.sin(2*math.pi*i/64)
                + (1000 if i % 2 else 0) for i in range(64)]
        fit = even_index_harmonic(vals)
        self.assertAlmostEqual(fit["mean"], 20, places=10)
        self.assertAlmostEqual(fit["cos"], 7, places=10)
        self.assertAlmostEqual(fit["sin"], -3, places=10)
        self.assertAlmostEqual(harmonic_at(fit, 0), 27, places=10)
        with self.assertRaises(ValueError):
            even_index_harmonic([2]*63)

    def test_rotating_source_support_is_distinct_from_translation(self):
        support = bytearray(PIXELS)
        support[29*64+31] = 1
        original = bytes(support)
        self.assertEqual(bbox(original), [31,29,31,29])
        xfit = {"mean":31.5, "cos":0.0, "sin":-10.0}
        yfit = {"mean":19.5, "cos":10.0, "sin":0.0}
        rotated = predict_2d(original, "rigid_screen_rotation", 16, xfit, yfit)
        translated = predict_2d(original, "orbit_translation", 16, xfit, yfit)
        self.assertEqual(bbox(rotated), [22,19,22,19])
        self.assertEqual(bbox(translated), [21,19,21,19])
        self.assertEqual(compare(rotated, rotated)["iou"], 1.0)
        self.assertEqual(compare(rotated, translated)["iou"], 0.0)
        self.assertEqual(predict_2d(original,"rigid_screen_rotation",0,xfit,yfit),original)
        self.assertEqual(predict_2d(original,"static_support",16,xfit,yfit),original)
        with self.assertRaises(ValueError):
            predict_2d(original,"unbounded_spatial_fit",16,xfit,yfit)
        with self.assertRaises(ValueError):
            compare(b"bad",original)

    def test_real_original_1536_ROM_frames_even_fit_odd_score(self):
        rom = (ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        source = (ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(source).hexdigest(),AXIS_REPORT_SHA)
        report = audit(rom, source)
        self.assertEqual(report["schema"],SCHEMA)
        self.assertEqual(report["original_frame_grid_size"],[24,64])
        self.assertTrue(report["controls_are_source_space_2D_nulls_not_3D"])
        self.assertFalse(report["original_1994_3D_mesh_camera_joint_axis_recovered"])
        self.assertFalse(report["source_racer_art_owner_approved"])
        self.assertGreater(report["source_support_pixels_min"], 0)
        self.assertGreaterEqual(report["source_support_pixels_max"],
                                report["source_support_pixels_min"])
        angles = [r["original_ROM_orientation_index"] for r in report["scored_odd_orientation_rows"]]
        self.assertEqual(angles,list(range(1,64,2)))
        self.assertEqual(set(report["summary"]),set(CONTROLS))
        for name, row in report["summary"].items():
            self.assertEqual(row["tested_odd_orientation_count"],32)
            self.assertTrue(0<=row["pooled_iou"]<=1)
            self.assertTrue(0<=row["mean_per_orientation_iou"]<=1)
            self.assertGreater(row["pooled_intersection"]+row["pooled_false_negative"],0)
        # Original-ROM source test at implementation head f6d7558e, Actions
        # run 41785648962, 32 odd orientations. Freeze exact result, not
        # merely a nonempty JSON report or a flattering fit claim.
        frozen = {
            "static_support": (613, 3099, 3124, 0.08967232),
            "orbit_translation": (3410, 302, 327, 0.84426838),
            "rigid_screen_rotation": (3477, 243, 260, 0.87361809),
        }
        for name, (tp, fp, fn, iou) in frozen.items():
            row = report["summary"][name]
            self.assertEqual(row["pooled_intersection"], tp)
            self.assertEqual(row["pooled_false_positive"], fp)
            self.assertEqual(row["pooled_false_negative"], fn)
            self.assertAlmostEqual(row["pooled_iou"], iou, places=8)
        self.assertGreater(report["summary"]["rigid_screen_rotation"]["pooled_iou"],
                           report["summary"]["orbit_translation"]["pooled_iou"])
        print("OK ART4K_PHASE_SUPPORT_2D_NULL_TEST_SUMMARY",
              json.dumps(report["summary"],sort_keys=True))

    def test_wrong_original_axis_and_rom_refused(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            audit(b"",b"{}")


if __name__ == "__main__":
    unittest.main()
