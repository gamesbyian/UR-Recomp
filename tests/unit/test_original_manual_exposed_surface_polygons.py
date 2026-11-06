"""Cropped-original 1994 print exposed surfaces, never entire original hub mesh."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_manual_sparse_landmarks import measure, visible_surface_regions
from tools.art.extract_manual_3d_reference_views import SOURCE, extract

ROOT=Path(__file__).resolve().parents[2]
INPUT=ROOT/"analysis/data/racer-original-manual-exposed-structural-surfaces-20261105.json"
PDF_SHA="50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235"
REGIONS={
 "p14-twist-fork-front":("cfbbc7b3e3cd1e3786897eba580bffec2ee9ceec268bcf4cdb4b5b6e30f4642b",
                         "cyan-fork-bridge-exposed",2134.0,9),
 "p15-mega-underside":("4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22",
                       "dark-near-hub-housing-face",35973.5,24),
}


class OriginalPrintExposedSurfaceTests(unittest.TestCase):
    def test_actual_cropped_source_identifiers_and_partial_face_uncertainty(self):
        source=json.loads(INPUT.read_text(encoding="utf-8"))
        self.assertEqual(source["schema"],"UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1")
        self.assertEqual(source["source_pdf_sha256"],PDF_SHA)
        self.assertEqual(len(source["annotations"]),2)
        seen=set()
        for row in source["annotations"]:
            name=row["reference_id"]
            self.assertIn(name,REGIONS)
            self.assertNotIn(name,seen)
            seen.add(name)
            sha,region_id,area,unc=REGIONS[name]
            self.assertEqual(row["crop_png_sha256"],sha)
            self.assertEqual(row["pixel_uncertainty"],unc)
            self.assertEqual(set(row["visible_points"]),{"saddle"})
            self.assertEqual(set(row["unmeasurable"]),
                             {"wheel","hub","crown","fork","clamp","crank"})
            self.assertEqual(len(row["visible_surface_regions"]),1)
            region=row["visible_surface_regions"][0]
            self.assertEqual(region["region_id"],region_id)
            dims=(358,369) if name.startswith("p14") else (900,1151)
            parsed=visible_surface_regions(row["visible_surface_regions"],dims)
            self.assertEqual(parsed[0]["projected_visible_2d_area_px2"],area)
            self.assertIs(region["original_3d_part_identity_verified"],False)
            self.assertIs(region["entire_original_3d_surface_visible"],False)
            self.assertIn("not independently artist reviewed",row["annotator"])
            self.assertGreater(len(row["perspective_and_occlusion_notes"]),100)
        self.assertEqual(seen,set(REGIONS))

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),
                         "real original print pixels require pinned PyMuPDF/Pillow")
    def test_actual_source_pdf_1994_rgb_pixel_replay_and_face_only_measurements(self):
        original=SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),PDF_SHA)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"crops"
            receipt=extract(original,folder)
            self.assertEqual(receipt["source_pdf_sha256"],PDF_SHA)
            report=measure(json.loads(INPUT.read_text(encoding="utf-8")),folder,original)
            self.assertEqual(report["reviewed_print_figure_count"],2)
            for row in report["observations"]:
                expected=REGIONS[row["reference_id"]]
                self.assertEqual(row["crop_png_sha256"],expected[0])
                self.assertEqual(len(row["visible_surface_regions"]),1)
                self.assertEqual(row["visible_surface_regions"][0]
                                 ["projected_visible_2d_area_px2"],expected[2])
                self.assertNotIn("hub",row["projected_pixel_distances"])
                self.assertIsNone(row["projected_ratios_only_if_whole_wheel_visible"]
                                  ["saddle"]["width_over_projected_wheel_diameter"])
                self.assertFalse(row["historical_1994_3d_camera_calibrated"])
                self.assertFalse(row["original_source_mesh_dimensions_recovered"])
                self.assertFalse(row["visible_surface_regions"][0]
                                 ["original_3d_part_identity_verified"])
                self.assertFalse(row["visible_surface_regions"][0]
                                 ["entire_original_3d_surface_visible"])
            self.assertFalse(report["three_dimensional_source_geometry_calibrated"])
            self.assertFalse(report["owner_character_likeness_approved"])
            self.assertFalse(report["shipping_art_approved"])


if __name__=="__main__":
    unittest.main()
