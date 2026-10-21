"""ROM-free adversarial tests for native Windows Actions ZIP transport evidence."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

from tools import qa_modern_visual_actions_archive as qa


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png_rgba(w,h,rgba):
    def chunk(name,data):
        return (struct.pack(">I",len(data))+name+data+
                struct.pack(">I",zlib.crc32(name+data)&0xffffffff))
    ihdr=struct.pack(">IIBBBBB",w,h,8,6,0,0,0)
    rows=b"".join(b"\0"+rgba[y*w*4:(y+1)*w*4] for y in range(h))
    return qa.PNG_SIG+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(rows))+chunk(b"IEND",b"")


class ActionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"images.zip"
        self.folder="real-native-route"
        self.w,self.h=320,224
        rgba=b"\xff\x22\x50\x00"*(self.w*self.h)
        self.p7=(f"P7\nWIDTH {self.w}\nHEIGHT {self.h}\nDEPTH 4\n"
                 "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()+rgba
        self.png=png_rgba(self.w,self.h,rgba)
        self.log=(f"[snes_load] name=UNIRACERS\n"
                  f"UR_BALDOSA_MODERN_DESTINATION stage=root raster=256x224 root=8,10,240,204 source=modern_product_view\n"
                  f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 guest_frame=40 "
                  f"output={self.w}x{self.h} source=SDL_RenderReadPixels backend=sdl3\n").encode()
        self.receipt={
            "actual_sdl_renderer_output":[self.w,self.h],
            "observed_in_draw":40,"png_sha256":sha(self.png),"p7_sha256":sha(self.p7),
            "native_process_log_sha256":sha(self.log),"exe_sha256":"a"*64,
            "source_sha":"b"*40,"native_semantic_route":"root-quit",
            "visual_approved":False,"hardware_approved":False,"release_gate_credit":0,
        }
        self.stage="probe_first"
        self.omit_p7=False
        self.omit_log=False

    def pack(self):
        with zipfile.ZipFile(self.path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            f=self.folder
            z.writestr(f+"/readback-receipt.json",json.dumps(self.receipt))
            z.writestr(f+"/actual-sdl-drawable.png",self.png)
            if not self.omit_p7:
                z.writestr(f+"/"+self.stage+"/actual-sdl-drawable.pam",self.p7)
            if not self.omit_log:
                z.writestr(f+"/"+self.stage+"/native-process.log",self.log)

    def test_normal_first_capture(self):
        self.pack()
        report=qa.verify(self.path)
        self.assertEqual(len(report["captures"]),1)
        self.assertTrue(report["captures"][0]["original_p7"].endswith(
            "probe_first/actual-sdl-drawable.pam"))
        self.assertFalse(report["visual_approved"])
        self.assertEqual(report["release_gate_credit"],0)

    def test_reject_other_native_checkout_or_other_executable_epoch(self):
        self.pack()
        self.assertEqual(len(qa.verify(
            self.path,expected_source_sha="b"*40,expected_exe_sha="a"*64)["captures"]),1)
        with self.assertRaisesRegex(qa.AuditError,"required source SHA"):
            qa.verify(self.path,expected_source_sha="c"*40)
        with self.assertRaisesRegex(qa.AuditError,"required Windows PE"):
            qa.verify(self.path,expected_exe_sha="d"*64)

    def test_fresh_process_selected_second_capture(self):
        self.stage="capture_observed"
        self.pack()
        report=qa.verify(self.path)
        self.assertIn("capture_observed",report["captures"][0]["original_p7"])
        self.assertIn("capture_observed",report["captures"][0]["successful_process_log"])

    def test_paused_guest_frame_is_distinct_from_sdl_present_ordinal(self):
        self.log=self.log.replace(b"guest_frame=40", b"guest_frame=12")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        report=qa.verify(self.path)
        self.assertEqual(report["captures"][0]["guest_frame_witness"],12)
        self.assertEqual(report["captures"][0]["exact_rgba_bytes"],320*224*4)

    def test_missing_selected_p7_cannot_be_laundered_by_png(self):
        self.stage="capture_observed"
        self.omit_p7=True
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"missing exact successful P7"):
            qa.verify(self.path)

    def test_retained_refused_probe_log_cannot_replace_success(self):
        self.stage="capture_observed"
        self.omit_log=True
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"missing exact successful native route log"):
            qa.verify(self.path)

    def test_hash_correct_but_png_pixels_differ_from_p7(self):
        self.png=png_rgba(self.w,self.h,b"\x01\x02\x03\x04"*(self.w*self.h))
        self.receipt["png_sha256"]=sha(self.png)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"P7 differs from actual PNG"):
            qa.verify(self.path)

    def test_forged_producer_readback_marker_fails(self):
        self.log=b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 guest_frame=40 output=320x224 source=other\n"
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"does not witness successful SDL3"):
            qa.verify(self.path)

    def test_root_pixels_cannot_be_relabelled_as_records_screenshot(self):
        self.receipt["native_semantic_route"]="records-keyboard"
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"native semantic destination"):
            qa.verify(self.path)

    def test_stale_records_stage_rejected_when_root_repainted_before_capture(self):
        self.receipt["native_semantic_route"]="records-keyboard"
        self.log=self.log.replace(
            b"UR_BALDOSA_MODERN_DESTINATION stage=root ",
            b"UR_BALDOSA_MODERN_DESTINATION stage=records-1p raster=256x224 root=8,10,240,204 source=modern_product_view\n"
            b"UR_BALDOSA_MODERN_DESTINATION stage=root ")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"native semantic destination"):
            qa.verify(self.path)

    def test_last_records_1p_stage_admitted_not_later_root(self):
        self.receipt["native_semantic_route"]="records-keyboard"
        self.log=self.log.replace(
            b"UR_BALDOSA_MODERN_DESTINATION stage=root ",
            b"UR_BALDOSA_MODERN_DESTINATION stage=records-1p ")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        result=qa.verify(self.path)
        self.assertEqual(result["captures"][0]["native_painted_stage_at_capture"],
                         "records-1p")

    def test_authentic_original_refuses_modern_stage_even_with_valid_sdl3(self):
        self.receipt["native_semantic_route"]="authentic-stock"
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"Authentic capture contains Modern"):
            qa.verify(self.path)

    def test_authentic_original_requires_stock_load_without_modern_stage(self):
        self.receipt["native_semantic_route"]="authentic-stock"
        self.log=self.log.replace(
            b"UR_BALDOSA_MODERN_DESTINATION stage=root raster=256x224 root=8,10,240,204 source=modern_product_view\n",b"")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        result=qa.verify(self.path)
        self.assertEqual(result["captures"][0]["native_painted_stage_at_capture"],
                         "authentic-original")

    def test_342_canvas_cannot_masquerade_as_compact_43_source(self):
        self.log=self.log.replace(
            b"raster=256x224 root=8,10,240,204",
            b"raster=342x224 root=11,10,320,204")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"source canvas/root geometry mismatch"):
            qa.verify(self.path)

    def test_geometry_metadata_in_accepted_original_compact_capture(self):
        self.pack()
        result=qa.verify(self.path)["captures"][0]
        self.assertEqual(result["native_source_canvas_at_capture"],[256,224])
        self.assertEqual(result["native_root_geometry_at_capture"],[8,10,240,204])

    def test_real_play_guest_handoff_happens_before_sdl_present(self):
        self.receipt["native_semantic_route"]="play-stock-handoff"
        self.log=self.log.replace(
            b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved",
            b"UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
            b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        report=qa.verify(self.path)["captures"][0]
        self.assertEqual(report["native_painted_stage_at_capture"],
                         "original-stock-1p-after-handoff")
        self.assertEqual(report["native_source_canvas_at_capture"],[256,224])
        self.assertIsNone(report["native_root_geometry_at_capture"])

    def test_play_request_without_guest_handoff_is_not_proof(self):
        self.receipt["native_semantic_route"]="play-stock-handoff"
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"stock handoff was not witnessed"):
            qa.verify(self.path)

    def test_play_guest_handoff_after_snapshot_is_not_proof(self):
        self.receipt["native_semantic_route"]="play-stock-handoff"
        self.log += b"UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"stock handoff was not witnessed"):
            qa.verify(self.path)

    def test_repainted_modern_after_stock_handoff_is_rejected(self):
        self.receipt["native_semantic_route"]="play-stock-handoff"
        self.log=self.log.replace(
            b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved",
            b"UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
            b"UR_BALDOSA_MODERN_DESTINATION stage=root raster=256x224 root=8,10,240,204 source=modern_product_view\n"
            b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved")
        self.receipt["native_process_log_sha256"]=sha(self.log)
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"painted again"):
            qa.verify(self.path)

    def test_phony_approval_refused(self):
        self.receipt["visual_approved"]=True
        self.pack()
        with self.assertRaisesRegex(qa.AuditError,"overclaims"):
            qa.verify(self.path)

    def test_archive_member_traversal_refused(self):
        self.pack()
        with zipfile.ZipFile(self.path,"a") as z:
            z.writestr("../malicious.txt","whatever")
        with self.assertRaisesRegex(qa.AuditError,"traversing"):
            qa.verify(self.path)


if __name__=="__main__":
    unittest.main()
