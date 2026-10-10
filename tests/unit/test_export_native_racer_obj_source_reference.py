"""Native P1 source-only PNG crop must be lossless, provenance-verified and non-HD."""
from pathlib import Path
import hashlib
import json
import struct
import tempfile
import unittest
import zlib

from tools.check_baldosa_wide_single_slot_source import HEADER, WIDTH, HEIGHT, read_source
from tools.export_native_racer_obj_source_reference import (
    make_reference, lossless_png,
)


def decode_rgba_png(data: bytes) -> tuple[int, int, bytes]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Not PNG")
    offset, width, height, rows = 8, 0, 0, b""
    while offset < len(data):
        n = struct.unpack(">I", data[offset:offset + 4])[0]
        typ = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + n]
        expected_crc = struct.unpack(">I", data[offset + 8 + n:offset + 12 + n])[0]
        if zlib.crc32(typ + body) & 0xFFFFFFFF != expected_crc:
            raise ValueError("source PNG CRC mismatch")
        if typ == b"IHDR":
            width, height, depth, color, *_ = struct.unpack(">IIBBBBB", body)
            if (depth, color) != (8, 6):
                raise ValueError("not preserved RGBA")
        if typ == b"IDAT":
            rows += zlib.decompress(body)
        if typ == b"IEND":
            break
        offset += 12 + n
    reconstructed = b"".join(
        rows[(i * (width * 4 + 1)) + 1:(i + 1) * (width * 4 + 1)]
        for i in range(height)
    )
    return width, height, reconstructed


class NativeSourceRacerReferenceTests(unittest.TestCase):
    def test_rgba_png_round_trip_exact(self):
        img = bytes((255, 30, 15, 0, 30, 90, 200, 255,
                     100, 40, 200, 254, 0, 0, 0, 0))
        out = lossless_png(img, 2, 2)
        self.assertEqual(decode_rgba_png(out), (2, 2, img))
        with self.assertRaisesRegex(ValueError, "malformed"):
            lossless_png(img[:11], 2, 2)

    def test_real_native_obj_bbox_and_palette_preserved_without_making_hd(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "ur-baldosa-ws342-obj-slot97-frame002208.pam"
            report = root / "ws342_live_1p_0895_source_obj.json"
            raw = bytearray(WIDTH * HEIGHT * 4)
            one = (120 * WIDTH + 100) * 4
            two = (121 * WIDTH + 102) * 4
            raw[one:one + 4] = bytes((255, 66, 77, 255))
            raw[two:two + 4] = bytes((255, 66, 77, 255))
            source.write_bytes(HEADER + raw)
            observed = read_source(source, 97)
            report.write_text(json.dumps({
                "status": "native-1p-source-obj-slot97-frame2208-verified",
                "native_guest_crcs_identical": 5447,
                "independent_one_x_four_x_source_image_pairs": 7,
                "isolated_original_ppu_obj_slot": 97,
                "guest_frame": 2208,
                "no_remove_from_game": True,
                "widescreen_hd_replacement_admitted": False,
                "actual_bg_window_final_winner_proven": False,
                "source_obj_alpha": observed,
            }))
            result, png = make_reference(source, report)
            self.assertEqual(result["status"], "original-ppu-source-reference")
            self.assertEqual(result["native_original_source_opaque_pixels"], 2)
            self.assertEqual(result["native_original_source_bbox"], [100, 120, 102, 121])
            self.assertEqual(result["cropped_rgba_dimensions"], [3, 2])
            expected = (
                bytes((255, 66, 77, 255)) + bytes(8) +
                bytes(8) + bytes((255, 66, 77, 255))
            )
            self.assertEqual(decode_rgba_png(png), (3, 2, expected))
            self.assertEqual(result["original_visible_rgba_color_counts"],
                             {"FF424DFF": 2})
            self.assertEqual(result["cropped_raw_rgba_sha256"],
                             hashlib.sha256(expected).hexdigest())
            self.assertFalse(result["new_4x_authored_art_approved"])
            self.assertFalse(result["final_bg_window_priority_proven"])

            broken = json.loads(report.read_text())
            broken["source_obj_alpha"]["source_sha256"] = "0" * 64
            report.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ValueError, "authoritative"):
                make_reference(source, report)
            broken["source_obj_alpha"] = observed
            broken["no_remove_from_game"] = False
            report.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ValueError, "provenance"):
                make_reference(source, report)

    def test_all_transparent_native_source_is_an_honest_negative(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "ur-baldosa-ws342-obj-slot97-frame002208.pam"
            report = root / "valid.json"
            source.write_bytes(HEADER + bytes(WIDTH * HEIGHT * 4))
            native = read_source(source, 97)
            report.write_text(json.dumps({
                "status": "native-1p-source-obj-slot97-frame2208-verified",
                "native_guest_crcs_identical": 5447,
                "independent_one_x_four_x_source_image_pairs": 7,
                "isolated_original_ppu_obj_slot": 97,
                "guest_frame": 2208,
                "no_remove_from_game": True,
                "widescreen_hd_replacement_admitted": False,
                "actual_bg_window_final_winner_proven": False,
                "source_obj_alpha": native,
            }))
            result, png = make_reference(source, report)
            self.assertIsNone(png)
            self.assertEqual(result["status"], "source-empty-no-image")
            self.assertEqual(result["native_original_source_opaque_pixels"], 0)
            self.assertFalse(result["png_rendered_from_original_source"])


if __name__ == "__main__":
    unittest.main()
