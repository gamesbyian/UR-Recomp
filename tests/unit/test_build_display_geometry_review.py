import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.build_display_geometry_review import build_report, candidate_report, render_html


def write_bmp(path: Path, width: int = 4, height: int = 4) -> None:
    bpp = 24
    stride = ((width * 3 + 3) // 4) * 4
    pixel_bytes = bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row.extend(((x * 40) & 0xFF, (y * 40) & 0xFF, ((x + y) * 30) & 0xFF))
        row.extend(b"\0" * (stride - width * 3))
        pixel_bytes.extend(row)
    offset = 54
    size = offset + len(pixel_bytes)
    header = bytearray()
    header += b"BM"
    header += struct.pack("<IHHI", size, 0, 0, offset)
    header += struct.pack(
        "<IiiHHIIiiII",
        40, width, height, 1, bpp, 0, len(pixel_bytes), 2835, 2835, 0, 0
    )
    path.write_bytes(header + pixel_bytes)


class DisplayGeometryReviewTests(unittest.TestCase):
    def test_candidate_uses_margin_derivation(self):
        row = candidate_report(
            width=256,
            height=224,
            candidate={
                "id": "crt",
                "pixel_aspect": "7:6",
                "target_aspect": "16:9",
                "crop_top": 0,
                "crop_bottom": 0,
            },
        )
        self.assertEqual(row["derived_16x9"]["materializer_margin_pixels"], 48)
        self.assertTrue(row["derived_16x9"]["capacity_sufficient"])

    def test_square_full_height_fits_validated_plus72_capacity(self):
        row = candidate_report(
            width=256,
            height=224,
            candidate={
                "id": "raw",
                "pixel_aspect": "1:1",
                "target_aspect": "16:9",
                "crop_top": 0,
                "crop_bottom": 0,
            },
        )
        self.assertEqual(row["derived_16x9"]["materializer_margin_pixels"], 72)
        self.assertTrue(row["derived_16x9"]["capacity_sufficient"])

    def test_rejects_invalid_crop(self):
        with self.assertRaises(ValueError):
            candidate_report(
                width=256,
                height=224,
                candidate={
                    "id": "bad",
                    "pixel_aspect": "1:1",
                    "crop_top": 112,
                    "crop_bottom": 112,
                },
            )

    def test_builds_self_contained_review_from_canonical_bmp(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            frame = root / "race-entered.fb.bmp"
            write_bmp(frame)
            report = build_report(
                [frame],
                [{
                    "id": "raw",
                    "label": "Raw",
                    "pixel_aspect": "1:1",
                    "target_aspect": "16:9",
                    "crop_top": 0,
                    "crop_bottom": 0,
                }],
            )
            self.assertEqual(report["framebuffer_geometry"], [4, 4])
            self.assertEqual(report["captures"][0]["tag"], "race-entered")
            rendered = render_html(report)
            self.assertIn("data:image/bmp;base64,", rendered)
            self.assertIn("Diagnostic only.", rendered)
            self.assertIn("Raw · race-entered", rendered)


if __name__ == "__main__":
    unittest.main()
