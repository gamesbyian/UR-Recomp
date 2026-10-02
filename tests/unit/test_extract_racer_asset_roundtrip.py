import unittest

from tools.extract_racer_asset_roundtrip import (
    FRAME_TABLE,
    RESOURCE_TABLE,
    frame_pointer,
    lorom_offset,
    parse_resource_descriptor,
    read_snes_linear,
    unit_roundtrip,
)


class RacerAssetRoundtripTests(unittest.TestCase):
    def test_lorom_offset(self):
        self.assertEqual(lorom_offset(0x008000), 0x000000)
        self.assertEqual(lorom_offset(0x018000), 0x008000)
        self.assertEqual(lorom_offset(0x20A000), 0x102000)

    def test_read_snes_linear_crosses_bank(self):
        rom = bytearray(0x20000)
        rom[lorom_offset(0x00FFFE)] = 0x11
        rom[lorom_offset(0x00FFFF)] = 0x22
        rom[lorom_offset(0x018000)] = 0x33
        self.assertEqual(read_snes_linear(bytes(rom), 0x00FFFE, 3), b"\x11\x22\x33")

    def test_resource_descriptor_layout(self):
        rom = bytearray(0x200000)
        addr = RESOURCE_TABLE + 0x7F * 5
        off = lorom_offset(addr)
        rom[off:off+5] = bytes([0xA5, 0x34, 0x92, 0x40, 0x00])
        row = parse_resource_descriptor(bytes(rom), 0x7F)
        self.assertEqual(row["source_snes"], "259234")
        self.assertTrue(row["compressed"])
        self.assertEqual(row["stored_length"], 0x40)

    def test_frame_pointer_contract(self):
        rom = bytearray(0x200000)
        frame_id = 0x0123
        off = lorom_offset(FRAME_TABLE + frame_id * 3)
        rom[off:off+3] = bytes([0xCD, 0xAB, 0x04])
        row = frame_pointer(bytes(rom), frame_id)
        self.assertEqual(row["record_snes"], "27ABCD")
        self.assertEqual(row["entry_hex"], "cdab04")

    def test_unit_roundtrip(self):
        raw = bytes(range(64))
        hashes, rebuilt = unit_roundtrip(raw, 32)
        self.assertEqual(len(hashes), 2)
        self.assertEqual(rebuilt, raw)


if __name__ == "__main__":
    unittest.main()
