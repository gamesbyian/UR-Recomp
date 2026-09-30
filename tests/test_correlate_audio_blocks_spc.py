#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/correlate_audio_blocks_spc.py"
SPEC = importlib.util.spec_from_file_location("correlate_audio_blocks_spc", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AudioBlockSpcCorrelationTests(unittest.TestCase):
    def synthetic_rom(self) -> bytes:
        rom = bytearray(0xA0000)
        cursor = 0x080000
        for block_id in range(0x32):
            payload = bytes([block_id, block_id ^ 0xFF]) + bytes([block_id]) * 40
            record = (len(payload) + 2).to_bytes(2, "little") + payload
            rom[cursor:cursor + len(record)] = record
            cursor += len(record)
        return bytes(rom)

    def test_extract_complete_package_prefix(self):
        rows = MODULE.extract_block_payloads(self.synthetic_rom(), range(0x32))
        self.assertEqual(len(rows), 0x32)
        self.assertEqual(rows[0]["id_hex"], "0x00")
        self.assertEqual(rows[-1]["id_hex"], "0x31")
        self.assertEqual(rows[-1]["payload_length"], 42)

    def test_trimmed_match_recovers_framed_payload(self):
        payload = b"HEAD" + bytes(range(64)) + b"TAIL"
        ram = b"\x00" * 100 + bytes(range(64)) + b"\x00" * 100
        match = MODULE.best_trimmed_match(
            payload,
            ram,
            max_leading_trim=4,
            max_trailing_trim=4,
            min_match=32,
        )
        self.assertIsNotNone(match)
        self.assertEqual(match["apu_offset"], 100)
        self.assertEqual(match["leading_trim"], 4)
        self.assertEqual(match["trailing_trim"], 4)
        self.assertEqual(match["matched_length"], 64)


if __name__ == "__main__":
    unittest.main()
