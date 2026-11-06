"""Original 1994 printed cyan fork/crown/clamp image evidence, not 3D ownership."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_manual_sparse_landmarks import measure
from tools.art.extract_manual_3d_reference_views import SOURCE, extract

ROOT=Path(__file__).resolve().parents[2]
OBSERVED=ROOT/"analysis/data/racer-original-manual-fork-clamp-image-traces-20261105.json"
PREVIOUS=ROOT/"analysis/data/racer-original-manual-saddle-estimates-20261105.json"
PDF_SHA="50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235"
KNOWN={
    "p14-twist-fork-front": {
        "sha":"cfbbc7b3e3cd1e3786897eba580bffec2ee9ceec268bcf4cdb4b5b6e30f4642b",
        "parts":{"saddle","crown","fork","clamp"},
        "dims":{"crown":66, "fork":59, "clamp":25},
        "uncertainty":9,
    },
    "p15-mega-underside":{
        "sha":"4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22",
        "parts":{"saddle","crown","clamp"},
        "dims":{"crown":143, "clamp":80},
        "uncertainty":22,
    },
}


class PrintedOriginalForkClampObservationsTests(unittest.TestCase):
    def test_source_identity_and_explicit_uncalibrated_print_feature_groups(self):
        d=json.loads(OBSERVED.read_text(encoding="utf-8"))
        self.assertEqual(d["schema"],"UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1")
        self.assertEqual(d["source_pdf_sha256"],PDF_SHA)
        self.assertEqual(len(d["annotations"]),2)
        existing=json.loads(PREVIOUS.read_text(encoding="utf-8"))
        orig={r["reference_id"]:r for r in existing["annotations"]}
        for r in d["annotations"]:
            key=r["reference_id"]
            spec=KNOWN[key]
            self.assertEqual(r["crop_png_sha256"],spec["sha"])
            self.assertEqual(set(r["visible_points"]),spec["parts"])
            self.assertEqual(set(r["unmeasurable"]),
                             set(["wheel","hub","saddle","crown","fork",
                                  "clamp","crank"])-spec["parts"])
            self.assertEqual(r["pixel_uncertainty"],spec["uncertainty"])
            self.assertEqual(r["visible_points"]["saddle"],
                             orig[key]["visible_points"]["saddle"])
            self.assertIn("independently unreviewed",r["annotator"])
            self.assertGreater(len(r["perspective_and_occlusion_notes"]),280)
            for group,expected in spec["dims"].items():
                parts=r["visible_points"][group]
                if group=="clamp":
                    width=parts["clamp_bottom"][1]-parts["clamp_top"][1]
                else:
                    width=parts[group+"_right"][0]-parts[group+"_left"][0]
                self.assertEqual(width,expected)
            self.assertNotIn("wheel",r["visible_points"])

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),
                         "real original PDF RGB replay requires pinned PyMuPDF/Pillow")
    def test_actual_1994_original_pdf_pixels_and_no_false_3d_claims(self):
        original=SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),PDF_SHA)
        with tempfile.TemporaryDirectory() as tmp:
            cropped=Path(tmp)/"source"
            evidence=extract(original,cropped)
            self.assertEqual(evidence["source_pdf_sha256"],PDF_SHA)
            reviewed=measure(json.loads(OBSERVED.read_text(encoding="utf-8")),
                             cropped,original)
            self.assertEqual(reviewed["reviewed_print_figure_count"],2)
            self.assertFalse(reviewed["three_dimensional_source_geometry_calibrated"])
            self.assertFalse(reviewed["owner_character_likeness_approved"])
            self.assertFalse(reviewed["shipping_art_approved"])
            for row in reviewed["observations"]:
                spec=KNOWN[row["reference_id"]]
                self.assertEqual(set(row["projected_pixel_distances"]),
                                 spec["parts"])
                self.assertEqual(row["original_print_pixel_aspect"],"square")
                self.assertFalse(row["historical_1994_3d_camera_calibrated"])
                self.assertFalse(row["original_source_mesh_dimensions_recovered"])
                for part in spec["parts"]:
                    self.assertTrue(all(value is None for value in
                        row["projected_ratios_only_if_whole_wheel_visible"]
                           [part].values()))
                for name,length in spec["dims"].items():
                    metric="height_px" if name=="clamp" else "width_px"
                    self.assertEqual(row["projected_pixel_distances"][name]
                                     [metric],float(length))


if __name__=="__main__":
    unittest.main()
