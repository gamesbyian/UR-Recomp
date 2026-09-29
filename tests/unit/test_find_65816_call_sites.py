from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import find_65816_call_sites as calls


class CallSiteScannerTests(unittest.TestCase):
    def test_parse_cpu_address(self) -> None:
        self.assertEqual(calls.parse_cpu_address("02:8298"), (0x02, 0x8298))
        self.assertEqual(calls.parse_cpu_address("0x028298"), (0x02, 0x8298))

    def test_finds_bank_local_jsr(self) -> None:
        data = bytearray(b"\xea" * (0x10000 + 8))
        # ROM offset 0x10000 begins LoROM bank 02.
        data[0x10002:0x10005] = bytes([0x20, 0x98, 0x82])
        hits = calls.scan(bytes(data), 0x02, 0x8298)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["kind"], "JSR")
        self.assertEqual(hits[0]["source_cpu"], "02:8002")

    def test_rejects_jsr_from_other_bank(self) -> None:
        data = bytes([0x20, 0x98, 0x82])
        self.assertEqual(calls.scan(data, 0x02, 0x8298), [])

    def test_jsl_accepts_lorom_bank_mirror(self) -> None:
        data = bytes.fromhex("22 98 82 82")
        hits = calls.scan(data, 0x02, 0x8298)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["kind"], "JSL")
        self.assertEqual(hits[0]["encoded_target_bank"], "0x82")

    def test_rejects_wrong_long_bank(self) -> None:
        data = bytes.fromhex("22 98 82 83")
        self.assertEqual(calls.scan(data, 0x02, 0x8298), [])

    def test_rejects_non_rom_target(self) -> None:
        with self.assertRaises(ValueError):
            calls.scan(b"", 0x00, 0x2140)


if __name__ == "__main__":
    unittest.main()
