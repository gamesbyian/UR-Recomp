import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import extract_menu_visual_language as mvl  # noqa: E402


def put_entry(vram: bytearray, map_base: int, tx: int, ty: int, tile: int, palette: int) -> None:
    addr = (map_base + (ty % 32) * 32 + tx % 32) * 2
    entry = tile | palette << 10 | 0x2000
    vram[addr], vram[addr + 1] = entry & 0xFF, entry >> 8


def write_label(vram: bytearray, map_base: int, tx: int, ty: int, text: str) -> None:
    for ch in text:
        if ch != " ":
            slot = mvl.slot_for_char(ch)
            for dx, dy, tile in ((0, 0, 0), (1, 0, 1), (0, 1, 0x50), (1, 1, 0x51)):
                put_entry(vram, map_base, tx + dx, ty + dy, 2 * slot + tile, 7)
        tx += 2


class MenuVisualLanguageTests(unittest.TestCase):
    def test_encoding_matches_recovered_slots(self) -> None:
        # Slots observed in the MAIN_MENU tilemap: 1P, LEAGUE, OPTIONS.
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "1P"], [0x02, 0x30])
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "LEAGUE"],
                         [0x2A, 0x1C, 0x14, 0x20, 0x3A, 0x1C])
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "OPTIONS"],
                         [0x00, 0x30, 0x38, 0x24, 0x00, 0x2E, 0x36])
        self.assertEqual(mvl.char_for_slot(35), "OK")
        self.assertEqual(mvl.char_for_slot(39), "ICON_STUNT_HOOK")
        self.assertEqual(mvl.glyph_tiles(3), [6, 7, 0x56, 0x57])

    def test_text_rows_decode_spacing_and_centering(self) -> None:
        vram = bytearray(0x10000)
        write_label(vram, 0x1000, 3, 19, "DEFINE PLAYER")
        write_label(vram, 0x1000, 14, 10, "1P")
        rows = mvl.text_rows(bytes(vram), 0x1000, 64, 64, 7, 0)
        self.assertEqual([r["text"] for r in rows], ["1P", "DEFINE PLAYER"])
        self.assertEqual(rows[0]["center_x"], 128)
        self.assertEqual(rows[1]["center_x"], 128)
        self.assertEqual(rows[1]["x_left"], 24)

    def test_run_lengths_and_deltas(self) -> None:
        self.assertEqual(mvl.run_lengths([8, 8, 4, 4, 0]), [[8, 2], [4, 2], [0, 1]])
        self.assertEqual(mvl.deltas([0, 1, 3, 6]), [1, 2, 3])

    def test_png_writer_emits_valid_stream(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.png"
            mvl.write_png(path, 2, 1, bytes([255, 0, 0, 255, 0, 255, 0, 255]))
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height), (2, 1))
            idat = data.index(b"IDAT")
            length = struct.unpack(">I", data[idat - 4:idat])[0]
            self.assertEqual(zlib.decompress(data[idat + 4:idat + 4 + length])[:5], b"\x00\xff\x00\x00\xff")


if __name__ == "__main__":
    unittest.main()
