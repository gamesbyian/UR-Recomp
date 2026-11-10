"""Dependency-free preview codec acceptance and hostile-source checks."""
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.contributor_gallery import png_preview as p


def fixture(width=128, height=120, color_type=2, filter_type=0):
    channel_count = {2:3, 6:4}[color_type]
    raw = bytearray()
    for y in range(height):
        raw.append(filter_type)
        original = bytes(
            (x*5 + y*3 + channel*41) % 256
            for x in range(width)
            for channel in range(channel_count)
        )
        if filter_type == 1:
            row = bytearray(original)
            for i in range(len(row)):
                row[i] = (original[i] - (original[i-channel_count] if i >= channel_count else 0)) & 255
            raw.extend(row)
        else:
            raw.extend(original)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return p.SIGNATURE + p._chunk(b"IHDR", ihdr) + p._chunk(b"IDAT", zlib.compress(raw)) + p._chunk(b"IEND", b"")


class PngPreviewTests(unittest.TestCase):
    def test_deterministic_small_opaque_rgb_preview(self):
        for color_type in (2, 6):
            for filt in (0, 1):
                with self.subTest(color=color_type, filter=filt), tempfile.TemporaryDirectory() as d:
                    src = Path(d) / "original.png"
                    dest = Path(d) / "preview.png"
                    content = fixture(color_type=color_type, filter_type=filt)
                    src.write_bytes(content)
                    source_hash = hashlib.sha256(content).digest()
                    result = p.preview(src, dest, max_width=64, max_height=64)
                    self.assertEqual((result["width"], result["height"]), (64,60))
                    self.assertEqual(p.dimensions(dest.read_bytes()), (64,60))
                    self.assertEqual(hashlib.sha256(src.read_bytes()).digest(), source_hash)
                    self.assertEqual(dest.read_bytes()[:8], p.SIGNATURE)
                    with self.assertRaises(ValueError):
                        p.preview(src, dest, max_width=64, max_height=64)

    def test_truncated_and_crc_corruption_refused(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "source.png"
            dest = Path(d) / "preview.png"
            src.write_bytes(fixture()[:-6])
            with self.assertRaises(ValueError):
                p.preview(src, dest)
            self.assertFalse(dest.exists())
            data = bytearray(fixture())
            data[40] ^= 16
            src.write_bytes(data)
            with self.assertRaises(ValueError):
                p.preview(src, dest)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
