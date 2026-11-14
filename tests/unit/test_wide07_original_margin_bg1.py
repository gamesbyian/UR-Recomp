"""Adversarial pure controls for original-derived WIDE-07 BG1 pixel evidence."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import wide07_original_margin_bg1 as margin
from compare_wide07_original_native_rgb5 import source_course_tile


def make_original_map():
    wram = bytearray(131072)
    vram = bytearray(65536)
    def write16(dst, offset, value):
        struct.pack_into("<H", dst, offset, value)
    write16(wram, 0x4f1, 8)
    write16(wram, 0x4f3, 8)
    for coarse_y in range(8):
        for coarse_x in range(8):
            record = coarse_y * 8 + coarse_x
            write16(wram, 0x1000f + record * 2, record)
            for inner_y in range(4):
                for inner_x in range(4):
                    x, y = coarse_x * 4 + inner_x, coarse_y * 4 + inner_y
                    write16(wram, 0x1800f + record * 32 + (inner_y * 4 + inner_x) * 2,
                            1 + x + 32 * y)
    for y in range(32):
        for x in range(32):
            t = source_course_tile(bytes(wram), x, y)
            write16(vram, (0xc00 + y * 32 + x) * 2, t)
    return bytes(wram), bytes(vram)


class OriginalMarginTests(unittest.TestCase):
    def test_source_only_original_course_to_original_vram_alignment(self):
        wram, vram = make_original_map()
        dx, dy, matched = margin.calibrate_source_only(
            wram, vram, camera_x=0, camera_y=0,
            scroll_x=0, scroll_y=0, map_base=0xc00)
        self.assertEqual((dx, dy, matched), (0, 1, 256 * 224))

    def test_ambiguous_original_source_cannot_be_aligned_by_native_image(self):
        wram = bytearray(131072)
        struct.pack_into("<HH", wram, 0x4f1, 8, 8)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            margin.calibrate_source_only(bytes(wram), bytes(65536),
                camera_x=0, camera_y=0, scroll_x=0, scroll_y=0, map_base=0xc00)

    def test_planar_4bpp_pixel_and_transparency(self):
        vram = bytearray(65536)
        cgram = bytearray(512)
        for offset in (0, 1, 16, 17):
            vram[0x4000 + offset] = 0x80  # tile 0, pixel (0,0), palette index 15
        struct.pack_into("<H", cgram, 30, 0x7c1f)  # R/B max
        struct.pack_into("<H", cgram, 62, 0x03e0)  # second palette green
        self.assertEqual(margin.bg1_pixel(0, 0, 0, vram, cgram, 0x2000), (31, 0, 31))
        self.assertEqual(margin.bg1_pixel(0x4000, 15, 0, vram, cgram, 0x2000), (31, 0, 31))
        self.assertEqual(margin.bg1_pixel(0x8000, 0, 15, vram, cgram, 0x2000), (31, 0, 31))
        self.assertEqual(margin.bg1_pixel(0x400, 0, 0, vram, cgram, 0x2000), (0, 31, 0))
        self.assertIsNone(margin.bg1_pixel(0, 1, 0, vram, cgram, 0x2000))

    def test_original_64x64_bg2_map_quadrants_and_palette(self):
        vram = bytearray(65536)
        cgram = bytearray(512)
        bg2 = {"tile16": 0, "scsize": 3, "scbase": "7000",
               "namebase": "1000", "hofs": 0, "vofs": 0}
        # Force an opaque red pixel at tile (0,0) in all four quadrants.
        # Quadrant offsets are 0,1024,2048,3072 original VRAM words.
        for quadrant, base in enumerate((0, 1024, 2048, 3072)):
            struct.pack_into("<H", vram, 2 * (0x7000 + base), quadrant)
            vram[0x2000 + quadrant * 32] = 0x80
        struct.pack_into("<H", cgram, 2, 0x001f)
        for (x, y) in ((0, 0), (256, 0), (0, 256), (256, 256)):
            self.assertEqual(
                margin.bg2_pixel(vram, cgram, bg2, x, y), (31, 0, 0))
        self.assertIsNone(margin.bg2_pixel(vram, cgram, bg2, 1, 0))
        with self.assertRaisesRegex(ValueError, "BG2"):
            margin.bg2_pixel(vram, cgram, {**bg2, "scsize": 0}, 0, 0)

    def test_bg2_tile_flips_and_second_palette(self):
        vram = bytearray(65536)
        cgram = bytearray(512)
        bg2 = {"tile16": 0, "scsize": 3, "scbase": "7000",
               "namebase": "1000", "hofs": 0, "vofs": 0}
        vram[0x2000] = 0x80
        struct.pack_into("<H", cgram, 2 * 17, 0x03e0)
        for (x, y, flags) in ((0, 0, 0), (7, 0, 0x4000),
                              (0, 7, 0x8000), (7, 7, 0xc000)):
            struct.pack_into("<H", vram, 2 * 0x7000, 0x0400 | flags)
            self.assertEqual(
                margin.bg2_pixel(vram, cgram, bg2, x, y), (0, 31, 0))

    def test_visible_scanline_scroll_writes_are_not_ignored(self):
        header = "#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
        self.assertTrue(margin.source_scanline_scroll_stable(
            (header + "1936\t0\t295\t210D\tEA\thdma\n").encode(), 1936))
        self.assertFalse(margin.source_scanline_scroll_stable(
            (header + "1936\t100\t295\t210D\tEA\thdma\n").encode(), 1936))
        with self.assertRaisesRegex(ValueError, "frame"):
            margin.source_scanline_scroll_stable(
                (header + "1935\t0\t295\t210D\tEA\thdma\n").encode(), 1936)
        with self.assertRaisesRegex(ValueError, "truncated"):
            margin.source_scanline_scroll_stable((header + "#truncated\n").encode(), 1936)


if __name__ == "__main__":
    unittest.main()
