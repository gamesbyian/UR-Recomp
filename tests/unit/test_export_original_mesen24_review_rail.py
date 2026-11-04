"""ROM/PPU-backed 48-frame viewer-reference export and safe PNG contracts."""
import hashlib
import json
from pathlib import Path
import struct
import unittest
import zlib

from tools.art.export_original_mesen24_review_rail import (
    POSE_SHA, SCHEMA, export, png_rgba64, sha,
)

ROOT = Path(__file__).resolve().parents[2]


def png_pixels(data):
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    pos, compressed = 8, bytearray()
    while pos < len(data):
        count = struct.unpack(">I", data[pos:pos+4])[0]
        tag = data[pos+4:pos+8]
        payload = data[pos+8:pos+8+count]
        crc = struct.unpack(">I", data[pos+8+count:pos+12+count])[0]
        assert crc == zlib.crc32(tag+payload)&0xffffffff
        if tag == b"IHDR":
            assert payload == struct.pack(">IIBBBBB",64,64,8,6,0,0,0)
        if tag == b"IDAT":
            compressed.extend(payload)
        pos += 12+count
    rows = zlib.decompress(compressed)
    assert len(rows) == 64*257
    assert all(rows[y*257] == 0 for y in range(64))
    return b"".join(rows[y*257+1:(y+1)*257] for y in range(64))


class OriginalMesen24ReviewRailTests(unittest.TestCase):
    def test_png_encoder_lossless_alpha_and_bad_sizes(self):
        image = bytes([0, 0, 0, 0])*4095 + bytes([255, 5, 91, 255])
        self.assertEqual(png_pixels(png_rgba64(image)), image)
        with self.assertRaises(ValueError):
            png_rgba64(b"bad")

    def test_source_identity_required_before_export(self):
        with self.assertRaisesRegex(ValueError, "ROM"):
            export(b"", b"", b"")

    def test_actual_48_rom_identified_original_sprites(self):
        rom = (ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        original = (ROOT/"analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip").read_bytes()
        receipt = (ROOT/"analysis/data/racer-original-mesen24-exact-ROM-pose-IDs-20261103.json").read_bytes()
        self.assertEqual(sha(receipt), POSE_SHA)
        report, images = export(rom, original, receipt)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(len(report["frames"]), 48)
        self.assertEqual(len(images), 48)
        self.assertEqual(report["display_pixel_aspect"], [7, 6])
        self.assertFalse(report["original_1994_3D_mesh_camera_pose_recovered"])
        self.assertFalse(report["original_source_to_2026_GLB_joint_pose_verified"])
        self.assertEqual([r["role"] for r in report["frames"]],
                         ["blue"]*24+["red"]*24)
        first_blue, first_red = report["frames"][0], report["frames"][24]
        self.assertEqual(first_blue["original_ROM_frame_ID"], 0x00fd)
        self.assertEqual(first_red["original_ROM_frame_ID"], 0x0439)
        for row in report["frames"]:
            self.assertEqual(row["original_ROM_frame_ID"],
                             64*row["source_phase_index"]+row["source_orientation_index"])
            png = images[row["png"]]
            self.assertEqual(hashlib.sha256(png).hexdigest(), row["png_sha256"])
            rgba = png_pixels(png)
            self.assertEqual(hashlib.sha256(rgba).hexdigest(), row["source_RGBA_sha256"])
            self.assertGreater(sum(rgba[3::4]),0)
        with self.assertRaisesRegex(ValueError,"authenticated original"):
            export(rom, original+b"X", receipt)


if __name__ == "__main__":
    unittest.main()
