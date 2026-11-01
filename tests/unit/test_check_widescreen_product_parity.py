import struct
import tempfile
import unittest
from pathlib import Path

from tools.check_widescreen_product_parity import check, compare_center, compare_wram


def write_bmp(path: Path, width: int, height: int, pixel, bpp: int = 32, top_down: bool = True) -> None:
    bytes_pp = bpp // 8
    stride = (width * bytes_pp + 3) & ~3
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            b, g, r = pixel(x, y)
            row += bytes((b, g, r)) + (b"\x00" if bytes_pp == 4 else b"")
        row += b"\x00" * (stride - len(row))
        rows.append(bytes(row))
    if not top_down:
        rows.reverse()
    data = b"".join(rows)
    header = b"BM" + struct.pack("<IHHI", 54 + len(data), 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, width, -height if top_down else height,
                       1, bpp, 0, len(data), 0, 0, 0, 0)
    path.write_bytes(header + info + data)


def stock_pixel(x, y):
    return (x & 0xFF, y & 0xFF, (x ^ y) & 0xFF)


class WidescreenProductParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_center_matches_across_bmp_layouts(self):
        stock = self.root / "stock.bmp"
        wide = self.root / "wide.bmp"
        write_bmp(stock, 256, 8, stock_pixel, bpp=24, top_down=False)
        write_bmp(wide, 342, 8,
                  lambda x, y: stock_pixel(x - 43, y) if 43 <= x < 299 else (9, 9, 9))
        result = compare_center(stock, wide)
        self.assertTrue(result["comparable"])
        self.assertEqual(result["center_offset"], 43)
        self.assertEqual(result["differing_pixels"], 0)

    def test_center_difference_is_located(self):
        stock = self.root / "stock.bmp"
        wide = self.root / "wide.bmp"
        write_bmp(stock, 256, 8, stock_pixel)
        write_bmp(wide, 342, 8,
                  lambda x, y: (1, 2, 3) if (x, y) == (43 + 250, 5) else stock_pixel(x - 43, y))
        result = compare_center(stock, wide)
        self.assertEqual(result["differing_pixels"], 1)
        self.assertEqual(result["bbox"], [250, 5, 250, 5])


    def test_empty_or_truncated_bmp_cannot_pass_center_parity(self):
        stock = self.root / "stock.bmp"
        wide = self.root / "wide.bmp"
        write_bmp(stock, 256, 8, stock_pixel)
        write_bmp(wide, 342, 8, lambda x, y: stock_pixel(x - 43, y))
        self.assertEqual(compare_center(stock, wide)["differing_pixels"], 0)
        self.assertFalse(compare_center(stock, stock)["comparable"])

        # Both files contain plausible BMP headers but no pixels.
        for path in (stock, wide):
            write_bmp(path, 0, 0, stock_pixel)
        with self.assertRaisesRegex(ValueError, "invalid BMP"):
            compare_center(stock, wide)

        write_bmp(stock, 256, 8, stock_pixel)
        write_bmp(wide, 342, 8, lambda x, y: stock_pixel(x - 43, y))
        raw = wide.read_bytes()[:-3]
        # Make the header length agree with the truncated file, so the
        # pixel-payload check rather than header-size check must catch it.
        wide.write_bytes(raw[:2] + struct.pack("<I", len(raw)) + raw[6:])
        with self.assertRaisesRegex(ValueError, "truncated BMP pixels"):
            compare_center(stock, wide)

        write_bmp(wide, 342, 8, lambda x, y: stock_pixel(x - 43, y))
        raw = bytearray(wide.read_bytes())
        struct.pack_into("<I", raw, 30, 1)  # compressed BMP, unsupported
        wide.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "invalid BMP"):
            compare_center(stock, wide)

    def test_equal_short_or_empty_wram_cannot_pass_parity(self):
        write_bmp(self.root / "s.fb.bmp", 256, 4, stock_pixel)
        write_bmp(self.root / "w.fb.bmp", 342, 4,
                  lambda x, y: stock_pixel(x - 43, y))
        pair = ("cp", self.root / "s.fb.bmp", self.root / "w.fb.bmp",
                self.root / "s.wram.bin", self.root / "w.wram.bin")
        for size in (0, 0x10000):
            for path in (self.root / "s.wram.bin", self.root / "w.wram.bin"):
                path.write_bytes(bytes(size))
            report = check([pair])
            self.assertEqual(report["outcome"], "rejected")
            self.assertFalse(compare_wram(pair[3], pair[4])["complete_wram_images"])

    def test_wrong_source_geometry_cannot_claim_parity(self):
        stock = self.root / "s.fb.bmp"
        wide = self.root / "w.fb.bmp"
        a = self.root / "s.wram.bin"
        b = self.root / "w.wram.bin"
        a.write_bytes(bytes(0x20000))
        b.write_bytes(bytes(0x20000))
        pair = ("cp", stock, wide, a, b)
        # Each pair has a genuinely identical centre and complete equal WRAM.
        # The old check accepted all three as WIDE-07 parity evidence.
        for sw, sh, ww, wh in ((1, 1, 3, 1),
                               (256, 8, 342, 8),
                               (256, 224, 344, 224)):
            with self.subTest(geometry=(sw, sh, ww, wh)):
                write_bmp(stock, sw, sh, stock_pixel)
                offset = (ww - sw) // 2
                write_bmp(wide, ww, wh,
                          lambda x, y: stock_pixel(x - offset, y))
                self.assertEqual(compare_center(stock, wide)["differing_pixels"], 0)
                report = check([pair])
                self.assertEqual(report["outcome"], "rejected")
                self.assertFalse(report["metrics"]["cp"]["center"]["expected_source_geometry"])

    def test_wram_lane_allowed_but_leak_rejected(self):
        a = bytearray(0x20000)
        b = bytearray(a)
        b[0x03A0] = 1      # descriptor slot table
        b[0x0460] = 2      # strip staging
        (self.root / "a.bin").write_bytes(a)
        (self.root / "b.bin").write_bytes(b)
        ok = compare_wram(self.root / "a.bin", self.root / "b.bin")
        self.assertEqual(ok["lane_differences"], 2)
        self.assertEqual(ok["leaked_bytes"], 0)
        b[0x0069] = 4      # documented run-variant accumulator
        (self.root / "b.bin").write_bytes(b)
        variant = compare_wram(self.root / "a.bin", self.root / "b.bin")
        self.assertEqual(variant["leaked_bytes"], 0)
        self.assertEqual(variant["run_variant_differences"], ["0x00069"])
        b[0x2049] = 3      # BG1 scroll HDMA table: presentation leak
        (self.root / "b.bin").write_bytes(b)
        leak = compare_wram(self.root / "a.bin", self.root / "b.bin")
        self.assertEqual(leak["leaked_bytes"], 1)
        self.assertEqual(leak["first_leaks"], ["0x02049"])

    def test_envelope_outcome(self):
        write_bmp(self.root / "s.fb.bmp", 256, 224, stock_pixel)
        write_bmp(self.root / "w.fb.bmp", 342, 224, lambda x, y: stock_pixel(x - 43, y))
        (self.root / "s.wram.bin").write_bytes(bytes(0x20000))
        (self.root / "w.wram.bin").write_bytes(bytes(0x20000))
        pair = ("cp", self.root / "s.fb.bmp", self.root / "w.fb.bmp",
                self.root / "s.wram.bin", self.root / "w.wram.bin")
        self.assertEqual(check([pair])["outcome"], "accepted")
        wram = bytearray(0x20000)
        wram[0x2049] = 1
        (self.root / "w.wram.bin").write_bytes(wram)
        self.assertEqual(check([pair])["outcome"], "rejected")


if __name__ == "__main__":
    unittest.main()
