"""ROM-free immutable receipt controls for 20 authentic original Mesen sprite screens."""
import copy
import json
from pathlib import Path
import unittest

from tools.art.audit_original_mesen_sparse_pose_correspondence import (
    TICKS, SOURCE_ZIP_SHA, validate_receipt, audit_source,
)


def saved():
    return json.loads((Path(__file__).resolve().parents[2]/
        "analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json").read_text())


class SparseOriginalPoseCorrespondenceTests(unittest.TestCase):
    def test_frozen_original_40_racer_pixels_and_holdout_roles(self):
        d=saved()
        validate_receipt(d)
        self.assertEqual(d["source_zip_sha256"],SOURCE_ZIP_SHA)
        self.assertEqual([x["tick"] for x in d["samples"]],list(TICKS))
        self.assertEqual(d["summary"]["source_opaque_pixels"],12937)
        self.assertEqual(d["summary"]["red_plus_13_RGB"],521)
        self.assertEqual(d["summary"]["direct_source_RGB"],12416)
        self.assertEqual(d["summary"]["unexplained_RGB"],0)
        self.assertEqual(d["samples"][0]["blue"]["screen_xy"],[82,158])
        self.assertEqual(d["samples"][0]["red"]["screen_xy"],[48,48])
        self.assertEqual(d["samples"][-1]["red"]["screen_xy"],[104,46])
        self.assertEqual([j["frozen_role"] for j in d["original_source_corpus_frozen_joins"]],
                         ["withheld","fit"])
        self.assertEqual([j["tick"] for j in d["original_source_corpus_frozen_joins"]],[1601,1952])
        self.assertFalse(d["original_1994_source_3d_model_rig_camera_recovered"])
        self.assertFalse(d["original_ppu_colour_math_or_pixel_layer_ownership_proved"])
        self.assertFalse(d["experimental_2026_glb_pose_registration_verified"])
        self.assertFalse(d["owner_likeness_approved"])

    def test_receipt_tampering_and_3d_overclaim_are_refused(self):
        d=saved()
        for path,val in (("source_zip_sha256","a"*64),
                         ("source_no_frame_skip",False),
                         ("original_1994_source_3d_model_rig_camera_recovered",True),
                         ("source_original_per_scanline_oam_mutations_proved",True),
                         ("owner_likeness_approved",True)):
            changed=copy.deepcopy(d)
            changed[path]=val
            with self.subTest(field=path),self.assertRaises(ValueError):
                validate_receipt(changed)
        for key,val in (("red_plus_13",100),("exact",0),("opaque",999),
                        ("classification_sha256","0")):
            changed=copy.deepcopy(d)
            changed["samples"][0]["red"][key]=val
            with self.subTest(field=key),self.assertRaises(ValueError):
                validate_receipt(changed)
        changed=copy.deepcopy(d)
        changed["samples"][1]["tick"]=d["samples"][0]["tick"]
        with self.assertRaisesRegex(ValueError,"tick"):
            validate_receipt(changed)

    def test_source_archive_identity_fail_closed_without_rom_execution(self):
        import tempfile
        d=saved()
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/"not-the-authentic-original.zip"
            source.write_bytes(b"PK\x03\x04FAKE")
            with self.assertRaisesRegex(ValueError,"authentic"):
                audit_source(source,d)


if __name__=="__main__":
    unittest.main()
