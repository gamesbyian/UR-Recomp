"""Source-registered 1994 print aspect ≠ unique 2026 3D saddle mesh."""
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest

from tools.art.audit_print_saddle_camera_identifiability import (
    SCHEMA,ORIGINAL_2026_UPRIGHT_GLB_SHA256,
    ORIGINAL_1994_PRINT_SHA256,SOURCE_SADDLE_NODES,
    SOURCE_PRINT_RESULT,YAW_DEGREES,ELEVATION_DEGREES,
    ORIGINAL_SADDLE_PRINTS,verify_print_report,camera_aspect_ratio,
    compare_source_model,
)

ROOT=Path(__file__).resolve().parents[2]
SCORES=ROOT/"analysis/data/racer-original-manual-saddle-camera-ambiguity-20261105.json"
PRINTS=ROOT/SOURCE_PRINT_RESULT


class OriginalPrintSaddleCameraAmbiguityTests(unittest.TestCase):
    def test_genuinely_authenticated_print_2d_crops_not_3d_camera_observations(self):
        raw=json.loads(PRINTS.read_text(encoding="utf-8"))
        rows=verify_print_report(raw)
        self.assertEqual(len(rows),2)
        self.assertEqual(raw["authenticated_source_pdf_sha256"],
                         ORIGINAL_1994_PRINT_SHA256)
        self.assertEqual(set(SOURCE_SADDLE_NODES),
                         {"saddle__material_0","saddle__material_1"})
        self.assertEqual(sum(SOURCE_SADDLE_NODES.values()),2708)
        self.assertEqual(len(YAW_DEGREES)*len(ELEVATION_DEGREES),1073)
        self.assertEqual(set(ORIGINAL_SADDLE_PRINTS),
                         {"p14-twist-fork-front","p15-mega-underside"})
        bad=json.loads(json.dumps(raw))
        bad["observations"][0]["pixel_uncertainty"]=0
        with self.assertRaisesRegex(ValueError,"original print"):
            verify_print_report(bad)
        bad=json.loads(json.dumps(raw))
        bad["observations"][1]["projected_ratios_only_if_whole_wheel_visible"][
            "saddle"]["height_over_projected_wheel_diameter"]=.42
        with self.assertRaisesRegex(ValueError,"original print"):
            verify_print_report(bad)

    def test_retained_model_only_camera_census_and_no_1994_art_promotion(self):
        report=json.loads(SCORES.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"],SCHEMA)
        self.assertEqual(report["source_original_1994_print_pdf_sha256"],
                         ORIGINAL_1994_PRINT_SHA256)
        self.assertEqual(report["source_2026_actual_authored_upright_glb_sha256"],
                         ORIGINAL_2026_UPRIGHT_GLB_SHA256)
        self.assertEqual(report["total_different_source_model_orthographic_camera_orbits"],1073)
        self.assertEqual(report["source_2026_saddle_total_vertices"],2708)
        self.assertEqual(report["uncalibrated_independent_two_print_orbit_pair_combinations"],
                         508*188)
        self.assertEqual([x["matching_2026_model_only_orbits_within_uncertainty"]
                          for x in report["original_print_sources"]],[508,188])
        for key in ("camera_fits_are_anatomical_1994_source_3d_validation",
                    "observations_constrain_camera_or_model_uniquely",
                    "original_printed_1994_render_mesh_or_camera_recovered",
                    "original_game_ROM_64px_PPU_frames_used",
                    "unapproved_2026_saddle_vertices_or_materials_modified",
                    "owner_artist_likeness_approved",
                    "shipping_4k_character_art_approved"):
            self.assertIs(report[key],False,key)
        for record in report["original_print_sources"]:
            self.assertLess(record["uncertainty_propagated_ratio_lower_bound"],
                            record["observed_image_plane_width_over_height"])
            self.assertLess(record["observed_image_plane_width_over_height"],
                            record["uncertainty_propagated_ratio_upper_bound"])
            self.assertIs(record["human_artist_reviewed"],False)
            self.assertIs(record["original_1994_artist_camera_estimated"],False)
            self.assertIs(record["original_1994_actual_source_model_geometry_constrained"],False)

    @unittest.skipUnless(importlib.util.find_spec("numpy"),
                         "source 2026 GLB model-only 3D camera requires NumPy")
    def test_camera_projection_works_but_never_accepts_arbitrary_original_camera(self):
        import numpy as np
        vertices=np.asarray([[-1,-.3,-.2],[1,-.3,-.2],
                             [1,.3,.4],[-1,.3,.4]],dtype=float)
        self.assertGreater(camera_aspect_ratio(vertices,0,0),1)
        for yaw,elev in ((-5,0),(0,75),(20,1),(True,0)):
            with self.assertRaisesRegex(ValueError,"frozen"):
                camera_aspect_ratio(vertices,yaw,elev)
        with self.assertRaisesRegex(ValueError,"finite"):
            camera_aspect_ratio([[0,0,0],[1,0,0],[math.nan,1,0]],0,0)

    @unittest.skipUnless(importlib.util.find_spec("numpy") and
                         importlib.util.find_spec("trimesh"),
                         "optional true source model audit requires NumPy and Trimesh")
    def test_reproduce_source_model_if_exact_original_glb_explicitly_supplied(self):
        name=os.environ.get("UR_ART4K_AUTHORED_UPRIGHT_GLB")
        if not name:
            self.skipTest("exact source 2026 GLB provided only for independent recheck")
        actual=compare_source_model(Path(name),PRINTS)
        expected=json.loads(SCORES.read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)


if __name__=="__main__":
    unittest.main()
