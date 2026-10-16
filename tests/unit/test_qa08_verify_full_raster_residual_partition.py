"""Adversarial byte-level checks for the original/native 524-frame raster classifier."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("qa08_partition",
    ROOT/"tools/qa08_verify_full_raster_residual_partition.py")
qa=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

class SourcePartitionByteTest(unittest.TestCase):
    def test_green6_full_2x2_and_disjoint_gray_mask(self):
        source=(bytes((82,74,90,0))+bytes((132,132,132,0))+
                bytes((8,8,8,0))+bytes((0,0,0,0)))
        native=(bytes((90,66,74,255))+bytes((123,123,123,255))+
                bytes((8,8,8,255))+bytes((0,0,0,255)))
        value=qa.compare(source,native,width=2,height=2)
        self.assertEqual((value["wrong"],value["gray"],value["nongray"]),(2,1,1))
        self.assertEqual(value["bounds"],[0,0,1,0])
        self.assertEqual(value["mask"],b"\x01\x01\x00\x00")
        self.assertEqual(value["nongray_mask"],b"\x01\x00\x00\x00")
        self.assertEqual(value["swatches"][0],([90,74,82],[90,66,74],1))

    def test_green6_to5_roundtrip_not_false_pixel_error(self):
        value=qa.compare(bytes((24,132,148,0)),
                         bytes((148,132,24,255)),width=1,height=1)
        self.assertEqual(value["wrong"],0)
        self.assertIsNone(value["bounds"])

    def test_no_truncation_or_masked_geometry(self):
        original=b"\x00\x00\x00\x00"*4
        native=b"\x00\x00\x00\xff"*4
        for a,b in ((original[:-1],native),(original,native[:-4]),
                    (original+b"x",native)):
            with self.subTest(a=len(a),b=len(b)),self.assertRaises(ValueError):
                qa.compare(a,b,width=2,height=2)

    def test_forged_zip_must_fail_before_member_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"forged.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("qa08-original-2p-fullroute.json",json.dumps({"forged":True}))
            with self.assertRaisesRegex(ValueError,"original ZIP"):
                qa.load("twoplayer",path,path)

    def test_report_is_provenance_bounded_not_release(self):
        d=json.loads((ROOT/"analysis/data/qa08-source-verified-full-partition-20261016.json").read_text())
        self.assertEqual(d["source_original_native_frame_hashes_verified"],524)
        self.assertEqual(d["source_pixels_per_frame"],57344)
        self.assertEqual(d["oneplayer"]["incorrect_RGB5_pixels"],19153)
        self.assertEqual(d["twoplayer"]["incorrect_RGB5_pixels"],385373)
        self.assertEqual(d["twoplayer"]["four_gray_CGRAM_signature_pixels"],318775)
        self.assertEqual(d["twoplayer"]["gray_frames_with_same_296_pixel_medal_mask"],
                         [4176,4512,4848,5184])
        self.assertEqual(d["twoplayer"]["non_gray_medal_mask_SHA256"],
                         "8b83bed21e2ff70ca279f993f4256e1edd64ad8f1edb657ee87554527e0594be")
        for key in ("source_accepted_as_full_CPU_APU_camera_frame_phase",
                    "effective_final_pixel_OBJ_window_and_colour_math_ownership_proven",
                    "released_or_HDriver_art_likeness_approved"):
            self.assertFalse(d[key])
        for pin in qa.PINS.values():
            for name in ("original","windows"):
                self.assertEqual(len(pin[name]),64)
                int(pin[name],16)

if __name__=="__main__":
    unittest.main()
