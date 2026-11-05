"""Original manual partial-view landmark fidelity and anti-forged-crop regressions."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_manual_sparse_landmarks import (
    SCHEMA,PARTS,bounds,point,measure,
)
from tools.art.extract_manual_3d_reference_views import (
    extract,git_blob_sha1,
)


def annotation(sha,part="crown",ref="p14-twist-fork-front"):
    shown={"crown":{"crown_left":[10,100],"crown_right":[125,100]}}
    if part=="wheel":
        shown={"wheel":{
            "wheel_left":[10,90],"wheel_right":[410,90],
            "wheel_top":[110,10],"wheel_bottom":[110,610]},
            "crown":{"crown_left":[110,170],"crown_right":[210,170]}}
    return {
        "schema":SCHEMA,"source_pdf_sha256":sha,"annotations":[{
            "reference_id":ref,
            "annotator":"2026 printed-art observer",
            "pixel_uncertainty":2.0,
            "perspective_and_occlusion_notes":
                "Printed angled figure with occluded or out-of-page parts.",
            "visible_points":shown,
            "unmeasurable":{
                key:"Hidden behind ribbon, or not sufficiently resolved"
                for key in PARTS if key not in shown
            },
        }],
    }


class SparseManualLandmarkTests(unittest.TestCase):
    def test_source_axes_partial_bounds_and_no_imagined_wheel_diameter(self):
        self.assertEqual(bounds({"crown_left":(10,5),"crown_right":(30,5)},
                                "crown")["width_px"],20)
        self.assertEqual(bounds({"crank_root":(10,20),"pedal_center":(13,24)},
                                "crank")["projected_endpoint_separation_px"],5)
        self.assertRaises(ValueError,point,[True,40],(100,100),"x")
        self.assertRaises(ValueError,point,[100,40],(100,100),"x")
        self.assertRaises(ValueError,bounds,
                          {"fork_left":(30,10),"fork_right":(20,10)},"fork")

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),
                         "original PDF crop replay requires optional PyMuPDF/Pillow")
    def test_actual_four_page_pdf_pixel_replay_and_sparse_partial_annotations(self):
        import fitz
        from PIL import Image

        doc=fitz.open()
        for i in range(40):
            pg=doc.new_page(width=512,height=748.5)
            if i in (13,14,15):
                pg.draw_rect(fitz.Rect(100,100,350,650),
                             color=(0.1,0.5,0.7),fill=(0.1,0.5,0.7))
        raw=doc.tobytes()
        doc.close()
        digest=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/"views"
            original=extract(raw,output)
            self.assertEqual(len(original["figures"]),4)
            self.assertEqual(original["source_pdf_sha256"],digest)
            expected=git_blob_sha1(raw)
            first=annotation(digest)
            first['annotations'][0]['crop_png_sha256']=original['figures'][0]['crop_png_sha256']
            report=measure(first,output,raw,expected_blob=expected)
            self.assertEqual(report["reviewed_print_figure_count"],1)
            a=report["observations"][0]
            self.assertEqual(a["projected_pixel_distances"]["crown"]["width_px"],115)
            self.assertIsNone(
                a["projected_ratios_only_if_whole_wheel_visible"]
                ["crown"]["width_over_projected_wheel_diameter"])
            self.assertIn("wheel",a["unmeasurable"])
            self.assertIs(report["three_dimensional_source_geometry_calibrated"],False)
            self.assertIs(report["shipping_art_approved"],False)

            second=annotation(digest,part="wheel",ref="p15-mega-underside")
            second["annotations"][0]["crop_png_sha256"]=original["figures"][2]["crop_png_sha256"]
            report2=measure(second,output,raw,expected_blob=expected)
            b=report2["observations"][0]
            self.assertEqual(b["projected_pixel_distances"]["wheel"]["height_px"],600)
            self.assertEqual(
                b["projected_ratios_only_if_whole_wheel_visible"]
                ["crown"]["width_over_projected_wheel_diameter"],round(100/600,6))

            malformed=annotation(digest)
            malformed["annotations"][0]["crop_png_sha256"]=original["figures"][0]["crop_png_sha256"]
            del malformed["annotations"][0]["unmeasurable"]["wheel"]
            with self.assertRaisesRegex(ValueError,"observed OR explicitly"):
                measure(malformed,output,raw,expected_blob=expected)
            erroneous=annotation(digest)
            erroneous["annotations"][0]["crop_png_sha256"]=original["figures"][0]["crop_png_sha256"]
            erroneous["annotations"][0]["visible_points"]["crown"]["crown_right"]=[5,100]
            with self.assertRaisesRegex(ValueError,"inverted"):
                measure(erroneous,output,raw,expected_blob=expected)
            stale=annotation(digest)
            stale["annotations"][0]["crop_png_sha256"]="f"*64
            with self.assertRaisesRegex(ValueError,"different exact print crop"):
                measure(stale,output,raw,expected_blob=expected)
            wrong_pdf=annotation("f"*64)
            with self.assertRaisesRegex(ValueError,"authenticated PDF"):
                measure(wrong_pdf,output,raw,expected_blob=expected)

            # An adversary edits a crop and updates its own claimed SHA:
            # original-PDF pixel replay must still reject the false evidence.
            png=output/"p14-twist-fork-front.png"
            with Image.open(png) as picture:
                picture=picture.copy()
                picture.putpixel((0,0),(123,45,67))
                picture.save(png,format="PNG")
            receipt_path=output/"source-crops.json"
            claimed=json.loads(receipt_path.read_text(encoding="utf-8"))
            claimed["figures"][0]["crop_png_sha256"]=hashlib.sha256(
                png.read_bytes()).hexdigest()
            receipt_path.write_text(json.dumps(claimed),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"do not match actual authenticated PDF"):
                measure(first,output,raw,expected_blob=expected)


if __name__=="__main__":
    unittest.main()
