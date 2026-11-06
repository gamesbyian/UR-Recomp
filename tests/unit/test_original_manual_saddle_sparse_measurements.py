"""Independent source-PDF replay of conservative p14/p15 saddle image-plane points.

Source imagery is 1994 printed illustration, NOT authenticated production 3D.
Coordinates were visually estimated by GPT-6, not independently artist reviewed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_manual_sparse_landmarks import measure
from tools.art.extract_manual_3d_reference_views import SOURCE,extract

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/"analysis/data/racer-original-manual-saddle-estimates-20261105.json"
QUALIFIED=ROOT/"analysis/data/racer-original-manual-saddle-2d-pdf-verified-20261105.json"
SOURCE_SHA="50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235"
SHAS={
 "p14-twist-fork-front":"cfbbc7b3e3cd1e3786897eba580bffec2ee9ceec268bcf4cdb4b5b6e30f4642b",
 "p15-mega-underside":"4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22",
}


class PrintSaddle2DObservationsTests(unittest.TestCase):
    def test_only_observed_original_image_plane_saddle_in_two_source_print_views(self):
        data=json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"],"UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1")
        self.assertEqual(data["source_pdf_sha256"],SOURCE_SHA)
        self.assertEqual(len(data["annotations"]),2)
        confirmed=json.loads(QUALIFIED.read_text(encoding="utf-8"))
        self.assertEqual(confirmed["authenticated_source_pdf_sha256"],SOURCE_SHA)
        self.assertEqual(confirmed["reviewed_print_figure_count"],2)
        self.assertFalse(confirmed["three_dimensional_source_geometry_calibrated"])
        self.assertFalse(confirmed["owner_character_likeness_approved"])
        self.assertFalse(confirmed["shipping_art_approved"])
        self.assertEqual({r["reference_id"] for r in data["annotations"]},set(SHAS))
        expected={"p14-twist-fork-front":(154,66,8),
                  "p15-mega-underside":(318,273,14)}
        for row in data["annotations"]:
            name=row["reference_id"]
            self.assertEqual(row["crop_png_sha256"],SHAS[name])
            self.assertEqual(set(row["visible_points"]),{"saddle"})
            self.assertEqual(set(row["unmeasurable"]),
                             {"wheel","hub","crown","fork","clamp","crank"})
            self.assertTrue(all(len(reason)>12
                                for reason in row["unmeasurable"].values()))
            self.assertIn("not independently artist-reviewed",row["annotator"])
            saddle=row["visible_points"]["saddle"]
            w=saddle["saddle_right"][0]-saddle["saddle_left"][0]
            h=saddle["saddle_bottom"][1]-saddle["saddle_top"][1]
            self.assertEqual((w,h,row["pixel_uncertainty"]),expected[name])
            self.assertGreater(len(row["perspective_and_occlusion_notes"]),80)

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),
                         "real original manual PDF replay requires pinned PyMuPDF/Pillow")
    def test_real_source_original_pdf_crops_and_complete_rgb_evidence(self):
        source=SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),SOURCE_SHA)
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)/"crops"
            evidence=extract(source,dest)
            self.assertEqual(evidence["source_pdf_sha256"],SOURCE_SHA)
            report=measure(json.loads(FIXTURE.read_text(encoding="utf-8")),dest,source)
            self.assertEqual(report["reviewed_print_figure_count"],2)
            self.assertEqual(report,json.loads(QUALIFIED.read_text(encoding="utf-8")), "actual retained original PDF RGB rerender changed frozen observed 2D evidence")
            for observed in report["observations"]:
                self.assertEqual(observed["original_print_pixel_aspect"],"square")
                self.assertEqual(set(observed["projected_pixel_distances"]),{"saddle"})
                self.assertIsNone(observed["projected_ratios_only_if_whole_wheel_visible"]
                                  ["saddle"]["width_over_projected_wheel_diameter"])
                self.assertIsNone(observed["projected_ratios_only_if_whole_wheel_visible"]
                                  ["saddle"]["height_over_projected_wheel_diameter"])
                self.assertFalse(observed["historical_1994_3d_camera_calibrated"])
                self.assertFalse(observed["original_source_mesh_dimensions_recovered"])
            self.assertFalse(report["three_dimensional_source_geometry_calibrated"])
            self.assertFalse(report["owner_character_likeness_approved"])
            self.assertFalse(report["shipping_art_approved"])


if __name__=="__main__":
    unittest.main()
