import struct
import tempfile
import unittest
from pathlib import Path

from tools.analyze_display_active_height import analyze_capture, read_bmp_rgb


def write_bmp(path: Path, rows):
    height = len(rows)
    width = len(rows[0])
    stride = width * 4
    pixel_offset = 54
    size = pixel_offset + stride * height
    header = bytearray(54)
    header[0:2] = b"BM"
    struct.pack_into("<I", header, 2, size)
    struct.pack_into("<I", header, 10, pixel_offset)
    struct.pack_into("<I", header, 14, 40)
    struct.pack_into("<i", header, 18, width)
    struct.pack_into("<i", header, 22, -height)
    struct.pack_into("<H", header, 26, 1)
    struct.pack_into("<H", header, 28, 32)
    struct.pack_into("<I", header, 34, stride * height)
    pixels = bytearray()
    for row in rows:
        for r, g, b in row:
            pixels += bytes((b, g, r, 255))
    path.write_bytes(bytes(header) + bytes(pixels))


class DisplayActiveHeightTests(unittest.TestCase):
    def test_reads_top_down_bmp_and_detects_non_neutral_crop(self):
        a = (10, 20, 30)
        b = (40, 50, 60)
        rows = [
            [b, a, a, a],
            [a, a, a, a],
            [a, a, a, a],
            [a, a, a, a],
            [a, a, a, a],
            [a, a, a, b],
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "frame.bmp"
            write_bmp(path, rows)
            width, height, decoded = read_bmp_rgb(path)
            report = analyze_capture(path, 1, 1)

        self.assertEqual((width, height), (4, 6))
        self.assertEqual(decoded[0][0], b)
        self.assertEqual(decoded[-1][-1], b)
        self.assertFalse(report["crop_content_neutral"])
        self.assertEqual(
            report["distinct_cropped_pixels_vs_nearest_retained_boundary"], 2
        )
        self.assertEqual(report["cropped_pixels"], 8)

    def test_neutral_crop_is_reported_as_neutral(self):
        a = (1, 2, 3)
        rows = [[a] * 3 for _ in range(6)]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "frame.bmp"
            write_bmp(path, rows)
            report = analyze_capture(path, 1, 1)
        self.assertTrue(report["crop_content_neutral"])
        self.assertEqual(
            report["distinct_cropped_pixels_vs_nearest_retained_boundary"], 0
        )


if __name__ == "__main__":
    unittest.main()
