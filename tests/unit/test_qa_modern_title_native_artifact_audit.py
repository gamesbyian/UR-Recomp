"""Adversarial ROM-free source/P7 -> presented P6 Modern title archive QA.

Synthetic self-consistent receipts are not actual native screenshots. This
tests a stand-alone read-only consumer which is separately used on downloaded
real Windows Actions artifacts and the original packaged PE.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from tools import qa_modern_title_native_artifact_audit as qa


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ModernTitleArchiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.captures = self.root / "title.zip"
        self.package = self.root / "candidate.zip"

    def make(self, *, mut_logo=False, mut_osd_outside=False,
             mut_auth=False, bad_pe=False, missing_root=False):
        native = bytearray(70000)
        native[:2] = b"MZ"
        struct.pack_into("<I", native, 0x3c, 0x80)
        native[0x80:0x84] = b"PE\x00\x00"
        struct.pack_into("<H", native, 0x84, 0x14c if bad_pe else 0x8664)
        struct.pack_into("<H", native, 0x98, 0x20b)
        native_hash = sha(native)
        content = BytesIO()
        with zipfile.ZipFile(content, "w", compression=zipfile.ZIP_DEFLATED) as inner:
            inner.writestr("UR-Recomp-Baldosa-Windows-x64/UniracersSNESRecomp.exe",
                           native)
        with zipfile.ZipFile(self.package, "w") as outer:
            outer.writestr("UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip",
                           content.getvalue())
        with zipfile.ZipFile(self.captures, "w",
                             compression=zipfile.ZIP_DEFLATED) as archive:
            for prefix, width, reduced, route in qa.CASES:
                captures, presented = [], {}
                for stage in ("title", "root"):
                    src = bytearray(b"\x12\x36\xb4\xff" * (width * 224))
                    if mut_logo and stage == "title":
                        src[4 * (40 * width + (width - 238)//2 + 8)] ^= 1
                    p7 = (f"P7\nWIDTH {width}\nHEIGHT 224\nDEPTH 4\n"
                          "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + src
                    name = f"modern-native-{stage}-{width}x224.pam"
                    archive.writestr(f"{prefix}/captures/{name}", p7)
                    captures.append({
                        "stage": stage, "name": name,
                        "guest_frame": (16 if reduced else 48) if stage == "title"
                        else (64 if reduced else 80),
                        "sha256": sha(p7),
                    })
                    rgb = bytearray(b"\x12\x36\xb4" * (width * 224))
                    for y in range(2, 14):
                        for x in range(2, 46):
                            rgb[3*(y*width+x):3*(y*width+x)+3] = b"\x20\x20\x20"
                    if mut_osd_outside and stage == "root":
                        rgb[-3:] = b"\x11\x11\x11"
                    ppm = f"P6\n{width} 224\n255\n".encode() + rgb
                    filename = f"presented-{stage}.ppm"
                    if not (missing_root and stage == "root"):
                        archive.writestr(f"{prefix}/presented/{filename}", ppm)
                    presented[stage] = {
                        "present_frame": (16 if reduced else 32) if stage == "title"
                        else (64 if reduced else 80),
                        "file": filename,
                        "sha256": sha(ppm),
                        "source_match_fraction": 1.0,
                    }
                receipt = {
                    "executable_sha256": native_hash, "captures": captures,
                    "native_presented": {
                        "presentations_examined": 11, "matched": presented},
                    "drawable_aspect": "wide" if width == 342 else "4:3",
                    "reduced_motion": reduced,
                    "native_confirm_route": route,
                }
                archive.writestr(f"{prefix}/native-title-receipt.json",
                                 json.dumps(receipt))
                log = (
                    "UR_BALDOSA_MODERN_TITLE " +
                    ("native_keyboard_enter=1" if route == "keyboard"
                     else "native_p1_start=1") +
                    "\nUR_BALDOSA_MODERN_TITLE entered_root=1\n"
                    "UR_BALDOSA_MODERN_ROOT painted=1\n")
                archive.writestr(f"{prefix}/native-title-run.log", log)
            root = "modern-title-authentic-inert-pr2043"
            ppm = b"P6\n256 224\n255\n" + b"\x12\x36\xb4"*(256*224)
            changed = ppm[:-1] + b"\x33" if mut_auth else ppm
            archive.writestr(
                f"{root}/authentic-disabled-frame-000320-256x224.ppm", ppm)
            archive.writestr(
                f"{root}/authentic-enabled-frame-000320-256x224.ppm", changed)
            receipt = {
                "executable_sha256": native_hash, "original_frames": 320,
                "modern_title_or_root_present": False,
                "identical_host_presented_pixels": True,
                "native_original_visible_pixel_witness": {
                    "modern_root_enabled": {"sha256": sha(changed)},
                    "modern_root_disabled": {"sha256": sha(ppm)},
                },
            }
            archive.writestr(f"{root}/authentic-title-inert-receipt.json",
                             json.dumps(receipt))

    def test_complete_synthetic_host_qualifies_roi_not_entire_raster(self):
        self.make()
        result = qa.audit(self.captures, self.package)
        self.assertEqual(len(result["qualified_routes"]), 4)
        self.assertEqual(result["exe_size_bytes"], 70000)
        for row in result["qualified_routes"]:
            width = row["logical_width"]
            for stage in row["stages"]:
                self.assertEqual(stage["host_only_osd_difference_pixels"], 528)
                self.assertEqual(stage["whole_frame_exact_rgb_pixels"],
                                 width * 224 - 528)
                self.assertEqual(stage["host_osd_bounding_rect"],
                                 [2, 2, 45, 13])
                self.assertEqual(stage["roi_exact_rgb_pixels"],
                                 stage["roi_total_rgb_pixels"])
        self.assertTrue(result["authentic_host_presented_inert"])
        self.assertFalse(result["entire_frame_identical"])
        self.assertFalse(result["final_sdl_drawable_verified"])
        self.assertFalse(result["hardware_approved"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_reject_source_art_changed_inside_verified_title_logo(self):
        self.make(mut_logo=True)
        with self.assertRaisesRegex(qa.AuditError, "title/root ROI changed"):
            qa.audit(self.captures, self.package)

    def test_reject_host_only_pixel_outside_known_osd(self):
        self.make(mut_osd_outside=True)
        with self.assertRaisesRegex(qa.AuditError, "outside bounded OSD"):
            qa.audit(self.captures, self.package)

    def test_reject_inconsistent_authentic_enabled_output(self):
        self.make(mut_auth=True)
        with self.assertRaisesRegex(qa.AuditError, "stock host output differs"):
            qa.audit(self.captures, self.package)

    def test_reject_wrong_architecture_before_any_art_admission(self):
        self.make(bad_pe=True)
        with self.assertRaisesRegex(qa.AuditError, "AMD64 PE32"):
            qa.audit(self.captures, self.package)

    def test_reject_missing_native_host_root_presentation(self):
        self.make(missing_root=True)
        with self.assertRaisesRegex(qa.AuditError, "missing native artifact member"):
            qa.audit(self.captures, self.package)


if __name__ == "__main__":
    unittest.main()
