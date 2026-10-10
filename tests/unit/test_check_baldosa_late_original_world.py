"""Late real PPU witness must be distinct, source-wide and guest read-only."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_late_original_world import assess


def pam(width, height, colour):
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
              "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    pixels = bytearray(colour * (width * height))
    for y in range(height):
        for x in (0, 5, 12, 30, 52, width - 1, width - 7, width - 22):
            if 0 <= x < width:
                j = (y * width + x) * 4
                pixels[j:j + 4] = bytes((y % 255, x % 255, 127, 0))
    return header + pixels


class LateOriginalWorldTests(unittest.TestCase):
    def test_real_late_capture_requires_source_witness_and_all_guest_crcs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            caps = root / "captures"
            caps.mkdir()
            crc_a, crc_b = root / "a.crc", root / "b.crc"
            crc_a.write_bytes(b"12345678\n" * 2473)
            crc_b.write_bytes(crc_a.read_bytes())
            old = pam(342, 224, bytes((4, 6, 8, 0)))
            mid = pam(342, 224, bytes((7, 9, 11, 0)))
            new = pam(342, 224, bytes((14, 16, 18, 0)))
            for frame, raw in ((1808, old), (1856, mid), (2208, new)):
                (caps / f"ur-baldosa-ws342-{frame:06d}.pam").write_bytes(raw)
            log = root / "guest.log"
            log.write_text("UR_BALDOSA_WS342_LATE_PRESENT frame=2208 "
                           "saved=1 logical=342x224 density=1 "
                           "source=native-original-ppu\n")
            result = assess(caps, log, crc_a, crc_b, 2200)
            self.assertEqual(result["real_late_guest_frame"], 2208)
            self.assertGreater(result["changed_full_ppu_pixels_from_earlier"], 0)
            self.assertFalse(result["release_gameplay_visual_acceptance"])
            self.assertFalse(result["source_visible_hd_replacement_admitted"])
            with self.assertRaises(ValueError):
                assess(caps, log, crc_a, crc_b, 1999)
            crc_b.write_bytes(crc_a.read_bytes().replace(b"12345678", b"87654321", 1))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(caps, log, crc_a, crc_b, 2200)
            crc_b.write_bytes(crc_a.read_bytes())
            log.write_text("")
            with self.assertRaisesRegex(ValueError, "marker"):
                assess(caps, log, crc_a, crc_b, 2200)
            log.write_text("UR_BALDOSA_WS342_LATE_PRESENT frame=2208 "
                           "saved=1 logical=342x224 density=1 "
                           "source=native-original-ppu\n")
            (caps / "ur-baldosa-ws342-002208.pam").write_bytes(mid)
            with self.assertRaisesRegex(ValueError, "static"):
                assess(caps, log, crc_a, crc_b, 2200)


if __name__ == "__main__":
    unittest.main()
