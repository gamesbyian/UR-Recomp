"""A partially exposed printed hub face is an observed polygon, not a full hub."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_manual_sparse_landmarks import (
    visible_surface_regions, measure, SCHEMA,
)
from tools.art.extract_manual_3d_reference_views import extract,git_blob_sha1

REGION={
 "region_id":"near-side-hub-cover",
 "visible_appearance_notes":"Dark polygonal face of the central printed hub casing",
 "cutoff_or_occlusion_notes":"Concealed by tire and fork, no original full hub shape known",
 "visible_polygon_xy":[[20,25],[120,25],[115,140],[25,145]],
 "original_3d_part_identity_verified":False,
 "entire_original_3d_surface_visible":False,
}

class SourceManualPartialSurfaceTests(unittest.TestCase):
    def test_projected_partial_surface_area_never_certifies_original_3d(self):
        rows=visible_surface_regions([REGION],(200,200))
        self.assertEqual(len(rows),1)
        self.assertGreater(rows[0]["projected_visible_2d_area_px2"],10000)
        self.assertEqual(rows[0]["projected_bounds_xyxy"],[20,25,120,145])
        self.assertIs(rows[0]["original_3d_part_identity_verified"],False)
        self.assertIs(rows[0]["entire_original_3d_surface_visible"],False)
        self.assertIs(rows[0]["original_production_camera_calibrated"],False)
        self.assertEqual(visible_surface_regions(None,(200,200)),[])
        self.assertEqual(visible_surface_regions([],(200,200)),[])

    def test_reject_forged_or_nonfinite_visible_polygons(self):
        import copy
        for name,mod in [
            ("wrong-original-mesh",{"original_3d_part_identity_verified":True}),
            ("wrong-complete-face",{"entire_original_3d_surface_visible":True}),
            ("duplicate-vertex",{"visible_polygon_xy":[[20,20],[20,20],[40,40]]}),
            ("self-crossing",{"visible_polygon_xy":[[20,20],[130,130],[20,130],[130,20]]}),
            ("outside-crop",{"visible_polygon_xy":[[20,20],[200,20],[40,40]]}),
            ("not-enclosed",{"visible_polygon_xy":[[20,20],[30,30],[40,40]]}),
            ("wrong-shape",{"visible_polygon_xy":[[20,20],[30,30]]}),
            ("bad-label",{"region_id":"3d 1994 original mesh"}),
            ("empty-notes",{"visible_appearance_notes":"unknown"}),
        ]:
            candidate=copy.deepcopy(REGION)
            candidate.update(mod)
            with self.subTest(name=name),self.assertRaises(ValueError):
                visible_surface_regions([candidate],(200,200))
        with self.assertRaises(ValueError):
            visible_surface_regions([REGION,REGION],(200,200))

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),
                         "optional exact source PDF replay requires PyMuPDF/Pillow")
    def test_partial_surface_without_any_whole_hub_is_source_pdf_authenticated(self):
        import fitz
        doc=fitz.open()
        for n in range(40):
            pg=doc.new_page(width=512,height=748.5)
            if n in (13,14,15):
                pg.draw_rect(fitz.Rect(30,40,350,500),color=(.3,.7,.7),
                             fill=(.3,.7,.7))
        source=doc.tobytes()
        doc.close()
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/"figures"
            receipt=extract(source,folder)
            first=receipt["figures"][2]
            observed={
                "schema":SCHEMA,
                "source_pdf_sha256":hashlib.sha256(source).hexdigest(),
                "annotations":[{
                    "reference_id":"p15-mega-underside",
                    "crop_png_sha256":first["crop_png_sha256"],
                    "annotator":"independent original printed source observer",
                    "pixel_uncertainty":5,
                    "perspective_and_occlusion_notes":
                        "Original print oblique surface, camera and physical dimensions unknown",
                    "visible_points":{},
                    "unmeasurable":{part:
                        "Only one exposed polygon observed; part exterior occluded"
                        for part in ("wheel","hub","saddle","crown","fork","clamp","crank")},
                    "visible_surface_regions":[REGION],
                }],
            }
            result=measure(observed,folder,source,
                           expected_blob=git_blob_sha1(source))
            entry=result["observations"][0]
            self.assertEqual(entry["projected_pixel_distances"],{})
            self.assertEqual(entry["projected_ratios_only_if_whole_wheel_visible"],{})
            self.assertEqual(len(entry["visible_surface_regions"]),1)
            self.assertFalse(result["three_dimensional_source_geometry_calibrated"])
            self.assertFalse(result["owner_character_likeness_approved"])
            self.assertFalse(result["shipping_art_approved"])


if __name__=="__main__":
    unittest.main()
