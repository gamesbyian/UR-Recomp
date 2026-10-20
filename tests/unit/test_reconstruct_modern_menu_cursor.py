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
            fillram={"2101": "00"},
        ))
    return result, contract


class OriginalStockCursorTests(unittest.TestCase):
    def test_chronological_source_cursors_and_rendered_phases(self):
        dumps, contract = fixture()
        frames, evidence = cursor.reconstruct(dumps, contract)
        self.assertEqual(len(frames), 16)
        self.assertEqual([item["tile"] for item in evidence[::2]],
                         contract["cursor"]["spin_cycle_tiles"])
        self.assertGreaterEqual(len({f for f in frames}), 8)
        self.assertEqual(frames[0][0:4], bytes((40, 48, 88, 255)))
        self.assertEqual(len(cursor.png_frame(frames[0])) > 100, True)
        self.assertEqual(len(frames[0]), 39 * 39 * 4)
        self.assertTrue(all(record["opaque_pixels"] >= 1024
                            for record in evidence if "opaque_pixels" in record))

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
