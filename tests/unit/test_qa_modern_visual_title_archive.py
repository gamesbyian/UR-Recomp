"""ROM-free negative cases for source-to-final-SDL Modern title provenance.

Synthetic bytes test evidence refusal logic only; they are not screenshots of
the game and never establish hardware, artistic or release approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

from tools import qa_modern_visual_actions_archive as audit


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def png32(w: int, h: int, rgba: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    data = b"".join(b"\0" + rgba[y*w*4:(y+1)*w*4] for y in range(h))
    return (audit.PNG_SIG +
            chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0)) +
            chunk(b"IDAT",zlib.compress(data)) + chunk(b"IEND",b""))


class TitleSourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.archive = Path(self.tmp.name)/"original-native-title.zip"

    def pack(self, route: str, *, bad_pixel=False, confirm_before=False,
             late_root=False, missing_source=False, wrong_phase=False,
             actual_output=None):
        stage = "root" if route.startswith("title-transition") else "title"
        reduced = route.endswith("-reduced")
        sw = 256 if route == "title-intro-compact" else 342
        w,h = (actual_output if actual_output is not None else
               ((1024,768) if sw == 256 else (1280,720)))
        prefix = "ur-integrated-title-"+route
        # Native raw source, intentionally not identical to later moving
        # final SDL image: provenance uses its real P7 FNV and stage timing.
        native_rgba = b"\x98\x21\xe4\x00"*(sw*224)
        hash64 = 1469598103934665603
        for c in native_rgba:
            hash64 = ((hash64 ^ c) * 1099511628211) & 0xffffffffffffffff
        native = (f"P7\nWIDTH {sw}\nHEIGHT 224\nDEPTH 4\n"
                  "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()+native_rgba
        if bad_pixel:
            native = native[:-1] + bytes([native[-1]^1])
        rgba = b"\x20\x88\x12\x00"*(w*h)
        p7 = (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\n"
              "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()+rgba
        png = png32(w,h,rgba)
        capture_draw = 48 if stage == "title" else (68 if reduced else 88)
        first = (
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            f"UR_BALDOSA_MODERN_TITLE painted=1 raster={sw}x224 host=modern\n")
        saved = (f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw={capture_draw} "
                 f"guest_frame={capture_draw} output={w}x{h} "
                 "source=SDL_RenderReadPixels backend=sdl3\n")
        source_event = (
            f"UR_BALDOSA_MODERN_TITLE native_capture=1 stage={stage} "
            f"guest_frame={40 if stage=='title' else (60 if reduced else 75)} "
            f"raster={sw}x224 rgba_fnv1a64={hash64:016x} "
            f"path=C:/temp/original-native-source/modern-native-{stage}-{sw}x224.pam\n")
        entered_frame = (61 if late_root else 60) if reduced else (70 if late_root else 74)
        transition = (
            "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60\n"
            f"UR_BALDOSA_MODERN_TITLE entered_root=1 frame={entered_frame}\n"
            "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
            "UR_BALDOSA_MODERN_DESTINATION stage=root "
            "raster=342x224 root=11,10,320,204 source=modern_product_view\n")
        if stage == "title":
            log = first + source_event + (transition if confirm_before else "") + saved
            if not confirm_before:
                log += transition
        else:
            log = first + transition + source_event + saved
        receipt = {
            "schema_version":1,
            "native_process_exit":0,
            "SDL_driver":"windows",
            "native_semantic_route":route,
            "execution_mode":"modern",
            "native_route_marker_observed":True,
            "authentic_isolation_approved":False,
            "actual_sdl_renderer_output":[w,h],
            "observed_in_draw":capture_draw,
            "png_sha256":sha(png),
            "p7_sha256":sha(p7),
            "native_process_log_sha256":sha(log.encode()),
            "exe_sha256":"a"*64,
            "source_sha":"b"*40,
            "title_stage_capture":(
                "intro" if stage=="title" else
                "intro" if wrong_phase else "root-after-native-confirm"),
            "reduced_motion_requested":reduced,
            "visual_approved":False,
            "hardware_approved":False,
            "release_gate_credit":0,
        }
        with zipfile.ZipFile(self.archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(prefix+"/actual-sdl-drawable.png",png)
            z.writestr(prefix+"/readback-receipt.json",json.dumps(receipt))
            z.writestr(prefix+"/probe_first/actual-sdl-drawable.pam",p7)
            z.writestr(prefix+"/probe_first/native-process.log",log)
            if not missing_source:
                z.writestr(
                    prefix+"/probe_first/original-native-source/"
                    f"modern-native-{stage}-{sw}x224.pam",native)

    def test_actual_source_title_wide_compact_and_reduced_routes(self):
        for route in ("title-intro-wide","title-intro-compact",
                      "title-intro-reduced"):
            with self.subTest(route=route):
                self.pack(route)
                rows = audit.verify(self.archive)["captures"]
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]["native_painted_stage_at_capture"],
                                 "title-intro-before-p1")
                self.assertEqual(rows[0]["verified_native_title_source"]
                                 ["title_source_stage"],"title")
                self.assertFalse(rows[0]["human_approved"])

    def test_native_normal_and_reduced_title_to_root(self):
        for route in ("title-transition-root","title-transition-root-reduced"):
            with self.subTest(route=route):
                self.pack(route)
                row = audit.verify(self.archive)["captures"][0]
                self.assertEqual(row["native_painted_stage_at_capture"],
                                 "title-original-p1-to-root")
                self.assertTrue(row["verified_native_title_source"]
                                ["title_original_guest_confirmed_before_sdl"])
                self.assertEqual(row["native_root_geometry_at_capture"],
                                 [11,10,320,204])

    def test_real_compact_480p_title_keeps_original_256_source(self):
        self.pack("title-intro-compact",actual_output=(640,480))
        row=audit.verify(self.archive)["captures"][0]
        self.assertEqual(row["pixels"],[640,480])
        self.assertEqual(row["native_source_canvas_at_capture"],[256,224])

    def test_real_wide_1080p_title_keeps_original_342_source(self):
        self.pack("title-intro-wide",actual_output=(1920,1080))
        row=audit.verify(self.archive)["captures"][0]
        self.assertEqual(row["pixels"],[1920,1080])
        self.assertEqual(row["native_source_canvas_at_capture"],[342,224])

    def test_unmatched_43_window_and_native_wide_title_fail_closed(self):
        self.pack("title-intro-wide",actual_output=(1024,768))
        with self.assertRaisesRegex(audit.AuditError,
                                    "aspect does not match"):
            audit.verify(self.archive)

    def test_reject_source_pixel_edit_even_with_valid_original_png(self):
        self.pack("title-intro-wide",bad_pixel=True)
        with self.assertRaisesRegex(audit.AuditError,"source pixel FNV"):
            audit.verify(self.archive)

    def test_reject_missing_original_source_p7(self):
        self.pack("title-intro-wide",missing_source=True)
        with self.assertRaisesRegex(audit.AuditError,"missing retained member"):
            audit.verify(self.archive)

    def test_reject_title_confirmed_before_its_intro_screenshot(self):
        self.pack("title-intro-wide",confirm_before=True)
        with self.assertRaisesRegex(audit.AuditError,"already confirmed"):
            audit.verify(self.archive)

    def test_reject_wrong_title_phase_receipt(self):
        self.pack("title-transition-root",wrong_phase=True)
        with self.assertRaisesRegex(audit.AuditError,"stage/reduced-motion receipt"):
            audit.verify(self.archive)

    def test_reject_false_instantaneous_normal_title_exit(self):
        self.pack("title-transition-root",late_root=True)
        with self.assertRaisesRegex(audit.AuditError,"exit timing inconsistent"):
            audit.verify(self.archive)

    def test_reject_delayed_reduced_title_exit(self):
        self.pack("title-transition-root-reduced",late_root=True)
        with self.assertRaisesRegex(audit.AuditError,"exit timing inconsistent"):
            audit.verify(self.archive)


if __name__ == "__main__":
    unittest.main()
