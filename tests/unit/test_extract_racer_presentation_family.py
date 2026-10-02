import unittest

from tools.extract_racer_presentation_family import (
    FRAME_TABLE_ADDR,
    PALETTE_TABLE_ADDR,
    decode_bgr555,
    decode_frame_record,
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

    def test_4bpp_tile_roundtrip(self):
        payload = bytes(range(64))
        tiles = split_4bpp_tiles(payload)
        self.assertEqual(len(tiles), 2)
        self.assertEqual(b"".join(tiles), payload)

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
