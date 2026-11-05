"""Exact original PDF proof and four reference crop controls, no guessed anatomy."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.extract_manual_3d_reference_views import (
    BASIS,DPI,FIGURES,PAGE_COUNT,SOURCE,SOURCE_BLOB_SHA1,
    authenticate_pdf,git_blob_sha1,crop_box,extract,
)
from tools.art.measure_unicycle_reference import SOURCE_KINDS


class OriginalManual3DCropTests(unittest.TestCase):
    def test_repository_has_exact_official_pdf_blob_without_external_download(self):
        self.assertIn("official-manual",SOURCE_KINDS)
        self.assertEqual(len(SOURCE_BLOB_SHA1),40)
        self.assertEqual(SOURCE.name,"Uniracers-USA-manual.pdf")
        if SOURCE.is_file():
            authentic=authenticate_pdf(SOURCE.read_bytes())
            self.assertEqual(authentic["source_git_blob_sha1"],SOURCE_BLOB_SHA1)
            self.assertEqual(authentic["source_pdf_size"],6006270)

    def test_git_pdf_object_identity_refuses_byte_substitution(self):
        fake=b"%PDF-1.7\nsynthetic test manual\n"
        digest=git_blob_sha1(fake)
        self.assertEqual(digest,hashlib.sha1(
            ("blob "+str(len(fake))+"\0").encode()+fake).hexdigest())
        self.assertEqual(authenticate_pdf(fake,digest)["source_pdf_sha256"],
                         hashlib.sha256(fake).hexdigest())
        for changed in (b"invalid",fake+b" ",fake[:-1],b""):
            with self.assertRaises(ValueError):
                authenticate_pdf(changed,digest)

    def test_exact_four_full_page_manual_figures_and_pixel_basis(self):
        self.assertEqual((BASIS,DPI,PAGE_COUNT),((1024,1497),144,40))
        self.assertEqual([(row[0],row[1]) for row in FIGURES],[
            ("p14-twist-fork-front",13),("p14-zee-flip-oblique",13),
            ("p15-mega-underside",14),("p16-menu-saddle",15)])
        for row in FIGURES:
            self.assertEqual(row[1]+1,int(row[0].split("-")[0][1:]))
            self.assertEqual(crop_box(2048,2994,row[2]),
                             tuple(x*2 for x in row[2]))
        for box in ((-1,0,20,30),(0,0,1025,100),
                    (2,3,2,40),(1,1,2,2),(0,1,8,0)):
            with self.assertRaises(ValueError):
                crop_box(2048,2994,box)
        with self.assertRaises(ValueError):
            crop_box(100,2994,FIGURES[0][2])

    @unittest.skipUnless(importlib.util.find_spec("fitz") and
                         importlib.util.find_spec("PIL"),"optional PDF rendering absent")
    def test_synthetic_pdf_print_crops_are_atomic_and_template_never_passes_as_measurement(self):
        import fitz
        from tools.art.measure_unicycle_reference import measure
        doc=fitz.open()
        for i in range(40):
            page=doc.new_page(width=512,height=749)
            if i in (13,14,15):
                page.draw_rect(fitz.Rect(100,150,420,720),color=(1,0,0))
        raw=doc.tobytes()
        doc.close()
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)/"out"
            evidence=extract(raw,dest)
            self.assertEqual(len(evidence["figures"]),4)
            self.assertEqual(len(list(dest.glob("*.png"))),4)
            self.assertFalse(evidence["same_historical_3d_mesh_as_source_game_proven"])
            template=json.loads((dest/"landmarks.UNANNOTATED.json").read_text("utf-8"))
            self.assertTrue(all(r["view"]["pixel_aspect"]=="square"
                                for r in template["views"]))
            with self.assertRaises(ValueError):
                measure(dest/"landmarks.UNANNOTATED.json")
            with self.assertRaises(FileExistsError):
                extract(raw,dest)


if __name__=="__main__":
    unittest.main()
