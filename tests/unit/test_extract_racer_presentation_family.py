import unittest

from tools.extract_racer_presentation_family import (
    FRAME_TABLE_ADDR,
    PALETTE_TABLE_ADDR,
    decode_4bpp_tile,
    decode_bgr555,
    encode_png_rgba,
    packed_word_source,
    occupancy_rows_from_header,
    selected_occupancy_rows,
    pack_player_row_masks,
    compose_racer_staging,
    parse_palette_assets,
    rasterize_frame_rgba,
    decode_frame_record,
    decode_piece_mapping,
    frame_pointer,
    lorom_offset,
    palette_entry,
    split_4bpp_tiles,
)


class RacerPresentationRoundTripTests(unittest.TestCase):
    def test_lorom_mapping(self):
        self.assertEqual(lorom_offset(0x20, 0x8000), 0x100000)
        self.assertEqual(lorom_offset(0x82, 0xB32F), 0x1332F)

    def test_frame_pointer_decode_repack(self):
        rom = bytearray(0x110000)
        frame_id = 3
        off = lorom_offset(0x20, FRAME_TABLE_ADDR + frame_id * 3)
        rom[off:off + 3] = bytes.fromhex("34a512")
        ptr = frame_pointer(bytes(rom), frame_id)
        self.assertEqual((ptr.source_bank, ptr.source_addr), (0x35, 0xA534))
        self.assertEqual(ptr.repack(), bytes.fromhex("34a512"))

    def test_frame_record_decode_repack(self):
        raw = bytes.fromhex("2c112233aabbccddeeff")
        record = decode_frame_record(raw)
        self.assertEqual(record.header, bytes.fromhex("2c112233"))
        self.assertEqual(record.renderer_prefix_length, 10)
        self.assertEqual(len(record.packed_words), 3)
        self.assertEqual(record.repack(), raw)

    def test_piece_mapping_is_msb_first_30_cell_scan(self):
        raw = bytes.fromhex("38c31c70") + b"".join(
            x.to_bytes(2, "little")
            for x in (0x1B00,0x1C00,0x1D00,0x1E00,0x1F00,0x2000,0x2100,0x2200,0xFE14,0xFF14,0x2500,0x0015,0x1407)
        )
        record = decode_frame_record(raw)
        pieces = decode_piece_mapping(record)
        self.assertEqual(len(pieces), 13)
        self.assertEqual((pieces[0]["major_slot"], pieces[0]["minor_slot"], pieces[0]["word_hex"]), (0, 2, "0x1B00"))
        self.assertEqual((pieces[-1]["major_slot"], pieces[-1]["minor_slot"], pieces[-1]["word_hex"]), (4, 3, "0x1407"))
        self.assertEqual(pieces[0]["staged_1645_value"], "0x8360")
        self.assertEqual(pieces[8]["staged_15a1_value"], "0x002C")
        self.assertEqual(pieces[-1]["low2_renderer_ignored_value"], 3)

    def test_f2bb_row_packing_matches_recovered_14_bit_layout(self):
        p1 = bytes.fromhex("30c31c70")
        p2 = bytes.fromhex("70c31e30")
        self.assertEqual(
            occupancy_rows_from_header(p1),
            (0x0C, 0x0C, 0x0C, 0x1C, 0x1C),
        )
        self.assertEqual(
            occupancy_rows_from_header(p2),
            (0x1C, 0x0C, 0x0C, 0x1E, 0x0C),
        )
        self.assertEqual(
            pack_player_row_masks(
                occupancy_rows_from_header(p1),
                occupancy_rows_from_header(p2),
            ),
            (0x3070, 0x3030, 0x3030, 0x7078, 0x7030),
        )

    def test_f2bb_selector_clipping(self):
        header = bytes.fromhex("30c31c70")
        rows, cursor = selected_occupancy_rows(header, 1)
        self.assertEqual(rows, (0, 0x0C, 0x0C, 0x1C, 0x1C))
        self.assertEqual(cursor, 2)
        rows, cursor = selected_occupancy_rows(header, 2)
        self.assertEqual(rows, (0x0C, 0x0C, 0x0C, 0x1C, 0))
        self.assertEqual(cursor, 0)

    def test_companion_overlap_wins_but_consumes_primary_word(self):
        def frame(header_hex, words):
            return {
                "record_header_hex": header_hex,
                "pieces": [{"word_hex": f"0x{x:04X}"} for x in words],
            }

        result = compose_racer_staging(
            frame("fc000000", (0x0100, 0x0200, 0x0300, 0x0400, 0x0500, 0x0600)),
            frame("00000000", ()),
            frame("30000000", (0xAA00, 0xBB00)),
            frame("00000000", ()),
        )
        first_row = result["cells"][:14]
        self.assertEqual(
            [cell["choice"] for cell in first_row[:6]],
            [
                "p1_primary",
                "p1_primary",
                "p1_companion",
                "p1_companion",
                "p1_primary",
                "p1_primary",
            ],
        )
        self.assertEqual(
            [cell["word_hex"] for cell in first_row[:6]],
            ["0x0100", "0x0200", "0xAA00", "0xBB00", "0x0500", "0x0600"],
        )
        self.assertEqual(
            [(cell["major_slot"], cell["minor_slot"]) for cell in first_row[:6]],
            [(0, i) for i in range(6)],
        )
        self.assertEqual(result["final_word_cursors"]["p1_primary"], 6)
        self.assertEqual(result["final_word_cursors"]["p1_companion"], 2)
        self.assertEqual(
            [cell["staged_vram_word"] for cell in first_row],
            [0x6010 + i * 0x10 for i in range(14)],
        )

    def test_4bpp_tile_roundtrip(self):
        payload = bytes(range(64))
        tiles = split_4bpp_tiles(payload)
        self.assertEqual(len(tiles), 2)
        self.assertEqual(b"".join(tiles), payload)

    def test_4bpp_decode_known_planes(self):
        tile = bytearray(32)
        tile[0] = 0x80
        tile[1] = 0x40
        tile[16] = 0x20
        tile[17] = 0x10
        px = decode_4bpp_tile(bytes(tile))
        self.assertEqual(px[0][:4], [1, 2, 4, 8])

    def test_packed_word_source_matches_staging_consumer(self):
        self.assertEqual(packed_word_source(0x1B00), (0x27, 0x8360))
        self.assertEqual(packed_word_source(0xFF14), (0x2C, 0x9FE0))
        self.assertEqual(packed_word_source(0x1407), (0x28, 0x8280))

    def test_png_encoder_is_deterministic(self):
        rgba = bytes([255, 0, 0, 255]) * 4
        a = encode_png_rgba(2, 2, rgba)
        b = encode_png_rgba(2, 2, rgba)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_palette_asset_spec(self):
        self.assertEqual(parse_palette_assets("0x06,0x15"), (0x06, 0x15))
        self.assertEqual(parse_palette_assets("0x06,0x06"), (0x06,))
        self.assertEqual(parse_palette_assets("all"), tuple(range(0x06, 0x16)))
        with self.assertRaises(ValueError):
            parse_palette_assets("0x16")

    def test_palette_entry_and_bgr555_roundtrip(self):
        rom = bytearray(0x20000)
        asset_id = 6
        off = lorom_offset(0x82, PALETTE_TABLE_ADDR + asset_id * 5)
        rom[off:off + 5] = bytes.fromhex("03a0800400")
        ent = palette_entry(bytes(rom), asset_id)
        self.assertEqual((ent.source_bank, ent.source_addr, ent.length), (0x03, 0x80A0, 4))
        self.assertFalse(ent.compressed_flag)
        self.assertEqual(ent.repack(), bytes.fromhex("03a0800400"))
        payload = bytes.fromhex("1f00e003")
        colors = decode_bgr555(payload)
        rebuilt = b"".join(c["word"].to_bytes(2, "little") for c in colors)
        self.assertEqual(rebuilt, payload)


if __name__ == "__main__":
    unittest.main()
