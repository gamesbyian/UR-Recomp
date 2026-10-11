"""Fail-closed original top OBJ PNG crop from authenticated native slot98/99."""
from pathlib import Path
import hashlib
import json
import struct
import tempfile
import unittest

from tools.check_baldosa_wide_single_slot_source import HEADER, WIDTH, HEIGHT, read_source
from tools.export_native_racer_obj_source_reference import make_reference


def pam(path: Path, slot: int, x: int, y: int, rgba: bytes) -> dict:
    buf = bytearray(WIDTH * HEIGHT * 4)
    if rgba[3]:
        i = (y * WIDTH + x) * 4
        buf[i:i + 4] = rgba
    path.write_bytes(HEADER + buf)
    return read_source(path, slot)


class TopSourceReferenceTests(unittest.TestCase):
    def fixture(self, root: Path):
        top98 = root / "ur-baldosa-ws342-obj-slot98-frame002208.pam"
        top99 = root / "ur-baldosa-ws342-obj-slot99-frame002208.pam"
        m98 = pam(top98, 98, 45, 102, bytes((214, 64, 10, 255)))
        m99 = pam(top99, 99, 120, 100, bytes((13, 17, 70, 255)))
        records = [
            {"original_oam_slot": 98, "native_source": m98,
             "rgba_sha256": m98["source_sha256"],
             "original_1x_and_4x_remained_pixel_identical": True},
            {"original_oam_slot": 99, "native_source": m99,
             "rgba_sha256": m99["source_sha256"],
             "original_1x_and_4x_remained_pixel_identical": True},
        ]
        proof = {
            "status": "native-1p-paired-top-oam-source-truth",
            "native_guest_frame": 2208,
            "native_original_guest_crc_identical": 5447,
            "native_1x_and_4x_source_frames_identical": 7,
            "independent_original_guest_processes": 5,
            "no_sprite_removal_or_guest_mutation": True,
            "source_slot_emission_accepted": True,
            "individual_final_bg_or_obj_priority_accepted": False,
            "authored_hd_or_wide_replacement_accepted": False,
            "windows_beta_accepted": False,
            "original_top_slot98_and_slot99_sources": records,
        }
        dest = root / "top-native.json"
        dest.write_text(json.dumps(proof))
        return top98, top99, dest, proof

    def test_both_separately_proven_native_top_slots_export_exact_1px_references(self):
        with tempfile.TemporaryDirectory() as td:
            top98, top99, report, proof = self.fixture(Path(td))
            for slot, path, rgb in ((98, top98, "D6400AFF"), (99, top99, "0D1146FF")):
                meta, image = make_reference(path, report, slot=slot)
                self.assertEqual(meta["native_isolated_obj_slot"], slot)
                self.assertEqual(meta["native_original_source_opaque_pixels"], 1)
                self.assertEqual(meta["cropped_rgba_dimensions"], [1, 1])
                self.assertEqual(meta["original_visible_rgba_color_counts"], {rgb: 1})
                self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(meta["lossless_png_sha256"], hashlib.sha256(image).hexdigest())
                self.assertFalse(meta["new_4x_authored_art_approved"])
                self.assertFalse(meta["widescreen_hd_admission"])

            proof["native_original_guest_crc_identical"] = 5446
            report.write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError, "provenance"):
                make_reference(top98, report, slot=98)

            proof["native_original_guest_crc_identical"] = 5447
            proof["original_top_slot98_and_slot99_sources"][0]["rgba_sha256"] = "0" * 64
            report.write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError, "digest"):
                make_reference(top98, report, slot=98)

            proof["original_top_slot98_and_slot99_sources"][0]["rgba_sha256"] = (
                read_source(top98, 98)["source_sha256"]
            )
            proof["original_top_slot98_and_slot99_sources"].reverse()
            report.write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError, "attribution"):
                make_reference(top98, report, slot=98)

    def test_top_report_cannot_forge_old_bottom_native_proof(self):
        with tempfile.TemporaryDirectory() as td:
            top98, top99, report, proof = self.fixture(Path(td))
            with self.assertRaisesRegex(ValueError, "filename"):
                make_reference(top98, report, slot=97)
            with self.assertRaisesRegex(ValueError, "in scope"):
                make_reference(top98, report, slot=96)
            with self.assertRaisesRegex(ValueError, "in scope"):
                make_reference(top98, report, slot=98, frame=2209)


if __name__ == "__main__":
    unittest.main()
