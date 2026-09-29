from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import find_mmio_access_sites as mmio


class MmioAccessScannerTests(unittest.TestCase):
    def test_finds_absolute_read_write_candidates(self) -> None:
        data = bytes.fromhex(
            "ea "
            "8d 40 21 "
            "ad 41 21 "
            "cd 42 21 "
            "ea"
        )
        w = mmio.scan(data, 0x2140)
        r = mmio.scan(data, 0x2141)
        c = mmio.scan(data, 0x2142)
        self.assertEqual([(x["mnemonic"], x["access"]) for x in w], [("STA", "write")])
        self.assertEqual([(x["mnemonic"], x["access"]) for x in r], [("LDA", "read")])
        self.assertEqual([(x["mnemonic"], x["access"]) for x in c], [("CMP", "read")])
        self.assertTrue(w[0]["db_sensitive"])

    def test_long_access_requires_hardware_mirror_bank(self) -> None:
        data = bytes.fromhex(
            "8f 42 21 80 "
            "af 43 21 00 "
            "8f 42 21 7e"
        )
        writes = mmio.scan(data, 0x2142)
        reads = mmio.scan(data, 0x2143)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["explicit_bank"], "0x80")
        self.assertFalse(writes[0]["db_sensitive"])
        self.assertEqual(len(reads), 1)
        self.assertEqual(reads[0]["explicit_bank"], "0x00")

    def test_rejects_non_16_bit_target(self) -> None:
        with self.assertRaises(ValueError):
            mmio.scan(b"", 0x10000)


if __name__ == "__main__":
    unittest.main()
