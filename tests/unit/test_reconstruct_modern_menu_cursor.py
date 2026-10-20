#!/usr/bin/env python3
"""Test real-source OBJ decoder with controlled PPU data and negative cases.

The fabricated fixture only tests the extractor's arithmetic; it is NEVER
promoted to the native sprite pipeline or described as original cursor art.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import reconstruct_modern_menu_cursor as cursor


def fixture() -> tuple[list[SimpleNamespace], dict]:
    contract = json.loads(cursor.REFERENCE.read_text())
    tiles = contract["cursor"]["spin_cycle_tiles"]
    assert len(tiles) == 16
    vram = bytearray(65536)
    # SNES planar 4bpp: 16 original source phase tile groups occupying the
    # same 8x8 tile bank in the proven chronological ROM tile sequence.
    for i, first in enumerate(tiles):
        colour = (i % 15) + 1
        for y in range(4):
            for x in range(4):
                tile = first + y * 16 + x
                base = tile * 32
                for row in range(8):
                    for plane in range(4):
                        if colour & (1 << plane):
                            vram[base + (plane // 2) * 16 +
                                 row * 2 + plane % 2] = 255

    cgram = bytearray(512)
    for i, col in enumerate(contract["cursor"]["arrow_palette_rgb"]):
        # Rebuild RGB5 source CGRAM from measured multiples-of-eight RGB.
        r, g, b = [n >> 3 for n in col]
        word = r | (g << 5) | (b << 10)
        where = 2 * (128 + 7 * 16 + i)
        cgram[where:where + 2] = word.to_bytes(2, "little")
    # Shadow palette 5, pen1 is the source-measured maroon shadow.
    r, g, b = [n >> 3 for n in contract["cursor"]["shadow_palette_rgb"]]
    cgram[2 * (128 + 5 * 16 + 1):2 * (128 + 5 * 16 + 2)] = (
        r | g << 5 | b << 10).to_bytes(2, "little")

    result = []
    for i in range(64):
        oam = bytearray(544)
        for index in range(128):
            oam[4 * index + 1] = 240  # hide every non-source test sprite
        # Palette7 arrow plus palette5 shadow, both sized 32x32.
        oam[0:4] = bytes([79, 70, tiles[(i // 2) % 16], 7 << 1])
        oam[4:8] = bytes([86, 77, 0, 5 << 1])
        oam[512] = 0b00001010
        result.append(SimpleNamespace(
            tag=f"mvl-idle-{i:03d}",
            oam=bytes(oam),
            vram=bytes(vram), cgram=bytes(cgram),
            fillram={"2101": "20"},  # source-like large-32 OBJ size pair
        ))
    return result, contract


class OriginalStockCursorTests(unittest.TestCase):
    def test_chronological_source_cursors_and_rendered_phases(self):
        dumps, contract = fixture()
        frames, evidence = cursor.reconstruct(dumps, contract)
        self.assertEqual(len(frames), 16)
        # Sixty-four original idle dumps cover two complete 32-tick
        # rotations, while the atlas stores one 16-pose cycle.
        self.assertEqual([item["tile"] for item in evidence[::2]],
                         contract["cursor"]["spin_cycle_tiles"] * 2)
        self.assertGreaterEqual(len({f for f in frames}), 8)
        self.assertEqual(frames[0][0:4], bytes((40, 48, 88, 255)))
        self.assertEqual(len(cursor.png_frame(frames[0])) > 100, True)
        self.assertEqual(len(frames[0]), 39 * 39 * 4)
        self.assertTrue(all(record["opaque_pixels"] >= 1024
                            for record in evidence if "opaque_pixels" in record))

    def test_every_source_ppu_raster_retains_two_frame_hold_and_full_revolution(self):
        dumps, contract = fixture()
        frames, records = cursor.reconstruct(dumps, contract)
        self.assertEqual(len(frames), 16)
        self.assertEqual(len(records), 64)
        self.assertTrue(all("rgba_sha256" in record for record in records))
        self.assertEqual(records[0]["rgba_sha256"], records[1]["rgba_sha256"])
        self.assertEqual(records[0]["rgba_sha256"], records[32]["rgba_sha256"])
        self.assertEqual(records[31]["rgba_sha256"], records[63]["rgba_sha256"])
        first_tile = contract["cursor"]["spin_cycle_tiles"][0]
        corrupted_pos = first_tile * 32

        bad = deepcopy(dumps)
        pixels = bytearray(bad[1].vram)
        pixels[corrupted_pos] ^= 0x80
        bad[1].vram = bytes(pixels)
        with self.assertRaisesRegex(ValueError, "raster hold diverged"):
            cursor.reconstruct(bad, contract)

        bad = deepcopy(dumps)
        pixels = bytearray(bad[32].vram)
        pixels[corrupted_pos] ^= 0x80
        bad[32].vram = bytes(pixels)
        with self.assertRaisesRegex(ValueError, "raster revolution diverged"):
            cursor.reconstruct(bad, contract)

    def test_source_shadow_palette_must_match_every_original_ppu_capture(self):
        dumps, contract = fixture()
        bad = deepcopy(dumps)
        data = bytearray(bad[17].cgram)
        data[2 * (128 + 5 * 16 + 1)] ^= 0x1f
        bad[17].cgram = bytes(data)
        with self.assertRaisesRegex(ValueError, "shadow CGRAM colour drifted"):
            cursor.verify_source_frames(bad, contract)

    def test_oam_flip_is_applied_to_entire_32px_sprite(self):
        dumps, _ = fixture()
        d = dumps[0]
        sprite = next(s for s in cursor.mvl.sprites(d.oam)
                      if s["palette"] == 7)
        # Unique top-left ink from just the first CHR tile. Every other
        # raster pixel is transparent. A tile-wise flip would leave this
        # at (7,0), not the genuine whole-sprite endpoint (31,0).
        vram = bytearray(len(d.vram))
        vram[sprite["tile"] * 32] = 0x80
        d.vram = bytes(vram)

        def paint(flips):
            oam = bytearray(d.oam)
            oam[3] = (oam[3] & 0x3F) | flips
            d.oam = bytes(oam)
            frame = bytearray(cursor.CANVAS * cursor.CANVAS * 4)
            cursor.draw_sprite(d, sprite, frame, 0, 0)
            opaque = [(x, y) for y in range(cursor.CANVAS)
                      for x in range(cursor.CANVAS)
                      if frame[(y * cursor.CANVAS + x) * 4 + 3]]
            return opaque

        self.assertEqual(paint(0), [(0, 0)])
        self.assertEqual(paint(0x40), [(31, 0)])
        self.assertEqual(paint(0x80), [(0, 31)])
        self.assertEqual(paint(0xC0), [(31, 31)])

    def test_oam_flip_change_inside_two_tick_hold_is_rejected(self):
        dumps, contract = fixture()
        bad = deepcopy(dumps)
        attr = bytearray(bad[1].oam)
        attr[3] ^= 0x40
        bad[1].oam = bytes(attr)
        with self.assertRaisesRegex(ValueError, "hold changed OAM flipping"):
            cursor.verify_source_frames(bad, contract)
        bad = deepcopy(dumps)
        attr = bytearray(bad[32].oam)
        attr[3] ^= 0x80
        bad[32].oam = bytes(attr)
        with self.assertRaisesRegex(ValueError, "cycle OAM flips diverged"):
            cursor.verify_source_frames(bad, contract)

    def test_nonzero_obj_name_base_and_secondary_name_page(self):
        dumps, contract = fixture()
        _, original_evidence = cursor.reconstruct(dumps, contract)
        assert original_evidence
        original, _ = cursor.reconstruct(dumps, contract)
        # Shift actual 8 KiB source OBJ tile data from VRAM word 0 to
        # word 0x2000 (0x4000 bytes). The renderer must follow $2101 base,
        # rather than quietly reading the stale word-0 tile bank.
        src = dumps[0].vram
        relocated = bytearray(len(src))
        relocated[0x4000:0x6000] = src[:0x2000]
        for d in dumps:
            d.vram = bytes(relocated)
            d.fillram["2101"] = "21"
        shifted, _ = cursor.reconstruct(dumps, contract)
        self.assertEqual(shifted, original)
        self.assertEqual(cursor.original_obj_base_word(dumps[0]), 0x2000)
        # A separate name-select page is 0x1000 words (8 KiB), not 0x2000.
        dumps[0].fillram["2101"] = "29"  # size1, name-select1, base1
        self.assertEqual(cursor.original_obj_base_word(dumps[0], 0x100),
                         0x4000)
        dumps[0].fillram["2101"] = "20"  # size1, name-select0, base0
        self.assertEqual(cursor.original_obj_base_word(dumps[0], 0x100),
                         0x1000)

    def test_duplicate_original_cursor_or_shadow_oam_is_not_admitted(self):
        dumps, contract = fixture()
        for existing in (0, 1):
            bad = deepcopy(dumps)
            oam = bytearray(bad[0].oam)
            oam[8:12] = oam[existing * 4:existing * 4 + 4]
            oam[512] |= 0b00100000  # third sprite marked large, 32x32
            bad[0].oam = bytes(oam)
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                cursor.verify_source_frames(bad, contract)

    def test_source_oam_and_colour_contract_refuses_mismatch(self):
        dumps, contract = fixture()
        invalid = deepcopy(contract)
        invalid["cursor"]["spin_cycle_tiles"][0] = 199
        with self.assertRaisesRegex(ValueError, "tile/pose/shadow"):
            cursor.verify_source_frames(dumps, invalid)
        invalid = deepcopy(contract)
        invalid["cursor"]["shadow_offset_px"] = [7, 6]
        with self.assertRaisesRegex(ValueError, "timing"):
            cursor.verify_source_frames(dumps, invalid)
        bad = list(dumps)
        bad[7], bad[8] = bad[8], bad[7]
        with self.assertRaisesRegex(ValueError, "reordered"):
            cursor.verify_source_frames(bad, contract)
        bad = deepcopy(dumps)
        bad[0].fillram["2101"] = "malformed"
        with self.assertRaisesRegex(ValueError, "name-base"):
            cursor.reconstruct(bad, contract)
        bad = deepcopy(dumps)
        cgram = bytearray(bad[2].cgram)
        cgram[2 * (128 + 7 * 16 + 1)] ^= 0x1f
        bad[2].cgram = bytes(cgram)
        with self.assertRaisesRegex(ValueError, "palette drifted"):
            cursor.verify_source_frames(bad, contract)


if __name__ == "__main__":
    unittest.main()
